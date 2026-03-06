from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest

from calorie_app.adapters.telegram import validate_init_data
from calorie_app.config import settings


def _make_init_data(user_id: int = 42, bot_token: str | None = None) -> str:
    token = bot_token or settings.telegram_bot_token
    user_json = json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":"))
    params = {"auth_date": "1700000000", "user": user_json}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


class TestValidateInitData:
    def test_valid_init_data_returns_user(self) -> None:
        init_data = _make_init_data(user_id=12345)
        result = validate_init_data(init_data)
        assert result["id"] == 12345
        assert result["first_name"] == "Test"

    def test_missing_hash_raises(self) -> None:
        init_data = urlencode({"auth_date": "1700000000", "user": '{"id":1}'})
        with pytest.raises(ValueError, match="Missing hash"):
            validate_init_data(init_data)

    def test_invalid_hash_raises(self) -> None:
        # build manually with wrong hash
        user_json = json.dumps({"id": 1, "first_name": "X"}, separators=(",", ":"))
        params = {"auth_date": "1700000000", "user": user_json, "hash": "badhash123"}
        with pytest.raises(ValueError, match="Invalid initData signature"):
            validate_init_data(urlencode(params))

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError):
            validate_init_data("")
