# Evaluation Harness

This project includes a lightweight benchmark runner for the current MIND routing stack:

- SYNAPSE profiling signal
- UEX domain and knowledge retrieval
- ULM retrieval and optional grounding
- PAGE final answer composition

The harness runs directly against the current database content and local model configuration.

## Files

- benchmark cases: [evaluation-benchmark.json](/Users/tomislavm/Projects/PhD/adaptive-expert-system/docs/evaluation-benchmark.json)
- runner: [evaluate_mind_pipeline.py](/Users/tomislavm/Projects/PhD/adaptive-expert-system/backend/scripts/evaluate_mind_pipeline.py)

## Run

Fast mock PAGE/ULM mode:

```bash
cd backend
. .venv/bin/activate
python -m scripts.evaluate_mind_pipeline --path ../docs/evaluation-benchmark.json
```

Configured local llama mode:

```bash
python -m scripts.evaluate_mind_pipeline --path ../docs/evaluation-benchmark.json --llm-backend configured
```

JSON output:

```bash
python -m scripts.evaluate_mind_pipeline --json
```

Save a timestamped run artifact:

```bash
python -m scripts.evaluate_mind_pipeline --path ../docs/evaluation-benchmark.json --save
```

Save to a custom directory:

```bash
python -m scripts.evaluate_mind_pipeline --path ../docs/evaluation-benchmark.json --save --output-dir ../docs/evaluation-results
```

## What it checks

Each benchmark case can assert:

- expected domain codes
- minimum or maximum number of UEX items
- maximum number of ULM chunks
- whether expert suggestion should exist
- response text fragments that should appear
- response text fragments that must not appear

This is intended as a lightweight tuning loop, not a full automated quality judge.

## Saved results

When `--save` is used, the runner stores a timestamped JSON artifact containing:

- benchmark path
- LLM backend used
- case limit
- pass/fail totals
- full per-case results

Default output directory:

- [evaluation-results](/Users/tomislavm/Projects/PhD/adaptive-expert-system/docs/evaluation-results)
