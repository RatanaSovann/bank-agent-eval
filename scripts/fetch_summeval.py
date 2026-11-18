"""Download the SummEval expert annotations (used to validate the LLM judge).

Run locally. The file is ~20 MB. Licence: MIT (SummEval repo).
The annotations ship without source articles. To judge consistency you need the
CNN/DailyMail stories, paired with the repo's data_processing/pair_data.py:
    https://github.com/Yale-LILY/SummEval#data-preparation

Usage:
    uv run --with requests python scripts/fetch_summeval.py
"""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://storage.googleapis.com/sfr-summarization-repo-research/model_annotations.aligned.jsonl"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "summeval"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "model_annotations.aligned.jsonl"
    resp = requests.get(URL, timeout=120)
    resp.raise_for_status()
    target.write_bytes(resp.content)
    digest = hashlib.sha256(resp.content).hexdigest()
    rows = resp.content.count(b"\n")
    (OUT / "FETCH_INFO.txt").write_text(
        f"url: {URL}\nfetched_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"sha256: {digest}\nrows: {rows}\n"
    )
    print(f"saved {rows} rows to {target}")
    print("next: pair with CNN/DailyMail stories using SummEval's pair_data.py (see docstring)")


if __name__ == "__main__":
    main()
