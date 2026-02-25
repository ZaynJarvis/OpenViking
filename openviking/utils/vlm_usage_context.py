# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""VLM token usage tracking context manager.

Supports both synchronous and asynchronous usage.
"""

from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, Optional

from openviking_cli.utils import get_logger

logger = get_logger(__name__)


@dataclass
class VLMUsageInfo:
    """VLM token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class VLMUsageSnapshot:
    """Snapshot of VLM token usage at a point in time."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class VLMRequestTracker:
    """Tracks VLM token usage for a single request."""

    def __init__(self):
        self._start = VLMUsageSnapshot()
        self._end = VLMUsageSnapshot()
        self._captured = False

    def capture_start(self, vlm_base: Any) -> None:
        """Capture the starting token usage from VLM base."""
        total = vlm_base.get_token_usage_summary()
        self._start = VLMUsageSnapshot(
            prompt_tokens=total.get("total_prompt_tokens", 0),
            completion_tokens=total.get("total_completion_tokens", 0),
            total_tokens=total.get("total_tokens", 0),
        )
        self._captured = True

    def capture_end(self, vlm_base: Any) -> VLMUsageInfo:
        """Capture the ending token usage and return the delta."""
        total = vlm_base.get_token_usage_summary()
        self._end = VLMUsageSnapshot(
            prompt_tokens=total.get("total_prompt_tokens", 0),
            completion_tokens=total.get("total_completion_tokens", 0),
            total_tokens=total.get("total_tokens", 0),
        )
        return VLMUsageInfo(
            prompt_tokens=self._end.prompt_tokens - self._start.prompt_tokens,
            completion_tokens=self._end.completion_tokens - self._start.completion_tokens,
            total_tokens=self._end.total_tokens - self._start.total_tokens,
        )

    def get_usage(self) -> VLMUsageInfo:
        """Get the usage delta from captured start/end."""
        return VLMUsageInfo(
            prompt_tokens=self._end.prompt_tokens - self._start.prompt_tokens,
            completion_tokens=self._end.completion_tokens - self._start.completion_tokens,
            total_tokens=self._end.total_tokens - self._start.total_tokens,
        )


# Context variable to store the current request tracker
_vlm_usage_ctx: ContextVar[Optional[VLMRequestTracker]] = ContextVar("vlm_usage_ctx", default=None)


def _get_vlm_instance() -> Optional[Any]:
    """Get the global VLM instance."""
    try:
        from openviking_cli.utils.config import get_openviking_config

        vlm = get_openviking_config().vlm
        if vlm and vlm.is_available():
            return vlm.get_vlm_instance()
    except Exception as e:
        logger.debug(f"Failed to get VLM instance: {e}")
    return None


@contextmanager
def track_vlm_usage():
    """Synchronous context manager to track VLM token usage for the current request.

    Usage:
        with track_vlm_usage():
            # ... do work that uses VLM ...
            result = some_operation()
        usage = get_request_vlm_usage()
    """
    tracker = VLMRequestTracker()
    vlm_instance = _get_vlm_instance()
    if vlm_instance:
        tracker.capture_start(vlm_instance)
    token = _vlm_usage_ctx.set(tracker)
    try:
        yield tracker
    finally:
        if vlm_instance:
            tracker.capture_end(vlm_instance)
        _vlm_usage_ctx.reset(token)


@asynccontextmanager
async def track_vlm_usage_async():
    """Asynchronous context manager to track VLM token usage for the current request.

    Usage:
        async with track_vlm_usage_async():
            # ... do async work that uses VLM ...
            result = await some_async_operation()
        usage = get_request_vlm_usage()
    """
    tracker = VLMRequestTracker()
    vlm_instance = _get_vlm_instance()
    if vlm_instance:
        tracker.capture_start(vlm_instance)
    token = _vlm_usage_ctx.set(tracker)
    try:
        yield tracker
    finally:
        if vlm_instance:
            tracker.capture_end(vlm_instance)
        _vlm_usage_ctx.reset(token)


def get_request_vlm_usage() -> Optional[VLMUsageInfo]:
    """Get the VLM token usage for the current request.

    Returns:
        VLMUsageInfo with prompt_tokens, completion_tokens, total_tokens,
        or None if tracking is not active or VLM is not available.
    """
    tracker = _vlm_usage_ctx.get()
    if not tracker:
        return None

    vlm_instance = _get_vlm_instance()
    if not vlm_instance:
        return None

    return tracker.capture_end(vlm_instance)


def get_request_vlm_usage_dict() -> Optional[Dict[str, int]]:
    """Get the VLM token usage as a dictionary for the current request.

    Convenience function that returns usage as a dict or None.

    Returns:
        Dictionary with prompt_tokens, completion_tokens, total_tokens,
        or None if not in tracking context
    """
    usage = get_request_vlm_usage()
    if usage is None:
        return None
    return usage.to_dict()
