"""Temporary, single-runner Render Postgres access for external maintenance."""

import argparse
import ipaddress
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4


class AccessError(Exception):
    """Safe operator diagnostics without API response bodies or credentials."""


def request(method, database_id, token, payload=None):
    if not re.fullmatch(r"dpg-[a-z0-9-]+", database_id):
        raise AccessError("Configure the intended Render database ID.")
    req = Request(
        f"https://api.render.com/v1/postgres/{database_id}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with build_opener(ProxyHandler({})).open(req, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        raise AccessError(f"Render access update failed (HTTP {error.code}).") from None
    except URLError, TimeoutError, OSError:
        raise AccessError("Render access request failed; check connectivity.") from None


def public_ip():
    try:
        # Postgres uses IPv4; a dual-stack IP service can return the wrong family.
        req = Request("https://api.ipify.org?format=json")
        with build_opener(ProxyHandler({})).open(req, timeout=20) as response:
            address = ipaddress.ip_address(json.load(response)["ip"])
        if address.version != 4 or not address.is_global:
            raise ValueError("Expected a public IPv4 runner address")
        return address
    except URLError, OSError, ValueError, KeyError:
        raise AccessError(
            "Could not determine the maintenance runner address."
        ) from None


def open_access(database_id, token, state_path, *, api=request, address=None):
    address = address or public_ip()
    current = api("GET", database_id, token)["ipAllowList"]
    covered = any(address in ipaddress.ip_network(row["cidrBlock"]) for row in current)
    entry = {
        "cidrBlock": f"{address}/{address.max_prefixlen}",
        "description": "career-maintenance-" + uuid4().hex,
    }
    state = {"database_id": database_id, "entry": entry, "added": not covered}
    state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Record intent first so cleanup also works after an ambiguous API timeout.
    with state_path.open("x") as stream:
        state_path.chmod(0o600)
        json.dump(state, stream)
    if not covered:
        api("PATCH", database_id, token, {"ipAllowList": [*current, entry]})
    return {"event": "maintenance_access_opened", "added_single_runner": not covered}


def close_access(token, state_path, *, api=request):
    if not state_path.exists():
        return {"event": "maintenance_access_not_opened"}
    state = json.loads(state_path.read_text())
    if state["added"]:
        database_id = state["database_id"]
        current = api("GET", database_id, token)["ipAllowList"]
        retained = [row for row in current if row != state["entry"]]
        if retained != current:
            api("PATCH", database_id, token, {"ipAllowList": retained})
    state_path.unlink()
    return {"event": "maintenance_access_closed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["open", "close"])
    parser.add_argument("state", type=Path)
    args = parser.parse_args()
    try:
        token = os.environ["RENDER_API_KEY"]
        result = (
            open_access(os.environ["RENDER_POSTGRES_ID"], token, args.state)
            if args.command == "open"
            else close_access(token, args.state)
        )
        print(json.dumps(result))
    except AccessError as error:
        parser.exit(1, f"Maintenance access failed: {error}\n")
    except OSError, ValueError, KeyError:
        parser.exit(1, "Maintenance access failed; inspect private runner settings.\n")


if __name__ == "__main__":
    main()
