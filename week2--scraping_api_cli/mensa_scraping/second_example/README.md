# Mensa Plan Scraper

Web scraper for mensaplan.de that downloads HTML files and parses them into a SQLite database.

## Scripts

- **`scrape.py`** - Downloads HTML files from mensaplan.de using crawlee
- **`parse.py`** - Parses saved HTML files into SQLite database
- **Alternative: Use `wget` for bulk downloading** (see below)

## Usage

### Option 1: Python Scraper (crawlee)
```bash
# Scrape with limit for testing
./scrape.py --limit 10

# Scrape with overwrite enabled
./scrape.py --overwrite

# Parse HTML files to database
./parse.py

# Parse to custom database
./parse.py --db-path custom.db
```

### Option 2: wget Bulk Download (Recommended)

**Successful wget command:**
```bash
wget --recursive --no-parent --level=5 \
     --reject="*.css,*.js,*.png,*.jpg,*.ico,*.xml,*.rss" \
     --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
     --wait=0.3 \
     --directory-prefix=data_wget \
     --execute robots=off \
     --no-verbose \
     https://www.mensaplan.de/
```

**Key parameters:**
- `--level=5`: Deep enough to reach nested mensa pages (critical!)
- `--execute robots=off`: Ignore robots.txt restrictions  
- `--reject=...`: Skip asset files to save bandwidth
- `--wait=0.3`: Rate limiting to be respectful

### Option 3: wget2 (Experimental)

If you have wget2 installed, it may be faster due to HTTP/2 and better multithreading:

```bash
# Install wget2 first (not available by default)
# On macOS: brew install wget2
# On Ubuntu: apt install wget2

wget2 --recursive --no-parent --level=5 \
      --reject="*.css,*.js,*.png,*.jpg,*.ico,*.xml,*.rss" \
      --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
      --wait=0.3 \
      --directory-prefix=data_wget2 \
      --robots=off \
      --quiet \
      https://www.mensaplan.de/
```

**wget2 advantages:**
- HTTP/2 support for faster downloads
- Better multithreading 
- Improved HTML parsing
- Modern compression support (brotli, zstd)

## File Structure

Downloaded files are organized as:
```
data/
├── {city}/
│   ├── {university}/
│   │   ├── {mensa}/
│   │   │   └── {YYYY-MM-DD}.html
```

For cities without universities, the city name is used as the university folder.

## Database Schema

```sql
-- Mensa information
CREATE TABLE mensas (
    id INTEGER PRIMARY KEY,
    city TEXT NOT NULL,
    university TEXT,
    mensa_name TEXT NOT NULL,
    scraped_date DATE NOT NULL,
    UNIQUE(city, university, mensa_name, scraped_date)
);

-- Menu items with source traceability
CREATE TABLE menu_items (
    id INTEGER PRIMARY KEY,
    mensa_id INTEGER NOT NULL,
    date DATE NOT NULL,
    category TEXT NOT NULL,  -- e.g., 'Hauptgerichte', 'Beilage'
    item_name TEXT NOT NULL,
    price_students REAL,     -- Price for students
    price_staff REAL,        -- Price for staff
    meal_id TEXT,            -- HTML meal ID if available
    source_html_file TEXT,   -- Full path to source HTML file
    FOREIGN KEY (mensa_id) REFERENCES mensas(id)
);
```

## Post-Processing wget Downloads

After wget download, filter for pages with actual menu data:

```bash
# Find HTML files with weekly menu tables
find data_wget -name "*.html" -exec grep -l "aw-weekly-menu" {} \;

# Count files with menus
find data_wget -name "*.html" -exec grep -l "aw-weekly-menu" {} \; | wc -l

# Remove files without menus (optional)
find data_wget -name "*.html" ! -exec grep -q "aw-weekly-menu" {} \; -delete
```

## Requirements

- Python 3.12+
- uv package manager
- Dependencies managed via uv (see script headers)

## Weekly wget Strategy

For weekly automated scraping, you have two approaches:

### Option A: Timestamped Downloads (Recommended)
```bash
# Create timestamped directory for each run
DATE=$(date +%Y-%m-%d)
wget --recursive --no-parent --level=5 \
     --reject="*.css,*.js,*.png,*.jpg,*.ico,*.xml,*.rss" \
     --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
     --wait=0.3 \
     --directory-prefix=data_${DATE} \
     --execute robots=off \
     --no-verbose \
     https://www.mensaplan.de/
```

**Pros:** 
- Historical data preservation
- Easy to compare changes over time
- No risk of data loss

**Cons:** 
- More storage space
- Need deduplication during database parsing

