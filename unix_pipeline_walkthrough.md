# Unix Pipeline and CLI Tools Walkthrough

This walkthrough demonstrates the Unix philosophy of building data processing pipelines using small, composable command-line tools. You'll learn to chain together tools like `curl`, `jq`, `pup`, `rg`, and `sqlite-utils` to process data efficiently.

## Prerequisites

Install required command-line tools:

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install sqlite-utils (database toolkit)
uvx install sqlite-utils

# Install pup (HTML parser)
brew install pup

# Install jq (JSON processor) - usually pre-installed
which jq
```

## The Unix Philosophy

Unix tools follow these principles:
1. **Do one thing well**: Each tool has a single, focused purpose
2. **Work together**: Tools can be chained via pipes (`|`)
3. **Handle text streams**: Tools read from stdin, write to stdout
4. **Be composable**: Complex tasks built from simple components

## Step 1: Download the Processing Script

Get the HTML menu extraction script:

```bash
curl -o extract_menu_unix.py https://raw.githubusercontent.com/mpr1255/2025s1_mlci/master/week2--scraping_api_cli/mensa_scraping/second_example/extract_menu_unix.py
```

## Step 2: Understanding the Script Structure

The script follows Unix conventions:

```python
#!/usr/bin/env uv run --quiet --script
# /// script
# dependencies = ["beautifulsoup4"]
# ///
```

Key features:
- **Shebang**: Tells system to run with `uv`
- **Inline dependencies**: No separate requirements file needed
- **Stdin/stdout**: Reads file paths from stdin, outputs JSONL to stdout
- **JSONL format**: One JSON object per line (stream-friendly)

## Step 3: Basic Pipeline Operations

### Single File Processing

Process one HTML file:

```bash
echo "path/to/menu.html" | python extract_menu_unix.py
```

### Multiple Files with Find

Find and process all HTML files:

```bash
find data_wget -name "*.html" | python extract_menu_unix.py
```

### Filter with Grep/Ripgrep

Find files containing specific content, then process:

```bash
# Using ripgrep (faster)
rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py

# Using traditional grep
grep -r -l "aw-weekly-menu" data_wget | python extract_menu_unix.py
```

## Step 4: JSON Processing with jq

### Pretty Print JSON

Format output for human reading:

```bash
rg -l "aw-weekly-menu" data_wget | head -1 | python extract_menu_unix.py | jq .
```

### Collect Stream to Array

Convert JSONL (stream) to JSON array:

```bash
rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py | jq -s '.'
```

### Filter and Transform

Extract specific fields:

```bash
# Get only descriptions and prices
rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py | jq '{description, price_students}'

# Filter by city
rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py | jq 'select(.city == "mainz")'
```

## Step 5: Database Integration with sqlite-utils

### Direct Insert from Pipeline

Insert JSONL stream directly into SQLite:

```bash
rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py | sqlite-utils insert menu.db meals -
```

### Insert JSON Array

Convert to array first, then insert:

```bash
rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py | jq -s '.' | sqlite-utils insert menu.db meals -
```

### Query the Database

```bash
# View table schema
sqlite-utils schema menu.db meals

# Query data
sqlite-utils query menu.db "SELECT city, COUNT(*) as meal_count FROM meals GROUP BY city"

# Export to CSV
sqlite-utils query menu.db "SELECT * FROM meals WHERE price_students < 5.0" --csv > cheap_meals.csv
```

## Step 6: Building Complex Pipelines

### Multi-step Processing

```bash
# 1. Find files → 2. Extract data → 3. Filter → 4. Store
rg -l "aw-weekly-menu" data_wget \
  | python extract_menu_unix.py \
  | jq 'select(.price_students != null and .price_students < 10.0)' \
  | sqlite-utils insert menu.db affordable_meals -
```

### Error Handling and Logging

```bash
# Capture errors separately
rg -l "aw-weekly-menu" data_wget \
  | python extract_menu_unix.py 2>errors.log \
  | sqlite-utils insert menu.db meals - \
  && echo "Success: $(wc -l < errors.log) errors logged"
