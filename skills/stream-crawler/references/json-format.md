# stream-crawler JSON Format

This document illustrates the structure of the JSON files output by `stream-crawler` in a readable format.

## `page_type.json`

```json
{
  "url": "https://example.com/list",
  "content_delivery_type": "hybrid",
  "behaviors": [
    "infinite_scroll"
  ],
  "reasons": [
    "curl/Playwright text amounts are similar",
    "Strong clues for list/feed"
  ],
  "curl": {
    "body_text_len": 5230,
    "html_len": 81422,
    "script_chunk_count": 7
  },
  "playwright": {
    "page_index": 1,
    "text_len": 6412
  }
}
```

Items:

- `url`: Target URL
- `content_delivery_type`: Judgment result of the detector. Ex: `static_or_ssr`, `hybrid`, `spa_csr`
- `behaviors`: Array of auxiliary behavior labels. Ex: `infinite_scroll`, `document_page`
- `reasons`: String array of judgment reasons
- `curl`: Summary of initial HTML seen by `curl`
- `playwright`: Summary of the initial fetch by Playwright

When to use:

- When you want a rough overview of the entire page first
- When you want to check how the detector judged
- When you want to see the difference between `curl` and Playwright

## `page_000N.json`

```json
{
  "page_index": 2,
  "url": "https://example.com/list",
  "captured_at": "2026-03-17T11:20:26+09:00",
  "scroll": {
    "kind": "window",
    "position": 3840,
    "max_position": 7420,
    "client_height": 5000,
    "scroll_height": 12420
  },
  "observation": {
    "text_len": 15230,
    "node_count": 480,
    "tail_hash": "9e3c1d5d0c8d8c6b4f2f8d3b4b0a7f9c1d2e3f4a",
    "tail_text_sample": "..."
  },
  "trigger": {
    "mode": "coarse",
    "step_index": 1,
    "reasons": [
      "scroll_height +1504",
      "text_len +980",
      "node_count +1139",
      "tail_hash changed"
    ],
    "polls": 3
  },
  "snippets": [
    "item 1",
    "item 2"
  ],
  "output_files": {
    "raw_html": "/abs/path/page_0002.html",
    "all_text": "/abs/path/page_0002.txt"
  },
  "has_more_hint": true
}
```

Items:

- `page_index`: Save order number
- `url`: URL at the time of capture
- `captured_at`: ISO 8601 capture time
- `scroll`: Scroll state
  - `kind`: `window` or `element`
  - `position`: Current position
  - `max_position`: Maximum position at that time
  - `client_height`: Viewport or scroller height
  - `scroll_height`: Total height at that time
- `observation`: Observed values
  - `text_len`: Text length
  - `node_count`: Node count
  - `tail_hash`: Hash of the tail text
  - `tail_text_sample`: Sample of the tail text
- `trigger`: Reason this snapshot was saved
  - `mode`: `initial`, `coarse`, `fine`
  - `step_index`: Which sweep step it is
  - `reasons`: Growth judgment reasons
  - `polls`: Number of checks performed until growth stopped
- `snippets`: Beginning excerpts
- `output_files`: Corresponding HTML / TXT paths
- `has_more_hint`: Hint on whether there is likely a next snapshot

When to use:

- When you want to track at what point content growth occurred
- When you want to grasp the overall flow before opening HTML or TXT
- When you want to determine which snapshots to look at in detail
