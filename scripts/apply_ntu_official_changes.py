"""Apply the reviewed Oct 10 portal reference batch, retaining pending selection."""
import argparse
from pathlib import Path
from exchange_info.ntu_official_changes import apply_official_changes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, default=Path(__file__).parents[1] / "src/exchange_info/official_data/ntu")
    args = parser.parse_args()
    print(apply_official_changes(args.bundle_dir))
