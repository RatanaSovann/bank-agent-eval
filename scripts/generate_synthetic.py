"""Regenerate synthetic data from a versioned prompt folder through the Anthropic API.

v1 was written by Claude in chat (see data/synthetic/v1/MANIFEST.json). Use this script
to create API-generated versions (v2, v3, ...) where the model ID, parameters, prompt
hashes and output hashes are all logged, so every version can be traced to its prompt.

Rules:
- Never overwrite an existing version folder.
- To change the data, copy prompts/<old> to prompts/<new>, edit the copy, then run this.

Usage:
    export ANTHROPIC_API_KEY=...            # keep it in .env, never commit it
    uv run --with anthropic python scripts/generate_synthetic.py --prompts v2 --out v2 --model <pinned-model-id>
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "data" / "synthetic"
TASKS = {"customers.md": "customers.jsonl", "scenarios.md": "scenarios.jsonl"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True, help="prompt version folder, e.g. v2")
    ap.add_argument("--out", required=True, help="output version folder, e.g. v2")
    ap.add_argument("--model", required=True, help="pinned model ID")
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    prompt_dir = SYN / "prompts" / args.prompts
    out_dir = SYN / args.out
    if out_dir.exists():
        raise SystemExit(f"{out_dir} already exists: versions are never overwritten")
    out_dir.mkdir(parents=True)

    client = anthropic.Anthropic()
    manifest = {
        "version": args.out,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": {"model": args.model, "method": "Anthropic Messages API", "temperature": args.temperature},
        "prompts": {},
        "outputs": {},
    }
    context = ""
    for prompt_name, out_name in TASKS.items():
        prompt_bytes = (prompt_dir / prompt_name).read_bytes()
        manifest["prompts"][prompt_name] = {"path": str((prompt_dir / prompt_name).relative_to(ROOT)), "sha256": sha256_bytes(prompt_bytes)}
        user = prompt_bytes.decode() + context + "\n\nReturn only the JSON Lines, no commentary."
        msg = client.messages.create(model=args.model, max_tokens=16000, temperature=args.temperature,
                                     messages=[{"role": "user", "content": user}])
        text = "".join(block.text for block in msg.content if block.type == "text").strip()
        lines = [json.loads(line) for line in text.splitlines() if line.strip()]  # fails loudly on bad JSON
        out_path = out_dir / out_name
        out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in lines) + "\n", encoding="utf-8")
        manifest["outputs"][out_name] = {"path": str(out_path.relative_to(ROOT)), "sha256": sha256_bytes(out_path.read_bytes()),
                                         "rows": len(lines), "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}
        if out_name == "customers.jsonl":  # scenarios must reference these customers
            context = "\n\ncustomers.jsonl:\n" + out_path.read_text()
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest["outputs"], indent=2))


if __name__ == "__main__":
    main()
