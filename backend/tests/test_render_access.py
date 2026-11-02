import ipaddress

import pytest

from career_assistant.render_access import close_access, open_access


def test_maintenance_adds_only_one_runner_and_preserves_other_operators(tmp_path):
    original = {"cidrBlock": "198.51.100.1/32", "description": "existing operator"}
    rows = [original]
    changes = []

    def api(method, database_id, token, payload=None):
        assert database_id == "dpg-test-a"
        if method == "PATCH":
            rows[:] = payload["ipAllowList"]
            changes.append(list(rows))
        return {"ipAllowList": list(rows)}

    state = tmp_path / "access.json"
    open_access(
        "dpg-test-a",
        "synthetic",
        state,
        api=api,
        address=ipaddress.ip_address("8.8.8.8"),
    )
    assert rows[0] == original
    assert rows[1]["cidrBlock"] == "8.8.8.8/32"
    assert state.stat().st_mode & 0o777 == 0o600
    concurrent = {"cidrBlock": "203.0.113.1/32", "description": "another operator"}
    rows.append(concurrent)
    close_access("synthetic", state, api=api)
    assert rows == [original, concurrent]
    assert len(changes) == 2 and not state.exists()


def test_existing_network_access_is_never_removed(tmp_path):
    def api(method, database_id, token, payload=None):
        assert method == "GET"
        return {"ipAllowList": [{"cidrBlock": "8.8.8.0/24", "description": "existing"}]}

    state = tmp_path / "access.json"
    assert not open_access(
        "dpg-test-a",
        "synthetic",
        state,
        api=api,
        address=ipaddress.ip_address("8.8.8.8"),
    )["added_single_runner"]
    close_access("synthetic", state, api=api)
    assert not state.exists()


def test_access_timeout_can_be_cleaned_without_replacing_an_existing_state(tmp_path):
    rows = []

    def api(method, database_id, token, payload=None):
        if method == "PATCH":
            rows[:] = payload["ipAllowList"]
            if rows:
                raise TimeoutError("synthetic ambiguous timeout")
        return {"ipAllowList": list(rows)}

    state = tmp_path / "access.json"
    with pytest.raises(TimeoutError):
        open_access(
            "dpg-test-a",
            "synthetic",
            state,
            api=api,
            address=ipaddress.ip_address("8.8.8.8"),
        )
    with pytest.raises(FileExistsError):
        open_access(
            "dpg-test-a",
            "synthetic",
            state,
            api=api,
            address=ipaddress.ip_address("8.8.8.8"),
        )
    close_access("synthetic", state, api=api)
    assert rows == []
    assert (
        close_access("synthetic", state, api=api)["event"]
        == "maintenance_access_not_opened"
    )
