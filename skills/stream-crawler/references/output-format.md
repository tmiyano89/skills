# stream-crawler Output Format

## Report for Users

- Do not output the internal command sequences used for execution as they are.
- First, concisely report "how much was captured" and "whether there were problems along the way".
- If there are missing or defective parts, clearly state them as they are without supplementing.

## Contents to Return

1. Execution result
2. Target URL and page type judgment
3. Number of captured pages and termination reason
4. List of output files
5. Details of any problems, if they occurred

## Generated Files

| Type | Path Example | Description |
|------|--------|------|
| Initial HTML | `sessions/<name>/curl.html` | Initial HTML fetched by curl for the detector |
| Page Type | `sessions/<name>/page_type.json` | `content_delivery_type` and auxiliary attributes |
| Meta Information | `sessions/<name>/pages/page_0001.json` | Observed values, trigger, and output files of each snapshot |
| Full HTML | `sessions/<name>/pages/page_0001.html` | Main content HTML at that time |
| Full Text | `sessions/<name>/pages/page_0001.txt` | Main content text at that time |
| Logs | `sessions/<name>/logs/crawler.log` | Logs of coarse/fine sweeps and termination reasons |

## Main Items of `page_000N.json`

- `page_index`: Ordered page number
- `url`: URL at the time of capture
- `scroll`: Target scroll type, position, max position, scrollHeight
- `observation`: Observed values such as `text_len`, `node_count`, `tail_hash`
- `trigger`: Tells if it was saved by `initial`, `coarse`, or `fine`
- `snippets`: Excerpts from the beginning
- `output_files`: Actual paths of the HTML / text files
- `has_more_hint`: Hint on whether there is likely a next page
