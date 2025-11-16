def check_environment_variables():
    """Check if required environment variables are set."""
    required_vars = [
        "ETHERSCAN_API_KEY",
        "XYO_WALLET_ADDRESS",
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print("=" * 60)
        print("❌ ERROR: Missing Required Environment Variables")
        print("=" * 60)
        print()
        print("The following environment variables are not set:")
        for var in missing_vars:
            print(f"  • {var}")
        print()
        print("Setup Instructions:")
        print("  1. For GitHub Actions:")
        print("     - Go to Settings → Secrets and variables → Actions")
        print("     - Add secrets: ETHERSCAN_API_KEY, XYO_WALLET_ADDRESS")
        print()
        print("  2. For local runs:")
        print("     - Export the variables in your terminal, e.g.:")
        print("       export ETHERSCAN_API_KEY='your-key-here'")
        print("       export XYO_WALLET_ADDRESS='your-wallet-here'")
        print()
        sys.exit(1)