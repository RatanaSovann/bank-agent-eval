"""Fetch the public CommBank help pages listed in data/commbank_pages.csv.

Run locally (your machine can reach commbank.com.au; the build environment could not).
Before running: read the site's terms of use. Pages are saved for private research only.
Do not commit them to a public repo or republish them.

Usage:
    uv run --with requests --with beautifulsoup4 --with pypdf python scripts/fetch_commbank_pages.py
"""
import csv
import hashlib
import io
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PAGES_CSV = ROOT / "data" / "commbank_pages.csv"
OUT = ROOT / "data" / "raw" / "commbank"
LOG = OUT / "fetch_log.csv"
USER_AGENT = "bank-agent-eval research fetcher (personal portfolio project; contact via GitHub)"
DELAY_SECONDS = 3


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    # CommBank pages have no <main> tag; their "skip to main content" link targets this id.
    main = soup.find(id="skipmaincontent") or soup.find("main") or soup.body or soup
    lines = [line.strip() for line in main.get_text("\n").splitlines()]
    return "\n".join(line for line in lines if line)


def pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    robots = urllib.robotparser.RobotFileParser("https://www.commbank.com.au/robots.txt")
    robots.read()
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    rows = list(csv.DictReader(PAGES_CSV.open(encoding="utf-8")))
    with LOG.open("w", newline="", encoding="utf-8") as log_file:
        log = csv.writer(log_file)
        log.writerow(["page_id", "url", "status", "fetched_at", "text_file", "sha256", "note"])
        for row in rows:
            pid, url = row["page_id"], row["url"]
            fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            if not robots.can_fetch(USER_AGENT, url):
                log.writerow([pid, url, "skipped", fetched_at, "", "", "disallowed by robots.txt"])
                print(f"{pid}: skipped (robots.txt)")
                continue
            try:
                resp = session.get(url, timeout=30)
                resp.raise_for_status()
                if url.lower().endswith(".pdf"):
                    (OUT / f"{pid}.pdf").write_bytes(resp.content)
                    text = pdf_text(resp.content)
                else:
                    (OUT / f"{pid}.html").write_text(resp.text, encoding="utf-8")
                    text = page_text(resp.text)
                header = f"page_id: {pid}\nurl: {url}\nfetched_at: {fetched_at}\n\n"
                text_path = OUT / f"{pid}.txt"
                text_path.write_text(header + text, encoding="utf-8")
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                log.writerow([pid, url, resp.status_code, fetched_at, text_path.name, digest, ""])
                print(f"{pid}: ok ({len(text):,} chars)")
            except Exception as exc:  # keep going; the log records failures
                log.writerow([pid, url, "error", fetched_at, "", "", str(exc)[:200]])
                print(f"{pid}: error {exc}")
            time.sleep(DELAY_SECONDS)


if __name__ == "__main__":
    main()
