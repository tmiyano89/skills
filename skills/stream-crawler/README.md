# stream-crawler

`stream-crawler` is an implementation to fetch pages with infinite scroll or lazy loading in stages, **prioritizing fetch accuracy over speed**.

## Purpose

- Accurately capture content on URLs, including static pages, SPAs, and virtual lists.
- Heavier than `page-streaming`, but with a reproducible fetching strategy.
- Fix default values based on experiment results and keep the implementation small.

## Current Confirmed Policy

- Default viewport height is `5000`
- First, capture the initially displayed content as much as possible without scrolling.
- After that, regardless of the page type, perform sweep scroll, and judge termination based only on the stopping conditions.
- Scroll strategy is `coarse -> fine`
- `coarse_margin_px=300`
- `fine_step_px=100`
- `max_steps_per_page=3`
- `step_wait_ms=300` is not a "fixed wait" but a "growth check interval"
- `probe` is not adopted
- Growth judgment mainly uses `scrollHeight`, and subsidiarily uses `text_len` / `node_count` / `tail_hash`
- Detector provides reference data and is not used for stopping conditions.

`viewportHeight=1000` is used as an audit condition for testing the algorithm.

## Documentation

- [`docs/spec.md`](docs/spec.md): Specification
- [`references/output-format.md`](references/output-format.md): Output format
- [`references/json-format.md`](references/json-format.md): Details of JSON output

## Implementation

- [`scripts/stream_crawler.py`](scripts/stream_crawler.py): Core script
- [`scripts/detect_page_type.py`](scripts/detect_page_type.py): Detector

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Execution Example

```bash
python3 scripts/stream_crawler.py \
  --url "https://example.com/list" \
  --session-dir sessions/example
```
