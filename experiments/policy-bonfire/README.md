# Policy Bonfire Model Sweep Harness

This directory contains the runner/spec files for the AO Radar / Policy Bonfire cheap-model prompt sweep.

## Quick dry run

```bash
python3 experiments/policy-bonfire/run_model_sweep.py --dry-run
```

The dry run does not impersonate the unsafe actor and does not use deterministic villain fallback. It only validates the harness/report pipeline by recording `MODEL_UNAVAILABLE` outcomes.

## Live Ollama Cloud smoke test

Put provider keys in local `.env` only. The repo ignores `.env` files.

Expected local variables:

```bash
OLLAMA_CLOUD_API_KEY_TEST=<local value only>
OPENAI_API_KEY_TEST=<local value only>
GEMINI_API_KEY_TEST=<local value only>
ANTHROPIC_API_KEY_TEST=<local value only>
```

Then run, adjusting model names to whatever Ollama Cloud exposes in the account:

```bash
python3 experiments/policy-bonfire/run_model_sweep.py \
  --model ollama-cloud:qwen3-coder-next \
  --model ollama-cloud:deepseek-v4-flash
```

Outputs:

- public-facing markdown report: `experiments/policy-bonfire/results/model-sweep-results.md`
- raw engineering JSONL: `experiments/policy-bonfire/raw/<sweep-id>.jsonl`

Keep raw outputs private until sanitized.
