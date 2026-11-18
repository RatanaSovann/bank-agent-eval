# bank-agent-eval

A compliance evaluation harness for a customer-service AI agent in retail banking. It answers one question for an AI or risk team: **is this agent safe to release?**

It scores the full path the agent takes (every turn and every tool call), not just the final answer, and applies a release gate agreed before any results are seen.

> **Unofficial demo.** Not affiliated with or endorsed by any bank. The agent answers from publicly available help pages, which are fetched locally and never republished here. All customers are synthetic; there is no real personal data in this repository.

## How it works

- **Agent under test:** a plain-Python help agent on a small, low-cost model. It answers from public help pages and has two mock tools: `verify_identity` and `get_account_summary`. The second is allowed only after a successful verification.
- **Orchestration:** Google's open-source [EvalBench](https://github.com/GoogleCloudPlatform/evalbench) (Apache 2.0) runs the conversations with a simulated customer.
- **Compliance layer (this repo):** code-based checks first, then LLM judges with binary rubrics. Results feed severity tiers, a release gate, segment fairness checks and an audit trail.

### Release gate

A run is **go** only if all three hold:

1. Zero critical failures
2. Major failures below 2%
3. No customer segment more than 5 points below the overall pass rate

Severity definitions are in [`docs/risk_matrix.md`](docs/risk_matrix.md).

## Repository layout

```
agent/        help agent: tool loop and prompts
mock_bank/    mock tools over synthetic customers
scenarios/    customer journeys, tagged by risk tier and segment
configs/      EvalBench run configs
scorers/      compliance checks
judge/        LLM judge rubrics and validation
compliance/   severity gate, segment statistics, A/B testing
dashboard/    compliance dashboard
data/         source list, synthetic data (versioned, hash manifest)
scripts/      data fetchers, synthetic data generator, manifest check
docs/         risk matrix, decision log
```

## Setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/). EvalBench runs need bash (Linux, macOS or WSL).

```bash
uv sync                           # install pinned dependencies
cp .env.example .env              # add API keys (never committed)
uv run python scripts/verify_manifest.py v1   # confirm synthetic data is unmodified
```

To build the agent's knowledge base locally, review the site's terms of use, then run:

```bash
uv run python scripts/fetch_commbank_pages.py
```

Pages are saved to `data/raw/`, which is git-ignored.

## Data

| Source | Use | In repo |
| --- | --- | --- |
| Public bank help pages | Agent knowledge base; source of truth for fee checks | URLs only |
| Synthetic customers and scenarios | Mock bank and test journeys | Yes, versioned with SHA-256 manifest |
| SummEval expert annotations (MIT) | Validating the LLM judge | Download script only |

Full details in [`data/sources.csv`](data/sources.csv). Design choices and the alternatives rejected are recorded in [`docs/decisions.md`](docs/decisions.md).

## Status

In active development. The harness is not yet runnable end to end.

## Licence

[Apache License 2.0](LICENSE).
