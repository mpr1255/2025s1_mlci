# Mensa Menu Scraping Walkthrough

This walkthrough teaches you how to scrape data from web APIs by reverse engineering network requests. You'll learn to inspect browser network traffic, extract API calls, and build your own scraping script.

## Prerequisites

### Install uv (Python package manager)

Make sure you have `uv` installed:

```bash
which uv
```

If not installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install required command-line tools

You'll need `jq` (JSON processor) and `pup` (HTML parser). Check if you have them:

```bash
which jq
which pup
```

**Installation options:**

**On university cluster (Nix):**
```bash
nix profile install nixpkgs#jq
nix profile install nixpkgs#pup
```

**On macOS with Homebrew:**
```bash
brew install jq
brew install pup
```

If you don't have Homebrew, install it from https://brew.sh/

**On Linux (Ubuntu/Debian/WSL):**
```bash
sudo apt update
sudo apt install jq
```

For `pup` on Linux, you'll need to download the binary:
```bash
wget https://github.com/ericchiang/pup/releases/download/v0.4.0/pup_v0.4.0_linux_amd64.zip
unzip pup_v0.4.0_linux_amd64.zip
sudo mv pup /usr/local/bin/
```

> **📚 EXTRA INFO: Understanding PATH**
> 
> Why do we need to move `pup` to `/usr/local/bin/`? It's all about the PATH environment variable!
> 
> ```bash
> echo $PATH
> # Shows something like: /usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
> ```
> 
> When you type a command, Linux searches for executables in each directory listed in `$PATH`, in order:
> 1. `/usr/local/bin/` - locally installed programs (like our `pup`)  
> 2. `/usr/bin/` - system programs
> 3. `/bin/` - essential system programs
> 
> That's why `which pup` fails before moving the file, but works after moving it to `/usr/local/bin/` - because that directory is in your PATH!

## Step 1: Inspect the Target Website

Navigate to the Mensa menu page:

https://www.stw-ma.de/en/food-drink/menus/mensa-am-schloss-en/

1. Open your browser's Developer Tools (F12 or right-click → "Inspect")
2. Go to the **Network** tab
3. Reload the page to capture all network requests
4. Look for requests that might contain the menu data (often JSON or API calls)

## Step 2: Find the API Endpoint

In the Network tab, look for a request that returns the menu data. You should find something like:

- URL: `https://api.stw-ma.de/tl1/menuplan`
- Method: POST
- Contains form data with parameters like date, location, etc.

Right-click on this request and select "Copy as cURL" to get the full command.

## Step 3: Test the Raw cURL Command

The copied cURL command will look something like this (with many headers):

```bash
curl 'https://api.stw-ma.de/tl1/menuplan' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Cookie: [long cookie string]' \
  -H 'Origin: https://www.stw-ma.de' \
  -H 'Referer: https://www.stw-ma.de/en/food-drink/menus/mensa-am-schloss-en/' \
  -H 'User-Agent: [long user agent string]' \
  --data-raw 'id=bc003e93a1e942f45a99dcf8082da289&location=610&lang=en&date=2025-08-27&mode=day'
```

Test this command in your terminal to verify it works.

## Step 4: Simplify the cURL Command

Most headers are unnecessary. Start by reducing it to the essentials:

```bash
curl 'https://api.stw-ma.de/tl1/menuplan' -s \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  --data-raw "id=bc003e93a1e942f45a99dcf8082da289&location=610&lang=en&date=2025-08-27&mode=day"
```

## Step 5: Experiment to Find What's Really Required

**Key lesson**: You can experiment to see what parameters the server actually needs. Try removing parts:

```bash
# Remove the id parameter - what happens?
curl 'https://api.stw-ma.de/tl1/menuplan' -s \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  --data-raw "location=610&lang=en&date=2025-08-27&mode=day"
```

This works fine! Now try removing the Content-Type header:

```bash
# Even simpler - no headers needed
curl 'https://api.stw-ma.de/tl1/menuplan' -s \
  --data-raw "location=610&lang=en&date=2025-08-27&mode=day"
```

This also works! The `-s` flag makes curl silent (no progress bar).

