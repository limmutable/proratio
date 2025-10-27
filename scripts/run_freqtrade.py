import sys
import json
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_utilities.config.loader import load_and_hydrate_config

def main():
    """
    Loads and hydrates the Freqtrade config, then launches Freqtrade.
    """
    # The script name is the first argument, so the config path is the second
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_freqtrade.py <path_to_config>")
        sys.exit(1)

    config_path = sys.argv[1]
    
    # All other arguments are passed to freqtrade
    freqtrade_args = sys.argv[2:]

    hydrated_config = load_and_hydrate_config(config_path)

    cmd = [
        "freqtrade",
        *freqtrade_args,
        "--config",
        "-",  # Read config from stdin
    ]

    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    process.communicate(input=json.dumps(hydrated_config))

if __name__ == "__main__":
    main()
