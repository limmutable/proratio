#!/usr/bin/env python3
"""
Show Trading Configuration

Display current trading configuration with all parameters.

Usage:
    python scripts/show_trading_config.py
    python scripts/show_trading_config.py --save my_config.json
"""

import sys
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from proratio_core.config.trading_config import get_trading_config, TradingConfig


def main():
    parser = argparse.ArgumentParser(description='Show trading configuration')
    parser.add_argument(
        '--load',
        type=str,
        help='Load configuration from JSON file'
    )
    parser.add_argument(
        '--save',
        type=str,
        help='Save configuration to JSON file'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration only'
    )

    args = parser.parse_args()

    # Load config
    if args.load:
        config_file = Path(args.load)
        if not config_file.exists():
            print(f"❌ Config file not found: {config_file}")
            sys.exit(1)
        config = TradingConfig.load_from_file(config_file)
        print(f"✅ Loaded configuration from: {config_file}")
    else:
        # Use default config
        default_config = project_root / 'proratio_core' / 'config' / 'trading_config.json'
        if default_config.exists():
            config = TradingConfig.load_from_file(default_config)
            print(f"✅ Loaded default configuration from: {default_config}")
        else:
            config = get_trading_config()
            print("✅ Using built-in default configuration")

    # Validate
    errors = config.validate()
    if errors:
        print("\n❌ VALIDATION ERRORS:")
        for error in errors:
            print(f"  - {error}")
        if args.validate:
            sys.exit(1)
    else:
        print("✅ Configuration is valid")

    # Print summary
    if not args.validate:
        config.print_summary()

    # Save if requested
    if args.save:
        save_path = Path(args.save)
        config.save_to_file(save_path)
        print(f"\n💾 Saved configuration to: {save_path}")


if __name__ == '__main__':
    main()
