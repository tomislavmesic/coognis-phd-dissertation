# UEX Domain Taxonomy

This is the initial domain set for expert matching and expert knowledge tagging.

## Domain Codes

- `adaptive-systems`
  - adaptive behavior, personalization, profiling, user-state adjustment
- `expert-guidance`
  - expert follow-up, human review, specialist consultation
- `ml-modeling`
  - machine learning, prediction, modeling, validation, classification
- `ethics-gdpr`
  - privacy, consent, profiling limits, deletion, GDPR handling
- `education-guidance`
  - learner support, course guidance, training, learning pathways

## Recommended Usage

- Every expert should have at least one `expert_domains` record.
- Every expert knowledge item should have exactly one `domain_code`.
- Published knowledge used by UEX should set `status = "published"`.
- Knowledge items should set `source_expert_id` whenever they are expert-authored.

## Bootstrap Script

Use the one-time script at:

- [seed_uex_taxonomy.py](/Users/tomislavm/Projects/PhD/adaptive-expert-system/backend/scripts/seed_uex_taxonomy.py)

Suggested run order:

```bash
cd backend
. .venv/bin/activate
python -m scripts.seed_uex_taxonomy
python -m scripts.seed_uex_taxonomy --apply
```

If you also want starter knowledge for experts who currently have none:

```bash
python -m scripts.seed_uex_taxonomy --apply --seed-knowledge
```

## Importing A Prepared Dataset

If you already prepared a structured dataset JSON, use:

- [import_uex_dataset.py](/Users/tomislavm/Projects/PhD/adaptive-expert-system/backend/scripts/import_uex_dataset.py)

Dry run:

```bash
cd backend
. .venv/bin/activate
python -m scripts.import_uex_dataset --path ../docs/uex-dataset.json
```

Apply:

```bash
python -m scripts.import_uex_dataset --path ../docs/uex-dataset.json --apply
```

If you want the dataset to fully replace existing expert-linked knowledge items for the referenced experts:

```bash
python -m scripts.import_uex_dataset --path ../docs/uex-dataset.json --apply --replace-knowledge
```

What the importer updates:

- experts, matched by email
- expert domains
- expert profiles, using dataset MBTI as manual/effective MBTI
- knowledge items, linked by `source_expert_email`

## What The Script Does

- keeps existing expert-linked knowledge domains if they already exist
- backfills missing `expert_domains`
- infers fallback domains from expert name/email keywords
- falls back to `expert-guidance` if no stronger clue exists
- can optionally create one starter published knowledge item per expert with no knowledge items

## Next UEX Data Priority

After the bootstrap:

1. review seeded domains for each expert
2. replace generic starter knowledge with real expert-authored content
3. ensure future knowledge creation always sets:
   - `domain_code`
   - `source_expert_id`
   - `status`