```

### Parallel Processing

```bash
# Process files in parallel (if you have GNU parallel)
rg -l "aw-weekly-menu" data_wget | parallel -j4 "echo {} | python extract_menu_unix.py"
```

## Step 7: Data Validation and Quality Control

### Count Records at Each Step

```bash
# Count files found
echo "Files found: $(rg -l 'aw-weekly-menu' data_wget | wc -l)"

# Count records extracted
echo "Records extracted: $(rg -l 'aw-weekly-menu' data_wget | python extract_menu_unix.py | wc -l)"

# Count records in database
echo "Records in DB: $(sqlite-utils query menu.db 'SELECT COUNT(*) FROM meals' --raw-output)"
```

### Data Quality Checks

```bash
# Check for missing prices
rg -l "aw-weekly-menu" data_wget \
  | python extract_menu_unix.py \
  | jq 'select(.price_students == null)' \
  | wc -l

# Find duplicate meal_ids
sqlite-utils query menu.db "SELECT meal_id, COUNT(*) as count FROM meals GROUP BY meal_id HAVING count > 1"
```

## Step 8: Advanced Pipeline Patterns

### Conditional Processing

```bash
# Process only if output file doesn't exist
[ ! -f menu.db ] && {
  rg -l "aw-weekly-menu" data_wget \
    | python extract_menu_unix.py \
    | sqlite-utils insert menu.db meals -
}
```

### Incremental Updates

```bash
# Find new files (modified in last day)
find data_wget -name "*.html" -mtime -1 \
  | python extract_menu_unix.py \
  | sqlite-utils insert menu.db meals - --replace
```

### Data Transformation Pipeline

```bash
# Complex transformation: normalize prices, add metadata
rg -l "aw-weekly-menu" data_wget \
  | python extract_menu_unix.py \
  | jq '. + {
      price_normalized: (.price_students // 0),
      processed_at: now | strftime("%Y-%m-%d %H:%M:%S"),
      is_affordable: (.price_students // 999) < 5.0
    }' \
  | sqlite-utils insert menu.db enriched_meals -
```

## Step 9: Testing and Debugging

### Test with Limited Data

```bash
# Process only first file
rg -l "aw-weekly-menu" data_wget | head -1 | python extract_menu_unix.py | jq .

# Process first 3 files
rg -l "aw-weekly-menu" data_wget | head -3 | python extract_menu_unix.py | jq -s '.'
```

### Verbose Debugging

```bash
# Add debugging at each step
rg -l "aw-weekly-menu" data_wget | tee found_files.txt \
  | python extract_menu_unix.py | tee extracted_data.jsonl \
  | jq -s '.' | tee final_array.json \
  | sqlite-utils insert menu.db meals -
```

### Performance Monitoring

```bash
# Time the pipeline
time (rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py | sqlite-utils insert menu.db meals -)

# Monitor memory usage
/usr/bin/time -v rg -l "aw-weekly-menu" data_wget | python extract_menu_unix.py | sqlite-utils insert menu.db meals -
```

## Key Learning Points

- **Stream processing**: Unix pipes enable processing large datasets without loading everything into memory
- **Tool composition**: Complex tasks built from simple, focused tools
- **JSONL format**: Stream-friendly alternative to JSON arrays
- **Error handling**: Use stderr for errors, stdout for data
- **Incremental processing**: Build pipelines that can handle updates efficiently
- **Testing**: Always test with small datasets first
- **Debugging**: Use `tee` to capture intermediate results

## Best Practices

1. **Start small**: Test each pipeline step individually
2. **Use standards**: Follow JSON/JSONL conventions for data exchange
3. **Handle errors**: Separate error output from data output
4. **Document data flow**: Comment complex pipelines
5. **Validate data**: Check data quality at each stage
6. **Be efficient**: Use appropriate tools for each task (rg vs grep, jq vs awk)

## Next Steps

- Learn advanced `jq` programming for complex data transformations
- Explore `miller` for CSV/TSV processing
- Study `awk` and `sed` for text processing
- Practice building reusable pipeline components
- Investigate distributed processing with tools like `parallel`