**Learning point**: Many APIs are more forgiving than they appear. Always experiment to find the minimal required parameters.

## Step 6: Examine the Response

Add `| jq .` to format the JSON response nicely:

```bash
curl 'https://api.stw-ma.de/tl1/menuplan' -s \
  --data-raw "location=610&lang=en&date=2025-08-27&mode=day" \
  | jq .
```

You'll see the response contains HTML in a `content` field.

## Step 7: Extract and Parse the HTML

Extract just the HTML content and parse the table:

```bash
curl 'https://api.stw-ma.de/tl1/menuplan' -s \
  --data-raw "location=610&lang=en&date=2025-08-27&mode=day" \
  | jq -r .content \
  | pup 'table.speiseplan-table tr json{}'
```

This uses `pup` (a command-line HTML parser) to extract table rows as JSON.

## Step 8: Download the Python Script

Instead of manually parsing, we'll use a pre-built Python script. Download it using curl:

```bash
curl -o scrape.py https://raw.githubusercontent.com/mpr1255/2025s1_mlci/master/week2--scraping_api_cli/mensa_scraping/first_example/scrape.py
```

**What this does:**
- `curl` downloads the file from the URL
- `-o scrape.py` specifies the output filename ("output to scrape.py")
- Alternative: `-J` flag uses the server's suggested filename, but `-o` gives you explicit control

**Other download options:**
```bash
# Using wget (if available)
wget -O scrape.py https://raw.githubusercontent.com/mpr1255/2025s1_mlci/master/week2--scraping_api_cli/mensa_scraping/first_example/scrape.py

# Let curl auto-detect filename with -J -O
curl -J -O https://raw.githubusercontent.com/mpr1255/2025s1_mlci/master/week2--scraping_api_cli/mensa_scraping/first_example/scrape.py
```

## Step 9: Understand the Python Script

The script (`scrape.py`) does several important things:

1. **Shebang line**: `#!/usr/bin/env -S uv run` - This tells the system to run the script with `uv`
2. **Inline dependencies**: The script declares its Python dependencies inline using PEP 723 format
3. **CLI interface**: Uses `typer` to create a command-line interface
4. **Configurable payload**: The API parameters are stored in a dictionary that you can modify

Key parts of the payload you can modify:
- `date`: Change to any date in YYYY-MM-DD format
- `location`: Different mensa locations have different IDs
- `lang`: Switch between "en" and "de"

## Step 10: Run the Script

**Important**: Don't use system `python`! The script has a shebang line that uses `uv` to create a disposable virtual environment with the right dependencies.

Make the script executable and run it:

```bash
# Make executable
chmod +x scrape.py

# Run with shebang (recommended)
./scrape.py 2025-08-27

# Alternative: explicitly use uv
uv run scrape.py 2025-08-27
```

**Why the `./` is needed**: The dot means "current directory". Without it, the shell looks for `scrape.py` in your PATH directories.

Try different output formats:

```bash
# CSV output (default)
./scrape.py 2025-08-27

# JSON output
./scrape.py 2025-08-27 --json

# Explicit CSV
./scrape.py 2025-08-27 --csv
```

**What happens**: `uv` creates a temporary virtual environment with the script's dependencies (bs4, requests, typer), runs the script, then discards the environment. This gives you Go-like portability for Python scripts!

## Step 11: Build Data Processing Pipelines

You can pipe the output to other tools for further processing. First, make sure you have `sqlite-utils`:

```bash
# Check if sqlite-utils is installed
which sqlite-utils

# If not installed, install it
uv tool install sqlite-utils
```

Now build data pipelines step by step:

### Step 1: First, see what our script outputs

```bash
# Look at the CSV output
./scrape.py 2025-08-27
```

You'll see comma-separated values with headers. Now try JSON:

```bash
# Look at the JSON output  
./scrape.py 2025-08-27 --json
```

Notice how the same data is formatted differently - CSV for spreadsheets/databases, JSON for APIs/web apps.

### Step 2: Compose with sqlite-utils

Now let's pipe that output into a database. Start with CSV:

```bash
# Pipe CSV data into SQLite database
./scrape.py 2025-08-27 | sqlite-utils insert menu.db menu - --csv --pk=date --pk=category
```

