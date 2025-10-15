# Week 6: From CSV to a Query-Ready Database

## Designing, Loading, and Optimizing Real Parliamentary Speech Data

**Dataset:** [SpeakGer Corpus](https://berd-platform.de/records/g3225-rba63) - 74 years of German parliamentary debates

---

## Learning Objectives

By the end of this workshop, you will be able to:

- Download and inspect CSV data from public APIs using curl and Unix tools
- Design a relational database schema that connects multiple tables
- Explain what primary keys (PK) and foreign keys (FK) do and why they matter
- Load CSV data into SQLite using sqlite-utils
- Verify data integrity and query across related tables
- Create visualizations from database queries using R

---

## 0️⃣ The Big Picture: Why Databases?

You've learned to scrape data, call APIs, and process JSON/HTML. But once you have the data... **then what?**

### The CSV Problem

A CSV file is just text - great for interchange, terrible for analysis:

**Fragility:**
- No schema validation (columns can shift, types can break)
- No relationships (linking speakers to speeches requires manual matching)
- No integrity checks (duplicate records, orphaned data)

**Memory:**
- **This is the killer.** Tools like pandas or R's `read.csv()` load the **entire file into RAM**
- Our full Bremen dataset is 390MB - that's manageable
- But the Bundestag file is **1.8GB**
- Loading 1.8GB into memory on an 8GB laptop? Your computer will **crawl**
- Want to analyze all 16 states? That's **~10GB** - impossible for most laptops

**Databases solve this:**
- **Stream data** - only load what you need, when you need it
- Query 10GB of data while using 50MB of RAM
- **Indexes** make searches 1000x faster (no full scans)
- **Schema** enforces data types and relationships
- **Constraints** prevent bad data from entering
- **Transactions** ensure consistency across multiple tables

Think of it this way: a CSV forces you to load the entire phone book into your brain. A database lets you look up one name at a time.

---

## 1️⃣ Setup & Installation

### Check what you have

```bash
which curl        # Should show /usr/bin/curl (macOS) or similar
which sqlite3     # Should be installed on macOS by default
```

### Install package manager (if needed)

**macOS:** Install Homebrew if you don't have it
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Windows:** Use [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install) or [Git Bash](https://gitforwindows.org/)

**Linux:** You probably already have everything 🎉

### Install uv (modern Python package manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:
```bash
uv --version
```

### Install sqlite-utils via uv

```bash
uv tool install sqlite-utils
```

or just run it 

```bash
uvx sqlite-utils
```

This will download and run `sqlite-utils` automatically in case you don't want to install(??)

### Install TablePlus

Download from [https://tableplus.com/](https://tableplus.com/) (free version works fine)

### Check R installation

```bash
which R
which Rscript
```

If not installed: [https://cloud.r-project.org/](https://cloud.r-project.org/)

---

## 2️⃣ Understanding the Data

### The SpeakGer Corpus Structure

This dataset contains:
- **15+ million speeches** from German parliaments (1949-2025)
- **3 types of files:**
  1. `all_mps_meta.csv` - Fixed metadata about members of parliament (name, birth date, gender, etc.)
  2. `all_mps_mapping.csv` - Time-specific data (party, constituency per period)
  3. `[State].csv` - Individual speeches for each parliament (Bremen, Bayern, Bundestag, etc.)

### The Key Relationship: MPID

All three file types connect via **MPID** (Member of Parliament ID):
- `all_mps_meta.csv` has MPID as **primary key** (unique identifier)
- Speech files reference MPID as **foreign key** (links to a speaker)

---

## 3️⃣ Download & Inspect Data

### Understanding curl flags

Before we download, let's understand the tools:

**curl flags:**
- `-L` = Follow redirects (the API redirects to S3 storage)
- `-o filename` = Save output to a file instead of printing to terminal
- `-s` = Silent mode (don't show progress bars)
- `-J` = Use server-suggested filename from Content-Disposition header
- `-O` = Save with the filename from the URL (capital O!)

**Examples:**
```bash
# Save to specific filename
curl -L -o myfile.csv "https://example.com/data.csv"

# Use server's suggested filename
curl -LOJ "https://example.com/data.csv"

# Silent download (no progress bar)
curl -sL -o data.csv "https://example.com/data.csv"
```

### Download the metadata files (small, ~2MB each)

```bash
# Create a data directory
mkdir -p ~/speakger_data
cd ~/speakger_data

# Download MP metadata (fixed info: name, birth date, etc.)
curl -L -o all_mps_meta.csv \
  "https://berd-platform.de/records/g3225-rba63/files/all_mps_meta.csv?download=1"

# Download MP mapping (time-specific: party, constituency)
curl -L -o all_mps_mapping.csv \
  "https://berd-platform.de/records/g3225-rba63/files/all_mps_mapping.csv?download=1"
```

### Inspect what you downloaded

```bash
# See file sizes
ls -lh

# Count lines (rows)
wc -l all_mps_meta.csv
wc -l all_mps_mapping.csv

# Look at first 5 rows
head -5 all_mps_meta.csv

# Look at column headers only
head -1 all_mps_meta.csv

# Look at last 5 rows
tail -5 all_mps_meta.csv

# Look at last 10 rows without header
tail -10 all_mps_meta.csv

# Skip first line (header) and show next 5 rows
tail -n +2 all_mps_meta.csv | head -5
```

**What you should see:**
```
MPID;WikiDataLink;WikipediaLink;Name;LastName;Born;SexOrGender;Occupation;Religion;AbgeordnetenwatchID
```

**Notice:** This file uses **semicolon** (`;`) as a delimiter, not comma!

**Understanding head and tail:**
- `head -5 file` = first 5 lines
- `head -1 file` = just the first line (header)
- `tail -5 file` = last 5 lines
- `tail -n +2 file` = everything EXCEPT the first line (skip header)
- Combine with pipes: `tail -n +2 file | head -5` = lines 2-6

### Sample a smaller speech dataset (Bremen - one of the smallest states)

Full Bremen file is ~390MB. Let's download just the first 1000 rows for testing.

**🎯 Critical concept: Streaming vs Loading**

**Question:** When you run `curl URL | head -1001`, does curl download the **entire 390MB file** and then head takes the first 1001 lines?

**Answer:** NO! This is the beauty of Unix pipes - they **stream data**.

Here's what actually happens:

1. `curl` starts downloading and sends data to `stdout` (line by line)
2. `head` starts reading from `stdin`
3. After `head` receives 1001 lines, it **closes its input and exits**
4. This sends a `SIGPIPE` signal to `curl`
5. `curl` **stops downloading immediately**

**Result:** You only download ~1001 lines worth of data (~100KB), **not 390MB**!

This is:
- **Why Unix pipes are powerful** - they stream, not load
- **Why databases use similar strategies** - fetch only what you need
- **The opposite of pandas/R** - which load entire files into RAM

```bash
# Get first 1001 lines (1 header + 1000 data rows)
# This only downloads ~100KB, NOT the full 390MB file!
curl -sL "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" \
  | head -1001 > bremen_sample.csv
```

Check what you got:

```bash
wc -l bremen_sample.csv   # Should show 1001

head -3 bremen_sample.csv  # Look at structure

tail -3 bremen_sample.csv  # Look at the end
```

**What you should see:**
```
Period,Session,Date,Chair,Interjection,MPID,Party,Constituency,Speech
7,1,1967-11-08,True,False,0,[],, 35.03 Uhr.
7,1,1967-11-08,True,False,0,[],,Meine Damen und Herren...
```

**Notice:** Bremen uses **comma** (`,`) as delimiter

**Try this yourself (Method 1: watch the file size):**
```bash
# Watch the file size as it downloads (should stop at ~100KB)
curl -L "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" \
  | head -1001 > test_sample.csv &

# In another terminal
watch -n 0.5 'ls -lh test_sample.csv'
```

You'll see the file grow to ~100KB and then **stop** - not 390MB!

**Method 2: tail -f (watch the content as it arrives):**

Just like watching a log file grow in real-time!

```bash
# Terminal 1: Start the download
curl -L "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" \
  | head -1001 > test_sample.csv &

# Terminal 2: Watch the file content appear line-by-line
tail -f test_sample.csv
```

You'll see CSV lines appearing in real-time as they're downloaded! Press `Ctrl+C` when done.

**`tail -f` is CRITICAL for real-world work:**
- Watch server logs: `tail -f /var/log/nginx/access.log`
- Monitor database imports: `tail -f import.log`
- Debug long-running scripts: `tail -f script_output.log`
- Follow application logs: `tail -f app.log | grep ERROR`

**Bonus: Using `tee` for debugging/visibility**

**Question:** What if you want to **see the data** while it's being saved?

That's when `tee` is perfect! The `tee` command (named after a T-junction in plumbing) splits data to multiple destinations:

```bash
# See data scroll by on screen AND save to file
curl -sL "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" \
  | head -1001 \
  | tee test_sample.csv
```

You'll see all 1001 lines in your terminal AND they're saved to the file.

**When you'd use this:**
- **Debugging**: "Is my data getting corrupted in the pipeline?"
- **Verification**: Quick visual check of data format before running overnight on 50gb
- **Save intermediate steps**:
  ```bash
  curl URL | tee raw.csv | grep "SPD" | tee filtered.csv | wc -l
  # Creates: raw.csv (all data) and filtered.csv (just SPD rows)
  # Outputs: count of SPD rows
  ```

**⚠️ Important: Order matters for SIGPIPE!**

```bash
# This works as expected (saves 1001 lines):
curl URL | head -1001 | tee file

# This does NOT work (tee tries to save ALL 390MB!):
curl URL | tee file | head -1001
```

Why? In the second case:
1. `tee` starts writing the FULL stream to file
2. `head` exits after 1001 lines
3. `tee` gets SIGPIPE and stops... but has already written more than 1001 lines!

**Rule:** Put `tee` AFTER the limiting command (`head`), not before.

**When NOT to use `tee`:**
- Just silently saving data → use `> file` (simpler, faster)
- Don't need to see output → use `> file`
- Want clean, quiet scripts → use `> file`

---

## 4️⃣ Design the Database Schema

Before loading data, we need to understand **how tables relate to each other**.

### Use a visual schema designer

Go to **[ERDPlus](https://erdplus.com/)** (free, no login required)

1. Click "Try it now" or go directly to https://erdplus.com/trial
2. Select "Relational Schema" from the diagram types
3. Create three tables and define their relationships:

**Tables to create:**

**mps_meta**
- MPID (integer, PRIMARY KEY)
- WikiDataLink (text)
- WikipediaLink (text)
- Name (text)
- LastName (text)
- Born (date)
- SexOrGender (text)
- Occupation (text)
- Religion (text)
- AbgeordnetenwatchID (integer)

**speeches**
- id (integer, PRIMARY KEY, auto-increment)
- Period (integer)
- Session (integer)
- Date (date)
- Chair (boolean)
- Interjection (boolean)
- MPID (integer, FOREIGN KEY → mps_meta.MPID)
- Party (text)
- Constituency (text)
- Speech (text)

**mps_mapping**
- id (integer, PRIMARY KEY, auto-increment)
- MPID (integer, FOREIGN KEY → mps_meta.MPID)
- Period (integer)
- Parliament (text)
- Party (text)
- Constituency (text)

**Draw the relationships:**
- From `speeches.MPID` to `mps_meta.MPID` (many-to-one)
- From `mps_mapping.MPID` to `mps_meta.MPID` (many-to-one)

**Explore the diagram:**
- See how `MPID` connects all tables
- Each speech links to exactly one MP
- Each MP can have many speeches
- This is a **one-to-many relationship**

**Alternative tools:**
- [DrawSQL](https://drawsql.app/) - requires login but very polished
- [QuickDBD](https://www.quickdatabasediagrams.com/) - text-based, quick
- [Draw.io](https://app.diagrams.net/) - general purpose, supports ER diagrams

**Discussion questions:**
- Why is `MPID` the primary key in `mps_meta` but a foreign key in `speeches`?
- What happens if we try to insert a speech with `MPID=99999` but that MP doesn't exist?
- Should `Party` be in the `speeches` table, or should we always join to `mps_mapping`?
- What if a speaker changes parties mid-term? How does our schema handle that?

---

## 5️⃣ Load Data into SQLite

### The Hard Way: Understanding What Happens Under the Hood

Before we use the convenient tool, let's see **what actually needs to happen** to load a CSV into SQLite.

**Step 1: Create the database file**
```bash
cd ~/speakger_data

# This creates an empty database
sqlite3 speakger.db
```

**Step 2: Create the table with the right schema**

You need to:
1. Figure out the column names from the CSV header
2. Guess the data types (integer? text? date?)
3. Write SQL CREATE TABLE statement
4. Define primary keys

```sql
-- Inside sqlite3 prompt
CREATE TABLE mps_meta (
    MPID INTEGER PRIMARY KEY,
    WikiDataLink TEXT,
    WikipediaLink TEXT,
    Name TEXT,
    LastName TEXT,
    Born TEXT,  -- dates are stored as TEXT in SQLite
    SexOrGender TEXT,
    Occupation TEXT,
    Religion TEXT,
    AbgeordnetenwatchID INTEGER
);
```

**Step 3: Import the CSV**

```sql
-- Set mode to CSV
.mode csv

-- Set delimiter (this file uses semicolon!)
.separator ";"

-- Import (this skips the header automatically)
.import all_mps_meta.csv mps_meta
```

**Step 4: Verify**

```sql
SELECT COUNT(*) FROM mps_meta;
SELECT * FROM mps_meta LIMIT 5;
.quit
```

**Problems with the hard way:**
- ❌ Manual schema creation (error-prone)
- ❌ Have to guess data types
- ❌ No type inference (everything becomes TEXT unless you specify)
- ❌ Have to remember the right delimiter
- ❌ `.import` has quirks (handles quotes weirdly, escape characters)
- ❌ No validation - bad data just gets inserted

**your CSV might have:**
- Commas inside quoted fields
- NULL values represented as empty strings
- Different date formats
- Mixed types in a column

You'd have to **manually clean** the CSV first or write custom SQL.

---

### The Easy Way: sqlite-utils

Now let's see how `sqlite-utils` handles all of this automatically:

```bash
cd ~/speakger_data

# One command does everything!
uvx sqlite-utils insert speakger.db mps_meta all_mps_meta.csv \
  --csv \
  --delimiter=";" \
  --detect-types
```

**What `sqlite-utils` just did for you:**
- ✅ Read the CSV header to get column names
- ✅ **Inferred data types** by sampling the data (MPID is INTEGER, not TEXT)
- ✅ Created the table automatically
- ✅ Set MPID as primary key (because we'll tell it to with `--pk=MPID` next time)
- ✅ Handled the semicolon delimiter
- ✅ Properly escaped quotes, commas, newlines in data
- ✅ Loaded all rows efficiently

Check what you have:

```bash
# List tables
uvx sqlite-utils tables speakger.db

# Show schema (with inferred types!)
uvx sqlite-utils schema speakger.db

# Count rows
uvx sqlite-utils rows speakger.db mps_meta --count
```

**Compare the schemas:**

Hard way:
```sql
CREATE TABLE mps_meta (Born TEXT, ...)  -- everything is TEXT
```

sqlite-utils way:
```sql
CREATE TABLE mps_meta (
    MPID INTEGER,
    Born TEXT,
    AbgeordnetenwatchID INTEGER,  -- correctly inferred!
    ...
)
```

**The magic:** `--detect-types` samples your data and figures out which columns are integers, floats, text, etc.

---

### When to use the hard way

Sometimes you WANT manual control:
- Adding constraints (`NOT NULL`, `CHECK`, `UNIQUE`)
- Creating composite primary keys
- Defining foreign keys with `ON DELETE CASCADE`
- Custom column types or collations

But for 90% of cases? **sqlite-utils** or other wrappers will save you a lot of trouble.

### Load the speeches sample

```bash
uvx sqlite-utils insert speakger.db speeches bremen_sample.csv \
  --csv \
  --detect-types
```

### Verify the load

```bash
# Count rows in each table
uvx sqlite-utils rows speakger.db mps_meta --count
uvx sqlite-utils rows speakger.db speeches --count

# Show first 5 speeches
uvx sqlite-utils rows speakger.db speeches --limit 5 --fmt pretty
```

---

## 6️⃣ Inspect in TablePlus

**Open TablePlus** and:

1. Click "+ Create a new connection"
2. Select **SQLite**
3. Browse to `~/speakger_data/speakger.db`
4. Click "Connect"

**In TablePlus:**
- Click on `mps_meta` table → see all rows
- Click on `speeches` table → see your 1000 sample speeches
- Click the "Structure" tab → see column types and indexes

**Try this:**
- Filter speeches where `Party` contains "SPD"
- Sort by `Date` descending

---

## 7️⃣ Query the Database

### From the command line

Open SQLite directly:

```bash
sqlite3 speakger.db
```

Inside the SQLite prompt:

```sql
-- See all tables
.tables

-- See schema for a table
.schema speeches

-- Pretty output
.mode column
.headers on

-- How many speeches total?
SELECT COUNT(*) FROM speeches;

-- How many speakers?
SELECT COUNT(DISTINCT MPID) FROM speeches;

-- Most common party?
SELECT Party, COUNT(*) as speech_count
FROM speeches
WHERE Party != '[]'
GROUP BY Party
ORDER BY speech_count DESC
LIMIT 10;
```

Exit with `.exit`

### Join speeches to speaker metadata

```sql
sqlite3 speakger.db <<EOF
SELECT
  m.Name,
  m.SexOrGender,
  COUNT(*) as num_speeches
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.MPID > 0
GROUP BY m.Name, m.SexOrGender
ORDER BY num_speeches DESC
LIMIT 10;
EOF
```

**This shows:**
- Top 10 speakers by number of speeches
- Their gender
- Requires a **JOIN** across two tables using `MPID`

---

## 8️⃣ Handle Broken Data (When Things Go Wrong)

### What if we try to add a speech with an invalid MPID?

First, let's add a **foreign key constraint** to enforce data integrity:

```bash
# Recreate database with constraints
rm speakger.db

uvx sqlite-utils insert speakger.db mps_meta all_mps_meta.csv \
  --csv \
  --delimiter=";" \
  --detect-types \
  --pk=MPID
```

Now add speeches with foreign key:

```bash
# First, create the speeches table manually with FK
sqlite3 speakger.db <<EOF
CREATE TABLE speeches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  Period INTEGER,
  Session INTEGER,
  Date TEXT,
  Chair BOOLEAN,
  Interjection BOOLEAN,
  MPID INTEGER,
  Party TEXT,
  Constituency TEXT,
  Speech TEXT,
  FOREIGN KEY (MPID) REFERENCES mps_meta(MPID)
);
EOF
```

Now load data:

```bash
# This might fail for rows where MPID doesn't exist!
uvx sqlite-utils insert speakger.db speeches bremen_sample.csv \
  --csv \
  --detect-types
```

**sqlite-utils makes this easy** - it handles missing FKs gracefully. But in production, you'd want to:
1. Clean data first
2. Set MPID=0 or NULL for unknown speakers
3. Log errors for manual review

---

## 9️⃣ Optimize with Indexes

**Why index?** Imagine searching for a word in a book with no table of contents. You'd read every page!

Indexes are like a table of contents for your database.

```bash
sqlite3 speakger.db <<EOF
-- Create index on MPID for faster joins
CREATE INDEX idx_speeches_mpid ON speeches(MPID);

-- Create index on Party for faster filtering
CREATE INDEX idx_speeches_party ON speeches(Party);

-- Create index on Date for faster time-based queries
CREATE INDEX idx_speeches_date ON speeches(Date);
EOF
```

**Test the difference:**

```sql
-- Before index: full table scan
EXPLAIN QUERY PLAN
SELECT * FROM speeches WHERE MPID = 12345;

-- After index: uses index (much faster!)
EXPLAIN QUERY PLAN
SELECT * FROM speeches WHERE MPID = 12345;
```

Look for "SEARCH TABLE speeches USING INDEX" - that's good!

---

## 🔟 Visualize with R

Let's create a histogram showing **number of speeches per year**.

Create `visualize.R`:

```r
#!/usr/bin/env Rscript

# Install packages if needed
if (!require("DBI")) install.packages("DBI", repos="https://cloud.r-project.org")
if (!require("RSQLite")) install.packages("RSQLite", repos="https://cloud.r-project.org")
if (!require("ggplot2")) install.packages("ggplot2", repos="https://cloud.r-project.org")

library(DBI)
library(RSQLite)
library(ggplot2)

# Connect to database
con <- dbConnect(RSQLite::SQLite(), "speakger.db")

# Query: count speeches per year
query <- "
SELECT
  strftime('%Y', Date) as year,
  COUNT(*) as num_speeches
FROM speeches
WHERE Date IS NOT NULL
GROUP BY year
ORDER BY year
"

df <- dbGetQuery(con, query)
dbDisconnect(con)

# Convert year to numeric
df$year <- as.numeric(df$year)

# Create histogram
p <- ggplot(df, aes(x=year, y=num_speeches)) +
  geom_col(fill="steelblue") +
  labs(
    title="Bremen Parliamentary Speeches Over Time",
    subtitle="Sample of 1000 speeches from SpeakGer corpus",
    x="Year",
    y="Number of Speeches"
  ) +
  theme_minimal()

# Save plot
ggsave("speeches_histogram.png", p, width=10, height=6, dpi=300)

cat("Plot saved to speeches_histogram.png\n")
```

Make it executable and run:

```bash
chmod +x visualize.R
./visualize.R
```

Open `speeches_histogram.png` to see your visualization!

---

## 1️⃣1️⃣ Complete Pipeline: Download → Load → Query → Visualize

Here's the full pipeline in one script:

Create `pipeline.sh`:

```bash
#!/bin/bash

set -e  # Exit on error

echo "📥 Downloading data..."
mkdir -p data
cd data

curl -sL -o all_mps_meta.csv \
  "https://berd-platform.de/records/g3225-rba63/files/all_mps_meta.csv?download=1"

curl -sL "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" \
  | head -1001 > bremen_sample.csv

echo "✅ Downloaded $(wc -l < all_mps_meta.csv) MPs and $(wc -l < bremen_sample.csv) speeches"

echo "🗄️  Creating database..."
rm -f speakger.db

uvx sqlite-utils insert speakger.db mps_meta all_mps_meta.csv \
  --csv --delimiter=";" --detect-types --pk=MPID

uvx sqlite-utils insert speakger.db speeches bremen_sample.csv \
  --csv --detect-types

echo "📊 Database created with:"
uvx sqlite-utils tables speakger.db --counts

echo "🔍 Creating indexes..."
sqlite3 speakger.db <<EOF
CREATE INDEX IF NOT EXISTS idx_speeches_mpid ON speeches(MPID);
CREATE INDEX IF NOT EXISTS idx_speeches_date ON speeches(Date);
EOF

echo "📈 Running visualization..."
cd ..
Rscript visualize.R

echo "✨ Done! Check speeches_histogram.png"
```

Run the whole pipeline:

```bash
chmod +x pipeline.sh
./pipeline.sh
```

---

## 1️⃣2️⃣ Advanced Queries

### Find most polarizing topics (mentioned by multiple parties)

```sql
SELECT
  substr(Speech, 1, 100) as snippet,
  COUNT(DISTINCT Party) as num_parties,
  COUNT(*) as mentions
FROM speeches
WHERE Speech LIKE '%Migration%' OR Speech LIKE '%Asyl%'
GROUP BY substr(Speech, 1, 100)
HAVING num_parties > 1
ORDER BY num_parties DESC, mentions DESC
LIMIT 10;
```

### Gender breakdown by party

```sql
SELECT
  s.Party,
  m.SexOrGender,
  COUNT(*) as num_speeches
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.Party != '[]' AND m.SexOrGender IS NOT NULL
GROUP BY s.Party, m.SexOrGender
ORDER BY s.Party, num_speeches DESC;
```

### Longest speeches

```sql
SELECT
  m.Name,
  s.Date,
  LENGTH(s.Speech) as speech_length,
  substr(s.Speech, 1, 200) as preview
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
ORDER BY speech_length DESC
LIMIT 10;
```

---

## 1️⃣3️⃣ Scale Up: Load Full Dataset

Ready to work with the real data? Download a full state:

```bash
# Saarland is one of the smallest (~337MB)
curl -L -o Saarland.csv \
  "https://berd-platform.de/records/g3225-rba63/files/Saarland.csv?download=1"

# Load it (this will take a few minutes)
uvx sqlite-utils insert speakger.db speeches_saarland Saarland.csv \
  --csv --detect-types

# Create indexes
sqlite3 speakger.db <<EOF
CREATE INDEX idx_saarland_mpid ON speeches_saarland(MPID);
CREATE INDEX idx_saarland_date ON speeches_saarland(Date);
CREATE INDEX idx_saarland_party ON speeches_saarland(Party);
EOF
```

For the **full Bundestag** (~1.8GB), you'll want a machine with at least 4GB RAM and SSD storage.

---

### 🪵 Bonus: Logging Long-Running Operations

When loading large datasets, you want to **log progress** and monitor it in real-time. This is standard practice in data engineering.

**Create a logging import script** (`load_with_logging.sh`):

```bash
#!/bin/bash

set -e

LOG_FILE="import.log"
DB_FILE="speakger.db"
DATA_FILE="Saarland.csv"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================="
echo "Database Import Started: $(date)"
echo "========================================="
echo ""

echo "📊 File stats:"
ls -lh "$DATA_FILE"
echo "Rows to import: $(wc -l < "$DATA_FILE")"
echo ""

echo "🗄️  Starting database load..."
echo "Start time: $(date +%H:%M:%S)"

# Load data (this streams output to both terminal and log file)
uvx sqlite-utils insert "$DB_FILE" speeches_saarland "$DATA_FILE" \
  --csv --detect-types

echo "End time: $(date +%H:%M:%S)"
echo ""

echo "📈 Creating indexes..."
sqlite3 "$DB_FILE" <<EOF
CREATE INDEX IF NOT EXISTS idx_saarland_mpid ON speeches_saarland(MPID);
CREATE INDEX IF NOT EXISTS idx_saarland_date ON speeches_saarland(Date);
CREATE INDEX IF NOT EXISTS idx_saarland_party ON speeches_saarland(Party);
EOF

echo ""
echo "✅ Import complete!"
echo ""

echo "📊 Final database stats:"
sqlite3 "$DB_FILE" "SELECT COUNT(*) as total_rows FROM speeches_saarland"
ls -lh "$DB_FILE"

echo ""
echo "========================================="
echo "Database Import Finished: $(date)"
echo "========================================="
```

**Run it and watch logs in real-time:**

```bash
# Terminal 1: Run the import
chmod +x load_with_logging.sh
./load_with_logging.sh

# Terminal 2: Watch the log file update live (like watching server logs!)
tail -f import.log
```

You'll see lines appear in real-time as the import progresses!

**Why this matters:**

```bash
# This is how you'd monitor production processes:

# Watch a web server log
tail -f /var/log/nginx/access.log | grep "POST"

# Monitor database imports
tail -f import.log | grep "ERROR"

# Follow application logs with filtering
tail -f app.log | grep -E "(ERROR|WARN)"

# Watch multiple logs at once
tail -f *.log

# Follow with line numbers and colored output
tail -f import.log | nl
```

**The magic:**
- `exec > >(tee -a "$LOG_FILE") 2>&1` redirects ALL output to both terminal AND log file
- `tail -f` reads the file and **keeps watching** for new lines (unlike regular `tail`)
- Press `Ctrl+C` to stop watching (doesn't stop the original process)
- The log file persists - you can review it later with `less import.log`

**Real-world use cases:**
- Monitor long-running data imports (what we just did!)
- Debug cron jobs (redirect output to log, `tail -f` to watch)
- Track batch processing scripts
- Monitor machine learning training runs
- Watch API call logs during development

This is **essential** for production data pipelines!

---

## 1️⃣4️⃣ Discussion & Reflection

**Think about:**

1. **Schema Design**
   - Why normalize into separate tables vs. one wide table?
   - When would denormalization make sense?
   - What's the tradeoff between storage and query speed?

2. **Data Integrity**
   - What happens if MPID=0 or MPID is missing?
   - Should we enforce `NOT NULL` constraints?
   - How do we handle speakers who change parties?

3. **Indexing**
   - Which columns should be indexed?
   - What's the cost of indexes? (Hint: slower writes, more storage)
   - How do you decide?

4. **Query Optimization**
   - Use `EXPLAIN QUERY PLAN` to see how SQLite executes queries
   - Look for "SCAN TABLE" (slow) vs. "SEARCH TABLE USING INDEX" (fast)
   - Benchmark with `.timer on` in sqlite3

5. **Real-World Extensions**
   - How would you add time-series updates (new speeches each month)?
   - How would you handle corrections to old data?
   - How would you version the database schema?

---

## 1️⃣5️⃣ Deliverables

For this workshop, you should have:

1. ✅ A working `speakger.db` with at least the sample data loaded
2. ✅ At least 3 SQL queries that join across tables
3. ✅ An R script that queries the database and produces a visualization
4. ✅ A `pipeline.sh` script that automates download → load → query
5. ✅ Screenshots from TablePlus showing your schema and sample data

**Bonus challenges:**

- Load 2-3 state parliaments and compare speech patterns across regions
- Create a word frequency analysis (most common words by party)
- Build a simple web dashboard using Streamlit + SQLite
- Write a Python script that alerts you when new data is available

---

## 1️⃣6️⃣ Resources

### Documentation
- [SQLite Tutorial](https://www.sqlitetutorial.net/)
- [sqlite-utils docs](https://sqlite-utils.datasette.io/)
- [dbdiagram.io syntax](https://dbdiagram.io/docs)
- [R + SQLite guide](https://solutions.posit.co/connections/db/r-packages/dbi/)

### Tools
- [TablePlus](https://tableplus.com/)
- [DB Browser for SQLite](https://sqlitebrowser.org/) (free alternative)
- [Datasette](https://datasette.io/) (explore SQLite databases in a web UI)

### Books
- *SQL for Data Scientists* by Renée M. P. Teate
- *Use the Index, Luke* (free) - [https://use-the-index-luke.com/](https://use-the-index-luke.com/)

---

## ✅ Recap

| Concept | You Can Now... |
|---------|----------------|
| **Data ingestion** | Download CSV from APIs, inspect with Unix tools |
| **Schema design** | Model relationships, PKs, FKs |
| **Database creation** | Load CSV into SQLite with correct types |
| **Querying** | Write JOINs, filters, aggregates |
| **Optimization** | Add indexes, explain query plans |
| **Visualization** | Connect R to SQLite, create plots |
| **Automation** | Build reproducible pipelines |

**Next session:** We'll connect this database to a live Streamlit dashboard where users can explore speeches interactively!

---

## 📝 Core Pipeline (for reference)

Copy and paste this entire block into your terminal to run the complete pipeline:

```bash
# Setup
mkdir -p speakger_quick && cd speakger_quick

# Download data
echo "Downloading data..."
curl -sL -o all_mps_meta.csv \
  "https://berd-platform.de/records/g3225-rba63/files/all_mps_meta.csv?download=1"
curl -sL "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" \
  | head -1001 > bremen_sample.csv

# Load into database
echo "Creating database..."
uvx sqlite-utils insert speakger.db mps_meta all_mps_meta.csv \
  --csv --delimiter=";" --detect-types --pk=MPID
uvx sqlite-utils insert speakger.db speeches bremen_sample.csv \
  --csv --detect-types

# Create indexes
sqlite3 speakger.db <<EOF
CREATE INDEX idx_speeches_mpid ON speeches(MPID);
CREATE INDEX idx_speeches_date ON speeches(Date);
EOF

# Quick query
echo "Top speakers:"
sqlite3 speakger.db "SELECT m.Name, COUNT(*) as speeches
FROM speeches s JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.MPID > 0 GROUP BY m.Name ORDER BY speeches DESC LIMIT 5"

# Create visualization
cat > viz.R <<'RSCRIPT'
library(DBI); library(RSQLite); library(ggplot2)
con <- dbConnect(SQLite(), "speakger.db")

# Top speakers by gender
df <- dbGetQuery(con, "
  SELECT m.Name, m.SexOrGender as Gender, COUNT(*) as speeches
  FROM speeches s JOIN mps_meta m ON s.MPID = m.MPID
  WHERE s.MPID > 0 AND m.SexOrGender IS NOT NULL
  GROUP BY m.Name, m.SexOrGender
  ORDER BY speeches DESC LIMIT 15
")
dbDisconnect(con)

ggplot(df, aes(x=reorder(Name, speeches), y=speeches, fill=Gender)) +
  geom_col() + coord_flip() +
  scale_fill_manual(values=c("male"="#4A90E2", "female"="#E24A90")) +
  labs(title="Top 15 Speakers in Bremen Parliament",
       subtitle="Colored by gender",
       x=NULL, y="Number of Speeches") +
  theme_minimal() + theme(legend.position="top")
ggsave("speeches.png", width=10, height=7)
cat("Saved speeches.png\n")
RSCRIPT

Rscript viz.R
echo "Done! Check speeches.png"
```

---

