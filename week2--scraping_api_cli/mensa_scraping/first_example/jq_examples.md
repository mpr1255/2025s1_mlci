jq examples for the Mensa JSON output

The command `uv run test.py 2025-08-25 --json` prints a JSON array of objects like:

[
  {"date":"2025-08-25","category":"Salatbuffet","description":"...","price":"1,40 €"},
  {"date":"2025-08-25","category":"Themenpark","description":"...","price":"1,40 €"},
  {"date":"2025-08-25","category":"Dessert","description":"...","price":"1,50 €"}
]

Because the top-level value is an array, most queries start with `.[]` (iterate items) or an index like `.[0]`.

Basics
- All items (pretty print):
  - uv run test.py 2025-08-25 --json | jq '.'

- Count items:
  - uv run test.py 2025-08-25 --json | jq 'length'

- First item, whole object:
  - uv run test.py 2025-08-25 --json | jq '.[0]'

- First item’s category:
  - uv run test.py 2025-08-25 --json | jq -r '.[0].category'

Extracting fields
- All dates (one per line):
  - uv run test.py 2025-08-25 --json | jq -r '.[].date'

- All categories (one per line, raw text):
  - uv run test.py 2025-08-25 --json | jq -r '.[].category'

- Unique categories (sorted):
  - uv run test.py 2025-08-25 --json | jq -r '.[].category | ascii_downcase | sort | unique[]'

- Category and price (tab-separated):
  - uv run test.py 2025-08-25 --json | jq -r '.[] | [.category, .price] | @tsv'

Filtering
- Only Dessert rows:
  - uv run test.py 2025-08-25 --json | jq '.[] | select(.category == "Dessert")'

- Categories that contain "salat" (case-insensitive):
  - uv run test.py 2025-08-25 --json | jq '.[] | select(.category | test("salat"; "i"))'

- Rows where the description mentions "broccoli":
  - uv run test.py 2025-08-25 --json | jq '.[] | select(.description | test("broccoli"; "i"))'

Reshaping
- Keep only date, category, price (as objects):
  - uv run test.py 2025-08-25 --json | jq 'map({date, category, price})'

- Convert price to a number (EUR) and keep select fields:
  - uv run test.py 2025-08-25 --json | jq '
      map({
        date,
        category,
        price_eur: (.price | gsub("[^0-9,]"; "") | gsub(","; ".") | tonumber)
      })'

- Turn into simple lines "<date> <category> <price>":
  - uv run test.py 2025-08-25 --json | jq -r '.[] | "\(.date) \(.category) \(.price)"'

Sorting and grouping
- Sort by category:
  - uv run test.py 2025-08-25 --json | jq 'sort_by(.category)'

- Group by category and count items per category:
  - uv run test.py 2025-08-25 --json | jq '
      group_by(.category)
      | map({category: .[0].category, count: length})'

CSV from JSON with jq
- Make a quick CSV (category, price) with header:
  - uv run test.py 2025-08-25 --json | jq -r '
      ("category,price"),
      (.[] | [._category, .price] | @csv)'

- Full CSV matching the script schema (date, category, description, price):
  - uv run test.py 2025-08-25 --json | jq -r '
      ("date,category,description,price"),
      (.[] | [.date, .category, .description, .price] | @csv)'

Tips and common pitfalls
- Use `-r` (raw output) to avoid quoted strings when you expect plain text.
- The input is an array. To get a field from each object, use `.[].field` or `.[] | .field`.
- Examples that failed:
  - `.date` — error: the top-level is an array, not an object.
  - `.[]date` — syntax error. Use `.[].date` or `.[] | .date`.

