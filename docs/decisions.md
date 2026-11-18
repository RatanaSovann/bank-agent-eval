# Decision log

Format: **Decision** · alternative rejected · reason. One entry per choice.

| Date | Decision | Alternative rejected | Reason |
| --- | --- | --- | --- |
| 2026-11-16 | Build on EvalBench for orchestration, simulated user and reporting | Writing a harness from scratch | Reuse proven plumbing; spend the time on the bank-specific compliance layer it lacks |
| 2026-11-16 | Small, low-cost model as the agent under test | A frontier model | Fails more, so the eval has something to find; mirrors cost-driven bank choices; sets up a cost vs safety A/B |
| 2026-11-16 | Defer prediction-powered inference to future work | Using PPI in the demo | At ~200 scenarios with one labeller, direct validation is cheaper and clearer; PPI pays off at production volume |
| 2026-11-16 | Prove judge trust on SummEval expert labels plus a written labelling protocol | Hand-labelling bank outputs as a non-expert | Labels should come from qualified people; the method is shown where expert truth exists |
| 2026-11-16 | Synthetic data v1 written from versioned prompts, with a hash manifest | Untracked hand-written test cases | Every scenario traces back to the prompt that made it; edits create new versions |
| 2026-11-18 | Code lives on the Windows drive, with Python run by Windows `uv`; WSL is used only for EvalBench's bash `run.sh` | Moving the whole repo into the WSL filesystem | Claude Code and the editor run on Windows; one `.venv` avoids clashes between two Pythons; EvalBench is the only bash dependency |
| 2026-11-18 | `.gitattributes` forces LF line endings | Git's Windows default (CRLF on checkout) | CRLF changes file bytes, so the synthetic-data hash manifest would fail and bash scripts would break in WSL |
| 2026-11-18 | Dependencies pinned with `uv` (`pyproject.toml` + `uv.lock`) | `pip` + `requirements.txt` | One lock file gives the same versions on every machine and in CI; that is part of the audit trail |