### Option B: Smart Conditional Download
```bash
# Only download if no data from this week exists
WEEK_START=$(date -d "monday" +%Y-%m-%d 2>/dev/null || date -v-monday +%Y-%m-%d)
if [ ! -d "data_week_${WEEK_START}" ]; then
    wget --recursive --no-parent --level=5 \
         --reject="*.css,*.js,*.png,*.jpg,*.ico,*.xml,*.rss" \
         --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
         --wait=0.3 \
         --directory-prefix=data_week_${WEEK_START} \
         --execute robots=off \
         --no-verbose \
         https://www.mensaplan.de/
fi
```

**Recommended:** Use Option A with timestamped downloads, then handle deduplication in `parse.py` using the database's `UNIQUE` constraint on `(city, university, mensa_name, scraped_date)`.

## General wget Rules for Page Structure Targeting

1. **Level Depth**: Use `--level=N` where N is deep enough to reach your target pages:
   - Level 1: `domain.com/page.html`  
   - Level 2: `domain.com/category/page.html`
   - Level 5: `domain.com/city/university/mensa/page.html`

2. **Content-Based Filtering**: Post-process to find pages with specific content:
   ```bash
   # Find pages containing specific HTML elements
   find data_wget -name "*.html" -exec grep -l "aw-weekly-menu" {} \;
   
   # Target pages with specific CSS classes
   find data_wget -name "*.html" -exec grep -l "class=\"menu-item\"" {} \;
   ```

3. **Path-Based Filtering**: Use directory structure patterns:
   ```bash
   # Find all mensa detail pages (not city index pages)
   find data_wget -path "*/mensa-*/*.html"
   
   # Exclude index pages, keep detail pages
   find data_wget -name "*.html" ! -name "index.html" -path "*/mensa-*/*"
   ```

4. **Size-Based Filtering**: Menu pages are typically larger:
   ```bash
   # Find HTML files larger than 10KB (likely contain menu data)
   find data_wget -name "*.html" -size +10k
   ```

## Unix Composable Data Pipeline

For demonstrating Unix composability principles, use this pipeline approach:

### Prerequisites
```bash
# Install required tools
uv tool install sqlite-utils  # or: pipx install sqlite-utils
brew install pup               # HTML parser with CSS selectors
```

### Single File Testing
```bash
# Test extraction on one file
rg -l "aw-weekly-menu" data_wget | head -1 | uv run extract_menu_unix.py

# Test full pipeline with one file  
rg -l "aw-weekly-menu" data_wget | head -1 | uv run extract_menu_unix.py | jq -s '.' | sqlite-utils insert test.db meals -
```

### Full Data Processing Pipeline
```bash
# Process all menu files into SQLite database
rg -l "aw-weekly-menu" data_wget | uv run extract_menu_unix.py | jq -s '.' | sqlite-utils insert menu_data.db meals -

# Query the results
sqlite-utils query menu_data.db "
  SELECT 
    city, 
    COUNT(*) as meal_count,
    AVG(price_students) as avg_price 
  FROM meals 
  GROUP BY city 
  ORDER BY meal_count DESC
"
```

### Pipeline Component Breakdown

1. **`rg -l "aw-weekly-menu" data_wget`** - Find HTML files containing menu data
2. **`uv run extract_menu_unix.py`** - Extract structured data as JSONL (uses pup internally)
3. **`jq -s '.'`** - Convert JSONL to JSON array for sqlite-utils
4. **`sqlite-utils insert menu_data.db meals -`** - Efficiently insert into SQLite

### Advanced Pipeline Options

```bash
# Process specific cities only
rg -l "aw-weekly-menu" data_wget | rg "mainz|berlin" | uv run extract_menu_unix.py | jq -s '.' | sqlite-utils insert city_subset.db meals -

# Real-time processing with xargs parallel processing
rg -l "aw-weekly-menu" data_wget | xargs -P 4 -I {} sh -c 'echo {} | uv run extract_menu_unix.py' | jq -s '.' | sqlite-utils insert parallel.db meals -

# Add data with upsert to handle duplicates
rg -l "aw-weekly-menu" data_wget | uv run extract_menu_unix.py | jq -s '.' | sqlite-utils upsert menu_data.db meals - --pk=meal_id
```

This approach demonstrates Unix philosophy:
- **Small focused tools** (`rg`, `jq`, `sqlite-utils`, custom script)
- **Composability** via pipes
- **Text-based interfaces** (JSONL)
- **Testability** (single file → subset → full dataset)

## Notes

- The `--overwrite` flag controls whether to skip existing files for today's date
- The `source_html_file` column in the database allows easy verification of parsing accuracy
- Rate limiting (`--wait`) is important to be respectful to the server
- `--level=5` is needed because some cities have deeply nested mensa pages
- Deduplication should happen at the database level, not file level, for data integrity
- **Always use `uv run` instead of raw `python3`** for inline dependencies