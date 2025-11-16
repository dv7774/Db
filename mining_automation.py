#!/usr/bin/env python3
"""
XYO Mining / Portfolio Automation Script

Features:
- Uses Etherscan to fetch real ETH + XYO balances
- Uses CoinGecko to fetch live USD prices
- Logs progress over a session (like your old simulator)
- Writes a CSV portfolio report per run
- Prints a liquidation summary vs target USD

Environment variables required:
  ETHERSCAN_API_KEY       - Etherscan API key
  XYO_WALLET_ADDRESS      - Wallet address to monitor
Optional:
  LIQUIDATION_TARGET_USD  - Target liquidation amount (default: 15000)
"""

import argparse
import time
import os
import sys
import csv
from pathlib import Path
from datetime import datetime, timedelta

import requests


XYO_CONTRACT = "0x55296f69f40Ea6d20E478533C15a6B08b654E758"  # XYO token
ETHERSCAN_BASE = "https://api.etherscan.io/api"
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=ethereum,xyo-network&vs_currencies=usd"
)


def check_environment_variables():
    """Check if required environment variables are set."""
    required_vars = ["ETHERSCAN_API_KEY", "XYO_WALLET_ADDRESS"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print("=" * 60)
        print("❌ ERROR: Missing Required Environment Variables")
        print("=" * 60)
        print("")
        print("The following environment variables are not set:")
        for var in missing_vars:
            print(f"  • {var}")
        print("")
        print("Setup Instructions:")
        print("  1. For GitHub Actions:")
        print("     - Go to Settings → Secrets and variables → Actions")
        print("     - Add secrets: ETHERSCAN_API_KEY and XYO_WALLET_ADDRESS")
        print("")
        print("  2. For local testing:")
        print("     export ETHERSCAN_API_KEY='your_api_key'")
        print("     export XYO_WALLET_ADDRESS='0x...'")
        print("")
        print("For detailed setup instructions, see MINING_SETUP.md")
        print("=" * 60)
        sys.exit(1)

    target_usd = float(os.environ.get("LIQUIDATION_TARGET_USD", "15000"))

    return {
        "api_key": os.environ.get("ETHERSCAN_API_KEY"),
        "wallet_address": os.environ.get("XYO_WALLET_ADDRESS"),
        "target_usd": target_usd,
    }


def etherscan_request(params):
    """Helper for Etherscan API calls with basic error handling."""
    try:
        resp = requests.get(ETHERSCAN_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "0" and data.get("message") != "OK":
            raise RuntimeError(data.get("result", "Unknown Etherscan error"))
        return data
    except Exception as e:
        print(f"  ⚠️  Etherscan API error: {e}")
        return None


def get_eth_balance(api_key, wallet):
    """Return ETH balance (float) for a wallet."""
    params = {
        "module": "account",
        "action": "balance",
        "address": wallet,
        "tag": "latest",
        "apikey": api_key,
    }
    data = etherscan_request(params)
    if not data:
        return None
    # balance is in Wei; convert to ETH
    try:
        wei = int(data["result"])
        return wei / 10**18
    except Exception as e:
        print(f"  ⚠️  Failed to parse ETH balance: {e}")
        return None


def get_xyo_balance(api_key, wallet):
    """Return XYO token balance (float) for a wallet."""
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": XYO_CONTRACT,
        "address": wallet,
        "tag": "latest",
        "apikey": api_key,
    }
    data = etherscan_request(params)
    if not data:
        return None
    try:
        raw = int(data["result"])
        # XYO has 18 decimals
        return raw / 10**18
    except Exception as e:
        print(f"  ⚠️  Failed to parse XYO balance: {e}")
        return None


def get_usd_prices():
    """Fetch ETH and XYO prices in USD from CoinGecko."""
    try:
        resp = requests.get(COINGECKO_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        eth_usd = data["ethereum"]["usd"]
        xyo_usd = data["xyo-network"]["usd"]
        return eth_usd, xyo_usd
    except Exception as e:
        print(f"  ⚠️  CoinGecko price error: {e}")
        return None, None


def write_csv_report(rows):
    """Write a CSV report for this session and return the file path."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = reports_dir / f"portfolio_report_{timestamp}.csv"

    fieldnames = [
        "timestamp_utc",
        "wallet",
        "eth_balance",
        "eth_usd",
        "xyo_balance",
        "xyo_usd",
        "total_usd",
    ]

    with file_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return file_path


def simulate_mining(duration_minutes, config):
    """
    Run a mining/portfolio monitoring session for the specified duration.

    Every ~10 seconds:
      - fetch ETH balance
      - fetch XYO balance
      - fetch prices (once at start, reuse)
      - log progress
      - accumulate rows for CSV
    """
    wallet = config["wallet_address"]
    target_usd = config["target_usd"]

    print("╔══════════════════════════════════════════════════╗")
    print("║   XYO Mining & Portfolio Automation - Session   ║")
    print("╚══════════════════════════════════════════════════╝")
    print("")
    print("Configuration:")
    print(f"  • Wallet: {wallet[:10]}...{wallet[-8:]}")
    print(f"  • Duration: {duration_minutes} minute(s)")
    print(f"  • Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  • Target liquidation: ${target_usd:,.2f} USD")
    print("")

    print("Fetching USD prices from CoinGecko...")
    eth_usd, xyo_usd = get_usd_prices()
    if eth_usd is None or xyo_usd is None:
        print("❌ Could not get prices. Aborting session.")
        sys.exit(1)

    print(f"  • ETH price: ${eth_usd:,.4f}")
    print(f"  • XYO price: ${xyo_usd:,.8f}")
    print("")
    print("=" * 60)

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    iteration = 0
    rows = []

    while datetime.now() < end_time:
        iteration += 1
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        elapsed = (datetime.now() - start_time).total_seconds()
        remaining = (end_time - datetime.now()).total_seconds()
        progress = (elapsed / (duration_minutes * 60)) * 100

        print("")
        print(f"[Iteration {iteration}] {datetime.now().strftime('%H:%M:%S')}")
        print("  ⛏️  Processing block data...")
        print("  📊 Fetching balances via Etherscan...")

        eth_balance = get_eth_balance(config["api_key"], wallet)
        xyo_balance = get_xyo_balance(config["api_key"], wallet)

        if eth_balance is None or xyo_balance is None:
            print("  ⚠️  Skipping this iteration due to API error.")
        else:
            eth_value = eth_balance * eth_usd
            xyo_value = xyo_balance * xyo_usd
            total_usd = eth_value + xyo_value

            print(f"  💰 ETH: {eth_balance:.6f} (~${eth_value:,.2f})")
            print(f"  💠 XYO: {xyo_balance:,.0f} (~${xyo_value:,.2f})")
            print(f"  ✅ Total portfolio (ETH + XYO): ${total_usd:,.2f}")
            print(f"  🎯 Target liquidation: ${target_usd:,.2f}")
            print(
                f"  📈 Progress: {progress:.1f}% | "
                f"Elapsed: {elapsed:.1f}s | Remaining: {max(remaining,0):.1f}s"
            )

            rows.append(
                {
                    "timestamp_utc": now,
                    "wallet": wallet,
                    "eth_balance": f"{eth_balance:.10f}",
                    "eth_usd": f"{eth_value:.2f}",
                    "xyo_balance": f"{xyo_balance:.10f}",
                    "xyo_usd": f"{xyo_value:.2f}",
                    "total_usd": f"{total_usd:.2f}",
                }
            )

        # Sleep up to 10 seconds between iterations
        remaining_time = (end_time - datetime.now()).total_seconds()
        if remaining_time > 0:
            time.sleep(min(10, remaining_time))
        else:
            break

    # Final summary
    total_time = (datetime.now() - start_time).total_seconds()
    print("")
    print("=" * 60)
    print("")
    print("╔══════════════════════════════════════════════════╗")
    print("║          Mining / Portfolio Session Done         ║")
    print("╚══════════════════════════════════════════════════╝")
    print("")
    print(f"  ✓ Total iterations: {iteration}")
    print(f"  ✓ Total time: {total_time:.1f}s ({total_time/60:.2f} minutes)")

    if rows:
        last = rows[-1]
        total_usd = float(last["total_usd"])
        print(f"  ✓ Final total (ETH + XYO): ${total_usd:,.2f}")
        gap = total_usd - target_usd
        if gap >= 0:
            print(
                f"  🟢 You are ABOVE the target by ${gap:,.2f}. "
                "You could plan liquidation now."
            )
        else:
            print(
                f"  🟡 You are BELOW the target by ${-gap:,.2f}. "
                "You may need additional assets or price movement."
            )

        report_path = write_csv_report(rows)
        print(f"  📝 CSV report written to: {report_path}")
    else:
        print("  ⚠️ No successful balance samples recorded; no CSV created.")

    print("")
    print("Status: All mining/portfolio operations completed. 🎉")


def main():
    """Main entry point for the mining automation script."""
    parser = argparse.ArgumentParser(
        description="XYO Mining / Portfolio Automation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables Required:
  ETHERSCAN_API_KEY       - API key for Etherscan
  XYO_WALLET_ADDRESS      - XYO wallet address to monitor

Optional:
  LIQUIDATION_TARGET_USD  - Target USD amount (default: 15000)

Example:
  python mining_automation.py --duration-minutes 1
        """,
    )

    parser.add_argument(
        "--duration-minutes",
        type=int,
        required=True,
        help="Duration to run mining automation in minutes",
    )

    args = parser.parse_args()

    if args.duration_minutes <= 0:
        print("Error: Duration must be a positive integer")
        sys.exit(1)

    config = check_environment_variables()

    try:
        simulate_mining(args.duration_minutes, config)
    except KeyboardInterrupt:
        print("\n⚠️  Mining automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during mining automation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()