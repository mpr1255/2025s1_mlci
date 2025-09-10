# Unix Command-Line Data Processing Pipeline

**Learning Objectives:** Master Unix pipelines, command composition, and high-performance text processing through a real-world chess data analysis example.

## Getting the Data

We'll download chess game data in PGN (Portable Game Notation) format:

```bash
# Create a directory called 'raw' to store our data
# The -p flag means "create parent directories if needed" and won't error if it exists
mkdir -p raw

# Change into the raw directory
cd raw

# Download chess data files using curl
# -o flag specifies the output filename (what to save it as)
# Each file contains thousands of chess games
curl -o mega2600_part_01.pgn https://raw.githubusercontent.com/rozim/ChessData/master/mega2600_part_01.pgn
curl -o mega2600_part_02.pgn https://raw.githubusercontent.com/rozim/ChessData/master/mega2600_part_02.pgn
curl -o mega2600_part_03.pgn https://raw.githubusercontent.com/rozim/ChessData/master/mega2600_part_03.pgn
curl -o mega2600_part_04.pgn https://raw.githubusercontent.com/rozim/ChessData/master/mega2600_part_04.pgn
curl -o mega2600_part_05.pgn https://raw.githubusercontent.com/rozim/ChessData/master/mega2600_part_05.pgn

# List files with details using ll (or ls -la if ll isn't available)
# This shows file sizes, permissions, and timestamps
ll
# If ll doesn't work, use: ls -la

# Count how many games we downloaded
# grep -c counts matching lines (each game has one Result line)
echo "Downloaded $(grep -c Result *.pgn) chess games"

# Move back up one directory level
# .. means "parent directory" (the directory that contains this one)
cd ..

# Check where we are now
pwd  # pwd = "print working directory"
```

## Understanding the Data Format

Let's look at what's inside a PGN file:

```bash
# Show the first 30 lines of a PGN file
# head shows the beginning of a file (default is 10 lines, -30 means 30 lines)
head -30 raw/mega2600_part_01.pgn

# Alternative: use cat to show a whole file (but it's huge!)
# cat raw/mega2600_part_01.pgn  # Don't do this - file is too big!

# Better: use less for scrolling through large files
# less raw/mega2600_part_01.pgn  # Press 'q' to quit
```

You'll see PGN format looks like this:
```
[Event "Tournament Name"]
[White "Player A"]
[Black "Player B"] 
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
```

The Result field tells us who won:
- `1-0` means White wins (1 point for White, 0 for Black)
- `0-1` means Black wins (0 points for White, 1 for Black)
- `1/2-1/2` means Draw (half point each)

```bash
# See just the Result lines from our files
# grep searches for text patterns in files
grep "Result" raw/*.pgn | head -5
```

## Step 1: Basic Pipeline

Start with simple commands, then combine them with pipes (|):

```bash
# Count total games in each file
# -c flag means "count matching lines" instead of showing them
grep -c "Result" raw/*.pgn

# Extract all Result lines and count unique values
# The pipe (|) sends output from one command to the next
grep "Result" raw/*.pgn | sort | uniq -c
# Explanation:
# 1. grep finds all Result lines
# 2. sort puts them in alphabetical order
# 3. uniq -c counts consecutive identical lines

# AWK version (more efficient but harder to read)
awk '/Result/ {
    if ($2 ~ /"1-0"/) white++
    else if ($2 ~ /"0-1"/) black++
    else if ($2 ~ /"1\/2-1\/2"/) draw++
} END {
    print "White:", white, "Black:", black, "Draws:", draw
}' raw/*.pgn

# This AWK command is cryptic! Here's what it does:
# - /Result/ means "for lines containing 'Result'"
# - $2 is the second field (space-separated)
# - ~ means "matches pattern"
# - END runs after all lines are processed
# But this is hard to read and modify - let's use Python instead!
```

## Step 2: Python CLI Tool

### Understanding the uv Shebang

Look at the top of our parse.py file:

```bash
# Show the first 5 lines of parse.py
head -5 parse.py
```

You'll see this special "shebang" line AT THE TOP of the file:
```python
#!/usr/bin/env uv run --quiet --script
# /// script
# dependencies = ["typer", "rich"]  
# ///
```