**What's happening here:**
- `./scrape.py 2025-08-27` generates CSV data
- `|` pipes it to the next command
- `sqlite-utils insert menu.db menu -` reads from stdin (the `-` means "read from pipe")
- `--csv` tells sqlite-utils the input is CSV format
- `--pk=date --pk=category` sets up composite primary key

Try the same with JSON:

```bash
# Pipe JSON data into SQLite database
./scrape.py 2025-08-28 --json | sqlite-utils insert menu.db menu - --pk=date --pk=category
```

### Step 3: Handle real-world issues

When you try to run the same date twice, you'll get an error:

```bash
# This will fail if run twice!
./scrape.py 2025-08-27 | sqlite-utils insert menu.db menu - --csv --pk=date --pk=category
# Error: UNIQUE constraint failed: menu.date, menu.category
```

**Solution 1: Use `--replace` to update existing records:**

```bash
./scrape.py 2025-08-27 | sqlite-utils insert menu.db menu - --csv --pk=date --pk=category --replace
```

**Solution 2: Use `--ignore` to skip duplicates:**

```bash 
./scrape.py 2025-08-27 | sqlite-utils insert menu.db menu - --csv --pk=date --pk=category --ignore
```

### Step 4: Process multiple dates (the right way)

**❌ Problematic approach** - shell loops can fail partway through:

```bash
# Don't do this - fragile and hard to debug
for date in 2025-08-26 2025-08-29 2025-08-30; do
  ./scrape.py $date | sqlite-utils insert menu.db menu - --csv --pk=date --pk=category
done
```

Problems with this approach:
- If one date fails, the loop stops
- No error handling for missing menu data (some dates might not exist)
- Hard to debug which date caused the failure
- No way to resume from where it left off

**✅ Better approach** - handle each date individually with error handling:

```bash
# Process one date at a time, with error handling
for date in 2025-08-26 2025-08-29 2025-08-30; do
  echo "Processing $date..."
  if ./scrape.py $date | sqlite-utils insert menu.db menu - --csv --pk=date --pk=category --replace; then
    echo "✓ Success: $date"
  else
    echo "✗ Failed: $date"
  fi
done
```

**✅ Best approach** - modify the Python script itself to handle multiple dates:

```bash
# Future improvement: let the Python script handle multiple dates
# ./scrape.py 2025-08-26 2025-08-27 2025-08-28 --output-db menu.db
```

> **💡 Why Python is better for batch processing:**
> - Better error handling and logging
> - Can validate dates before making requests  
> - Can implement retry logic and rate limiting
> - Single transaction for all inserts (atomic)
> - More readable and maintainable code
> - Can handle edge cases (weekends, holidays, etc.)

### Step 5: Query your data

Now query the database you've built:

```bash
# Find all menu items
sqlite-utils query menu.db "SELECT * FROM menu LIMIT 5"

# Search for specific categories
sqlite-utils query menu.db "SELECT * FROM menu WHERE category LIKE '%vegan%'"

# Count items by date
sqlite-utils query menu.db "SELECT date, COUNT(*) as item_count FROM menu GROUP BY date"

# Export back to JSON
sqlite-utils query menu.db "SELECT * FROM menu WHERE price != 'N/A'" --json-cols
```

## Step 12: Experiment and Modify

Try modifying the script:

1. Change the `location` parameter to scrape different mensa locations
2. Modify the parsing logic to extract additional information
3. Add error handling for missing data
4. Create a script that automatically fetches multiple days

## Key Learning Points

- **Network inspection**: Browser dev tools reveal how web applications communicate with servers
- **API reverse engineering**: You can extract API calls from browser traffic
- **cURL simplification**: Most headers are optional; focus on the essential ones
- **Shebang scripts**: Modern Python scripts can declare dependencies inline
- **CLI design**: Tools like `typer` make it easy to create professional command-line interfaces
- **Data pipelines**: Unix philosophy of small, composable tools working together

## Next Steps

- Explore other APIs using similar techniques
- Learn about rate limiting and ethical scraping practices
- Build more sophisticated data processing pipelines
- Investigate authentication and session handling for protected APIs