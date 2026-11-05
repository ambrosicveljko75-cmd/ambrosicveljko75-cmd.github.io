#!/usr/bin/env python3
"""Read-only HilltopAds publisher bridge for GitHub Actions.
It never exposes the API key and never injects advertising code into the site.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

VERIFY_FILENAME = ""
VERIFY_CODE = "8081f16693262819eb20a5a22a45dacb911a4946"
BASE_URL = "https://api.hilltopads.com/publisher"
BLOCKED = ("igaming", "gambling", "casino", "betting", "sportsbook", "sportbook", "kladionica", "kazino", "popunder", "directlink", "adult", "sweepstakes")

def clean(value: Any) -> bool:
    return not any(word in json.dumps(value, ensure_ascii=False).lower() for word in BLOCKED)

def api_get(endpoint: str, key: str, params: dict[str, str] | None = None) -> Any:
    query = {"key": key}
    if params:
        query.update(params)
    url = f"{BASE_URL}/{endpoint.lstrip('/')}?{urllib.parse.urlencode(query)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Ambrosic-HilltopAds-Bridge/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def main() -> None:
    today = dt.date.today()
    week_ago = today - dt.timedelta(days=7)
    key = os.environ.get("HILLTOPADS_API_KEY", "").strip()
    status: dict[str, Any] = {
        "updated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository": "ambrosicveljko75-cmd.github.io",
        "site": "https://ambrosicveljko75-cmd.github.io/",
        "verification": {"file": f"https://ambrosicveljko75-cmd.github.io/{VERIFY_FILENAME}", "code": VERIFY_CODE, "status": "READY_FOR_VERIFICATION"},
        "guardrails": {"mainstream_only": True, "blocked_keywords": list(BLOCKED), "advertising_scripts_embedded": False},
        "api": {"status": "WAITING_FOR_API_KEY_SECRET", "mode": "read_only", "endpoints": ["balance", "inventory", "listStats"]},
    }
    if key:
        try:
            balance = api_get("balance", key)
            inventory = api_get("inventory", key)
            stats = api_get("listStats", key, {"date": str(week_ago), "date2": str(today), "group": "date"})
            zones = inventory.get("result", inventory.get("zones", [])) if isinstance(inventory, dict) else []
            if not isinstance(zones, list):
                zones = []
            clean_zones = [z for z in zones if isinstance(z, dict) and clean(z)]
            status["api"] = {"status": "CONNECTED", "mode": "read_only", "last_7_days": {"from": str(week_ago), "to": str(today)}, "clean_zone_count": len(clean_zones), "total_zone_count": len(zones), "balance": balance, "statistics": stats}
        except Exception as exc:
            status["api"] = {"status": "ERROR", "mode": "read_only", "message": str(exc)}
    Path("hilltopads_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status["api"]["status"], "verification": status["verification"]["status"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
