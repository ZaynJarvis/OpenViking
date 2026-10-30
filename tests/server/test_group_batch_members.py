# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0
"""Atomic bulk group membership and cache invalidation contracts."""

import json
import os
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

from openviking.server.account_stores.file import FileStore
from openviking.server.account_stores.mysql import MySQLAccountStore
from openviking.server.account_stores.mysql_schema import Account, Base
from openviking.server.account_stores.redis_mysql import RedisMySQLAccountStore
from openviking.server.store_assembly import build_api_key_manager
from openviking.storage.viking_fs import VikingFS
from openviking_cli.exceptions import FailedPreconditionError, NotFoundError
from tests.server.account_store_fakes import InMemoryAGFS


@pytest.fixture(params=["file", "mysql"])
async def manager(request):
    service_name = f"test-batch-{uuid4().hex}"
    engine = None
    if request.param == "mysql":
        raw_mysql = os.environ.get("OV_TEST_MYSQL")
        if not raw_mysql:
            pytest.skip("Set OV_TEST_MYSQL to exercise MySQL batch membership transactions")
        result = build_api_key_manager(
            "root",
            None,
            service_name=service_name,
            account_store_provider="mysql",
            account_store_params=json.loads(raw_mysql),
            issue_user_keys=False,
        )
        store = result._store
        assert isinstance(store, MySQLAccountStore)
        engine = create_async_engine(store._url, **store._engine_options)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    else:
        result = build_api_key_manager(
            "root", cast(VikingFS, SimpleNamespace(agfs=InMemoryAGFS())), issue_user_keys=False
        )
    await result.load()
    try:
        await result.create_account("acme", "admin")
        await result.register_user("acme", "alice")
        await result.register_user("acme", "bob")
        await result.create_group("acme", "engineering")
        yield result
    finally:
        await result.close()
        if engine is not None:
            async with engine.begin() as connection:
                await connection.execute(
                    delete(Account).where(Account.service_name == service_name)
                )
            await engine.dispose()


async def test_batch_add_is_idempotent_and_updates_all_membership_indexes(manager):
    await manager.add_group_member("acme", "engineering", "admin")
    user_ids = ["bob", "alice", "admin", "bob"]

    assert await manager.add_group_members("acme", "engineering", user_ids) is True
    assert await manager.add_group_members("acme", "engineering", user_ids) is True
    assert await manager.get_group_members("acme", "engineering") == ["admin", "alice", "bob"]
    assert await manager.get_groups("acme") == [{"group_id": "engineering", "member_count": 3}]
    for user_id in set(user_ids):
        assert await manager.get_user_group_ids("acme", user_id) == ("engineering",)

    await manager.close()
    await manager.load()
    assert await manager.get_group_members("acme", "engineering") == ["admin", "alice", "bob"]


async def test_batch_rejects_user_from_another_account_without_partial_additions(manager):
    await manager.create_account("other", "outsider")
    await manager.add_group_member("acme", "engineering", "admin")

    with pytest.raises(NotFoundError, match="User not found"):
        await manager.add_group_members("acme", "engineering", ["alice", "outsider", "bob"])

    assert await manager.get_group_members("acme", "engineering") == ["admin"]
    assert await manager.get_user_group_ids("acme", "alice") == ()
    assert await manager.get_user_group_ids("other", "outsider") == ()


async def test_batch_rejects_deleting_user_without_partial_additions(manager):
    await manager.begin_deletion(
        "acme", "bob", task_id="delete-bob", owner_account_id="acme", owner_user_id="admin"
    )

    with pytest.raises(FailedPreconditionError, match="deletion is in progress"):
        await manager.add_group_members("acme", "engineering", ["alice", "bob"])

    assert await manager.get_group_members("acme", "engineering") == []
    assert await manager.get_user_group_ids("acme", "alice") == ()


@pytest.mark.parametrize(
    "account_id,group_id,missing",
    [("missing", "engineering", "Account"), ("acme", "missing", "Group")],
)
async def test_batch_requires_account_and_group(manager, account_id, group_id, missing):
    with pytest.raises(NotFoundError, match=f"{missing} not found"):
        await manager.add_group_members(account_id, group_id, ["alice", "bob"])
    assert await manager.get_group_members("acme", "engineering") == []


async def test_file_batch_writes_once_and_keeps_indexes_unchanged_on_write_failure(monkeypatch):
    agfs = InMemoryAGFS()
    manager = build_api_key_manager(
        "root", cast(VikingFS, SimpleNamespace(agfs=agfs)), issue_user_keys=False
    )
    await manager.load()
    try:
        await manager.create_account("acme", "alice")
        await manager.register_user("acme", "bob")
        await manager.create_group("acme", "engineering")
        store = manager._store
        assert isinstance(store, FileStore)
        write = AsyncMock(wraps=store._write_groups_json)
        monkeypatch.setattr(store, "_write_groups_json", write)
        write.side_effect = OSError("group store unavailable")

        with pytest.raises(OSError, match="group store unavailable"):
            await manager.add_group_members("acme", "engineering", ["alice", "bob"])
        assert await manager.get_group_members("acme", "engineering") == []
        assert await manager.get_user_group_ids("acme", "alice") == ()
        assert await manager.get_user_group_ids("acme", "bob") == ()

        write.reset_mock(side_effect=True)
        await manager.add_group_members("acme", "engineering", ["alice", "bob", "bob"])
        write.assert_awaited_once()
        await manager.add_group_members("acme", "engineering", ["bob", "alice"])
        write.assert_awaited_once()
    finally:
        await manager.close()


@pytest.mark.parametrize("fails", [False, True])
async def test_redis_batch_invalidates_all_distinct_users_only_after_success(monkeypatch, fails):
    mysql = SimpleNamespace(
        _service_name="test-batch",
        _engine_options={},
        add_group_members=AsyncMock(return_value=True),
    )
    store = RedisMySQLAccountStore(
        service_name="test-batch",
        mysql_store=cast(MySQLAccountStore, mysql),
        params={"cache": {"provider": "redis", "params": {}}},
    )

    @asynccontextmanager
    async def unlocked(account_id):
        assert account_id == "acme"
        yield

    monkeypatch.setattr(store, "_account_lock", unlocked)
    invalidate = AsyncMock()
    monkeypatch.setattr(store, "_invalidate", invalidate)
    if fails:
        mysql.add_group_members.side_effect = NotFoundError("bob", "user")
        with pytest.raises(NotFoundError):
            await store.add_group_members("acme", "engineering", ["alice", "bob", "alice"])
        invalidate.assert_not_awaited()
    else:
        assert await store.add_group_members("acme", "engineering", ["alice", "bob", "alice"])
        invalidate.assert_awaited_once_with(
            "acme", store._group_ids_key("acme", "alice"), store._group_ids_key("acme", "bob")
        )
    mysql.add_group_members.assert_awaited_once_with("acme", "engineering", ["alice", "bob"])
