# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0
"""Resource tree update modes used by add_resource."""

from typing import Literal

REPLACE = "replace"
UPSERT = "upsert"

ResourceUpdateMode = Literal["replace", "upsert"]
DEFAULT_RESOURCE_UPDATE_MODE: ResourceUpdateMode = REPLACE
SUPPORTED_RESOURCE_UPDATE_MODES = frozenset({REPLACE, UPSERT})


def normalize_resource_update_mode(value: str | None) -> ResourceUpdateMode:
    mode = value or DEFAULT_RESOURCE_UPDATE_MODE
    if mode not in SUPPORTED_RESOURCE_UPDATE_MODES:
        supported = ", ".join(sorted(SUPPORTED_RESOURCE_UPDATE_MODES))
        raise ValueError(f"Invalid resource mode '{mode}'. Supported values: {supported}")
    return mode  # type: ignore[return-value]