This shebang (the #! part) tells the system:
1. Use `uv run` to execute this Python script
2. `--quiet` suppresses uv's output messages
3. `--script` treats it as a standalone script
4. The dependencies (typer, rich) are installed automatically!

### Making the Script Executable and Using It

```bash
# Make the script executable
# chmod changes file permissions: +x adds "execute" permission
chmod +x parse.py

# Now we can run it directly with ./
# The ./ means "in the current directory"
./parse.py raw/mega2600_part_01.pgn

# Our script uses Typer CLI framework, so it has built-in help!
./parse.py --help

# Try different output formats (these are flags we added with Typer)
./parse.py raw/mega2600_part_01.pgn --format text   # Pretty table (default)
./parse.py raw/mega2600_part_01.pgn --format json   # JSON for databases
./parse.py raw/mega2600_part_01.pgn --format csv    # CSV for spreadsheets
```

## Step 3: Using find and xargs

### The Problem with Spaces in Filenames

```bash
# Let's create a file with spaces to see the problem
touch "raw/test file with spaces.pgn"
echo '[Result "1-0"]' > "raw/test file with spaces.pgn"

# List files to see our test file
ls raw/

# This FAILS because xargs splits on spaces:
find raw -name "*.pgn" | xargs ls -l
# Error! It tries to find "raw/test", "file", "with", "spaces.pgn" separately!

# This WORKS using null-byte separation:
find raw -name "*.pgn" -print0 | xargs -0 ls -l
# Success! The whole filename is treated as one unit

# Clean up our test file
rm "raw/test file with spaces.pgn"
```

### Understanding find and xargs Commands

```bash
# find: searches for files matching criteria
# Syntax: find [where] -name [pattern] [actions]
find raw -name "*.pgn" -type f
# Explanation:
# - raw: search in the raw directory
# - -name "*.pgn": files ending in .pgn (* means "any characters")
# - -type f: only files (not directories)

# Add -print0 for null-byte separation (safer!)
find raw -name "*.pgn" -type f -print0
# You won't see the difference visually, but the separator is \0 not \n

# xargs: takes input and runs a command with it as arguments
# Basic usage:
find raw -name "*.pgn" -type f -print0 | xargs -0 echo "Found:"

# Process each file individually with our parser
# -n1 means "one argument at a time"
find raw -name "*.pgn" -type f -print0 | xargs -0 -n1 ./parse.py

# Get absolute paths (full path from root /)
# realpath converts relative paths to absolute paths
find raw -name "*.pgn" -type f -print0 | xargs -0 realpath

# Process files in parallel for speed!
# -P4 means "use 4 parallel processes"
find raw -name "*.pgn" -type f -print0 | xargs -0 -n1 -P4 ./parse.py
```

## Step 4: Database Integration with sqlite-utils

```bash
# First, make sure sqlite-utils is installed
which sqlite-utils  # Check if it's available
# If not found, install with: pip install sqlite-utils

# Build a pipeline that processes files and stores in SQLite
# The backslash (\) continues the command on the next line
find raw -name "*.pgn" -type f -print0 | \
  xargs -0 -n1 ./parse.py --format json | \
  sqlite-utils insert games.db games -

# Let's break down what this does:
# 1. find: gets all .pgn files
# 2. xargs: runs parse.py on each file
# 3. parse.py --format json: outputs JSON (one game per line)
# 4. sqlite-utils insert: reads JSON from stdin (-) and inserts into database
#    - games.db is the database file (created automatically)
#    - games is the table name

# Now query our database!
# SQL lets us ask questions about our data
sqlite-utils query games.db "
  SELECT result, COUNT(*) as count 
  FROM games 
  GROUP BY result
" --table
# This counts how many games had each result

# See a few games in detail
sqlite-utils query games.db "SELECT * FROM games LIMIT 5" --table

# Export back to JSON if needed
sqlite-utils query games.db "SELECT * FROM games LIMIT 5" --json

# Check the database file size
ls -lh games.db
```

## Step 5: AWK for Stream Processing (Optional)

AWK is a classic Unix tool, but the syntax is cryptic:

```bash
# AWK counting example
awk '/Result/ {
    results[$2]++
} END {
    for (r in results) print r, results[r]
}' raw/*.pgn

# What this means:
# - /Result/: for lines containing "Result"
# - results[$2]++: increment counter for the second field
# - END: after processing all lines
# - for (r in results): loop through the results

# Honestly, this is hard to read and debug!
# Our Python script is much clearer and does the same thing.
```

## Building the Complete Pipeline

Let's combine everything we've learned:

```bash
# Complete pipeline with progress indication
echo "Processing chess games..."

# This complex pipeline processes files one by one with feedback
find raw -name "*.pgn" -type f -print0 | \
  while IFS= read -r -d '' file; do
    echo "Processing: $(basename "$file")"
    ./parse.py "$file" --format json
  done | \
  sqlite-utils insert analysis.db games - \
    --replace \
    --alter

# Let's understand the while loop:
# - IFS= : don't split on spaces (Internal Field Separator)
# - read -r -d '': read null-delimited input
# - basename: gets just the filename without the path
# - The loop shows progress as it processes each file

# sqlite-utils flags:
# - --replace: replace the table if it exists
# - --alter: automatically adjust table schema if needed

# Generate a summary report using SQL
sqlite-utils query analysis.db "
  SELECT 
    COUNT(*) as total_games,
    SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as white_wins,
    SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as black_wins,
    SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws
  FROM games
" --table

# The CASE WHEN is SQL's if-then:
# If result = '1-0' then count 1, else count 0
# SUM adds them all up
```

## Using the Makefile

The Makefile automates common tasks:

```bash
make download    # Download sample data
make parse       # Parse all PGN files
make database    # Create SQLite database
make clean       # Clean generated files
make all         # Run complete pipeline
```

## Key Concepts

### Unix Pipeline Philosophy
- Each tool does one thing well
- Tools compose through text streams
- Data flows without intermediate files

### Performance Benefits
- **Streaming**: Process data as it arrives
- **Parallelism**: Use multiple cores with `xargs -P`
- **Memory efficiency**: No need to load entire dataset

### Best Practices
1. Start simple, add complexity gradually
2. Test on small data first
3. Use `-print0` for robust file handling
4. Make scripts executable with `chmod +x`
5. Use JSON as intermediate format for structured data



## Exercises

1. **Modify parse.py** to extract additional metadata (players, dates)
2. **Create a pipeline** that finds games by a specific player
3. **Compare performance** of AWK vs Python for large files
4. **Build a Makefile** target that processes new files incrementally

Remember: The power isn't in any single tool, but in how they compose together!