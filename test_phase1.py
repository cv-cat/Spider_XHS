"""Phase 1 cookie validation: minimum-request smoke test for Spider_XHS APIs.

Total HTTP requests issued: 3 (search note, search user, user info).
Inserts sleeps between calls to look less bot-like.
"""

from __future__ import annotations

import os

import sys
import time

from loguru import logger

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env

QUERY = "榴莲"
SLEEP_SECONDS = 4


def _truncate(value: object, limit: int = 200) -> str:
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def main() -> int:
    cookies_str = load_env()
    if not cookies_str:
        logger.error("COOKIES env var is empty — aborting")
        return 1

    apis = XHS_Apis()

    logger.info(f"[1/3] search_some_note(query={QUERY!r}, require_num=1)")
    success, msg, notes = apis.search_some_note(QUERY, 1, cookies_str)
    if not success or not notes:
        logger.error(f"search_some_note failed: success={success} msg={_truncate(msg)}")
        return 2
    first = notes[0]
    logger.info(f"note hit: id={first.get('id')} model_type={first.get('model_type')} keys={list(first.keys())[:8]}")

    time.sleep(SLEEP_SECONDS)

    logger.info(f"[2/3] search_some_user(query={QUERY!r}, require_num=1)")
    success, msg, users = apis.search_some_user(QUERY, 1, cookies_str)
    if not success or not users:
        logger.error(f"search_some_user failed: success={success} msg={_truncate(msg)}")
        return 3
    user = users[0]
    user_id = user.get("id") or user.get("user_id") or user.get("userid")
    logger.info(
        f"user hit: id={user_id} name={user.get('name') or user.get('nickname')} keys={list(user.keys())[:10]}"
    )
    if not user_id:
        logger.error(f"could not locate user id in search result; raw={_truncate(user)}")
        return 4

    time.sleep(SLEEP_SECONDS)

    logger.info(f"[3/3] get_user_info(user_id={user_id})")
    success, msg, info = apis.get_user_info(user_id, cookies_str)
    if not success:
        logger.error(f"get_user_info failed: success={success} msg={_truncate(msg)}")
        return 5
    data = (info or {}).get("data") or {}
    basic = data.get("basic_info") or data.get("basicInfo") or {}
    interactions = data.get("interactions") or []
    logger.info(
        f"user_info ok: nickname={basic.get('nickname')} ip={basic.get('ip_location')} "
        f"gender={basic.get('gender')} desc={_truncate(basic.get('desc'), 80)}"
    )
    logger.info(f"interactions: {_truncate(interactions, 200)}")

    logger.success("Phase 1 smoke test passed — Cookie is alive on all three endpoints.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
