#!/usr/bin/env python3
"""
XYO Mining Automation Script

This script is intended to be used in GitHub Actions to monitor an XYO wallet.
It does **not** actually mine, but it simulates "mining cycles" by periodically:

- Checking ETH balance (gas / base value)
- Checking XYO token balance
- Printing structured logs for later parsing

Environment variables expected (set in GitHub → Settings → Secrets and variables → Actions):

  - ETHERSCAN_API_KEY     : Your Etherscan API key
  - XYO_WALLET_ADDRESS    : Wallet address to monitor (0x...)
  - XYO_CONTRACT_ADDRESS  : (optional) XYO ERC-20 contract; defaults to main XYO token

Example GitHub Actions step:

  - name: Run mining automation
    run: |
      python mining_automation.py --interval 900 --runtime-minutes 60

"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta

import requests

# Default XYO contract (legacy XYO ERC-20)
DEFAULT_XYO_CONTRACT = "0x55296f69f40Ea6d20E478533C15a6B08b654E758"
XYO_DECIMALS = 18
ETH_DECIMALS = 18


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log_line(msg: str) -> None:
    """Print a timestamped log line (friendly for GitHub Actions)."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] {msg}", flush=True)


def check_environment_variables() -> dict:
    """Check if required environment variables are set, return them in a dict.

    Exits with code 1 if required variables are missing.
    """
    required_vars = ["ETHERSCAN_API_KEY", "XYO_WALLET_ADDRESS"]
    optional_vars = ["XYO_CONTRACT_ADDRESS"]

    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        print("=" * 60)
        print("❌ ERROR: Missing Required Environment Variables")
        print("=" * 60)
        print("")
        print("The following environment variables are not set:")
        for var in missing:
            print(f"  • {var}")
        print("")
        print("Setup Instructions:")
        print("  1. In GitHub: Repo → Settings → Secrets and variables → Actions")
        print("  2. Add these secrets:")
        print("       - ETHERSCAN_API_KEY")
        print("       - XYO_WALLET_ADDRESS")
        print("  3. (Optional) Add XYO_CONTRACT_ADDRESS to override the default XYO token.")
        print("")
        sys.exit(1)

    cfg = {var: os.environ.get(var) for var in required_vars + optional_vars}
    if not cfg["XYO_CONTRACT_ADDRESS"]:
        cfg["XYO_CONTRACT_ADDRESS"] = DEFAULT_XYO_CONTRACT

    return cfg


def etherscan_get(url: str, params: dict) -> dict:
    """Call Etherscan API and handle common errors, returning JSON."""
    try:
        resp = requests.get(url, params=params, timeout=15)
    except requests.RequestException as exc:
        log_line(f"❌ Network error talking to Etherscan: {exc}")
        return {"status": "0", "message": "network error", "result": None}

    if resp.status_code != 200:
        log_line(f"❌ Etherscan HTTP {resp.status_code}: {resp.text[:200]}")
        return {"status": "0", "message": f"http {resp.status_code}", "result": None}

    try:
        data = resp.json()
    except ValueError:
        log_line("❌ Failed to parse JSON from Etherscan.")
        return {"status": "0", "message": "invalid json", "result": None}

    return data


def get_eth_balance(api_key: str, wallet: str) -> float:
    """Return ETH balance as a float in ETH units."""
    base_url = "https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "balance",
        "address": wallet,
        "tag": "latest",
        "apikey": api_key,
    }

    data = etherscan_get(base_url, params)

    if data.get("status") != "1" or data.get("result") is None:
        log_line(f"⚠️ Could not fetch ETH balance: {data.get('message')}")
        return 0.0

    try:
        wei = int(data["result"])
    except (TypeError, ValueError):
        log_line("⚠️ Invalid ETH balance format from Etherscan.")
        return 0.0

    return wei / (10 ** ETH_DECIMALS)


def get_xyo_balance(api_key: str, wallet: str, contract: str) -> float:
    """Return XYO balance as a float in token units."""
    base_url = "https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": contract,
        "address": wallet,
        "tag": "latest",
        "apikey": api_key,
    }

    data = etherscan_get(base_url, params)

    if data.get("status") != "1" or data.get("result") is None:
        log_line(f"⚠️ Could not fetch XYO balance: {data.get('message')}")
        return 0.0

    try:
        raw = int(data["result"])
    except (TypeError, ValueError):
        log_line("⚠️ Invalid XYO balance format from Etherscan.")
        return 0.0

    return raw / (10 ** XYO_DECIMALS)


# ---------------------------------------------------------------------------
# Core mining "loop"
# ---------------------------------------------------------------------------

def run_single_cycle(cfg: dict) -> None:
    """Perform one 'mining' cycle: query balances and log a summary."""
    api_key = cfg["ETHERSCAN_API_KEY"]
    wallet = cfg["XYO_WALLET_ADDRESS"]
    contract = cfg["XYO_CONTRACT_ADDRESS"]

    log_line("🚀 Starting mining cycle")
    log_line(f"👛 Wallet: {wallet}")
    log_line(f"🪙 XYO Contract: {contract}")

    eth_balance = get_eth_balance(api_key, wallet)
    xyo_balance = get_xyo_balance(api_key, wallet, contract)

    # Final structured line (easy to parse from logs later)
    log_line(
        f"✅ MINING_CYCLE_COMPLETE | "
        f"ETH_BAL={eth_balance:.8f} | "
        f"XYO_BAL={xyo_balance:.4f}"
    )


def run_loop(cfg: dict, interval_seconds: int, runtime_minutes: int | None) -> None:
    """Run repeated mining cycles.

    Args:
        cfg: Env configuration dict.
        interval_seconds: Seconds to sleep between cycles.
        runtime_minutes: If not None, stop after this many minutes.
    """
    start = datetime.utcnow()
    end = None
    if runtime_minutes is not None and runtime_minutes > 0:
        end = start + timedelta(minutes=runtime_minutes)
        log_line(
            f"⏱️ Looping every {interval_seconds}s for ~{runtime_minutes} minutes "
            f"(until {end.strftime('%Y-%m-%d %H:%M:%S UTC')})"
        )
    else:
        log_line(f"⏱️ Looping every {interval_seconds}s (no end time set)")

    cycle = 0
    while True:
        cycle += 1
        log_line(f"🔁 Mining cycle #{cycle}")
        run_single_cycle(cfg)

        if end is not None and datetime.utcnow() >= end:
            log_line("🏁 Runtime limit reached, exiting loop.")
            break

        log_line(f"😴 Sleeping {interval_seconds} seconds before next cycle...")
        time.sleep(interval_seconds)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="XYO mining / wallet monitoring script for GitHub Actions."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single mining cycle and exit.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=900,
        help="Seconds between cycles in loop mode (default: 900 = 15 minutes).",
    )
    parser.add_argument(
        "--runtime-minutes",
        type=int,
        default=None,
        help="Maximum runtime in minutes for loop mode. "
             "If omitted, runs until the job times out.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    cfg = check_environment_variables()

    log_line("==============================================")
    log_line("🧠 XYO Mining Automation Script starting up...")
    log_line("==============================================")

    if args.once:
        log_line("Mode: single-cycle run (--once)")
        run_single_cycle(cfg)
    else:
        log_line("Mode: loop")
        run_loop(cfg, interval_seconds=args.interval, runtime_minutes=args.runtime_minutes)

    log_line("✅ Script finished successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())