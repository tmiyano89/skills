# stream-crawler Spec

## 1. Purpose

The purpose of `stream-crawler` is to capture the content on a URL as accurately as possible. Speed is a secondary requirement.

The targets are as follows:

- Static pages
- Infinite scroll lists
- Lazy loading lists
- Search results or feeds in SPAs
- List pages containing virtual lists

## 2. Prerequisites

- Use Playwright for browser operations
- Use `detect_page_type.py` for the detector
- Save format is `page_000N.{json,html,txt}`
- Default viewport is `1440x5000`
- `1440x1000` is used as an algorithm validation condition for sweep scroll

## 3. Confirmed Algorithm

### 3.1 Initial Fetch

1. Fetch initial HTML with `curl` and save it to `curl.html`
2. Open the target URL with Playwright
3. Observe the initial state with the large viewport and save `page_0001`
4. Run the detector and save `page_type.json`

If data can be fetched without scrolling, that is the safest approach. However, the detector does not determine "if the initial fetch is sufficient."

### 3.2 Scroll Strategy

1. After the initial fetch, perform a sweep scroll regardless of the page type, and determine whether to continue based on the stopping conditions in 3.3.
2. Select the optimal scroller from `window` / `element`.
3. In `coarse`, move to `300px` before the bottom edge.
4. In `fine`, advance by `100px`.
5. Observe growth at `300ms` intervals after each scroll.
6. End the wait when `scrollHeight`, `text_len`, `node_count`, and `tail_hash` stop changing.
7. If there is growth, save the next snapshot.
8. If there is no growth, proceed to the termination check.

### 3.3 Stopping Conditions

- Maximum of `3` sweeps per page.
- If there is no growth in both `coarse` and `fine`, and the bottom is reached, the page ends.
- If no new snapshots are obtained, terminate the crawl.

### 3.4 Handling of the Detector

- The detector is reference data saved in `page_type.json`.
- The detector's results are not used for stopping conditions.
- For all pages, including `static_or_ssr`, the decision to continue is determined solely by the stopping conditions in 3.3.

## 4. Default Values

| key | value |
|---|---:|
| `viewport_height` | `5000` |
| `max_pages` | `5` |
| `max_steps_per_page` | `3` |
| `coarse_margin_px` | `300` |
| `fine_step_px` | `100` |
| `step_wait_ms` | `300` |
| `settle_timeout_ms` | `2400` |

## 5. Growth Judgment

### Primary Indicator

- Increase in `scrollHeight`

### Auxiliary Indicators

- Increase in `text_len`
- Increase in `node_count`
- Change in `tail_hash`

`scrollHeight` is the primary determinant as it is the simplest and most stable. However, auxiliary indicators are maintained for future compatibility with virtual lists.

## 6. Rejected Proposals

- A proposal to control only with a fixed wait.
- A proposal to have `probe` as an independent phase.
- A proposal to go deep using only fixed steps from the beginning.

`viewportHeight=1000` was not rejected but was adopted only as a validation condition.

## 7. Outputs

- `curl.html`
- `page_type.json`
- `pages/page_000N.html`
- `pages/page_000N.txt`
- `pages/page_000N.json`
- `logs/crawler.log`

## 8. Audit

When operation verification on representative sites is necessary, manually run `stream_crawler.py` and check the following:

- Presence of growth
- The step where growth first occurs
- Reason for growth
- Increment in `scrollHeight`
