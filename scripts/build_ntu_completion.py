"""Replay the reviewed all-school completion batch in the development checkout."""
import json
from exchange_info.ntu_completion import apply_completion, PACKAGE

if __name__ == "__main__":
    print(json.dumps(apply_completion(PACKAGE / "official_data/ntu", apply_assets=True), ensure_ascii=False))
