# Terminal 2: Reproduce & Augment a Streaming Data Analysis Pipeline

This walkthrough demonstrates how command-line tools can be faster than distributed systems like Hadoop for many data processing tasks. We'll reproduce and modernize Adam Drake's famous chess analysis pipeline that was [**235x faster** than a Hadoop cluster.](https://adamdrake.com/command-line-tools-can-be-235x-faster-than-your-hadoop-cluster.html)

You'll learn to build streaming data pipelines using Unix tools, replace arcane `awk` with readable Python, and store results in SQLite for further analysis.

## Prerequisites

### Install required tools

```bash
# Check what's already installed
which uv curl wget sqlite-utils tree

# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install sqlite-utils
uv tool install sqlite-utils
```

### Install tree command (for directory visualization)

**On university cluster (Nix):**
```bash
nix profile install nixpkgs#tree
```

**On macOS with Homebrew:**
```bash
brew install tree
```

**On Linux (Ubuntu/Debian/WSL):**
```bash
sudo apt update && sudo apt install tree
```

**If you don't have tree, you can see directory structure with:**
```bash
# Alternative to tree
find . -type d | sed -e 's/[^-][^\/]*\//  /g' -e 's/^  //' -e 's/-/|/'
```

## Step 1: Set Up Proper Project Structure

Learn essential file system commands and create a well-organized project:

### Basic File System Commands

```bash
# Create directories
mkdir my-directory              # Create single directory
mkdir -p path/to/nested/dirs   # Create nested directories (-p = parents)

# Create empty files  
touch filename.txt             # Creates empty file or updates timestamp
touch file1.txt file2.txt      # Create multiple files

# See what you created
ls                            # List files and directories
ls -la                        # List with details (long format, all files)
```

### Create Project Structure

```bash
# Create project directory
mkdir chess-analysis
cd chess-analysis

# Set up directory structure with mkdir -p
mkdir -p raw/        # Raw data - never modify these files
mkdir -p src/        # Source code and scripts  
mkdir -p out/        # Generated outputs - safe to delete anytime
mkdir -p tests/      # Test files and validation
mkdir -p ref/        # Reference materials and documentation

# Create placeholder files to see structure
touch raw/.gitkeep src/.gitkeep out/.gitkeep tests/.gitkeep ref/.gitkeep

# Verify structure with tree
tree

# Alternative if no tree command:
find . -type d | sed -e 's/[^-][^\/]*\//  /g' -e 's/^  //' -e 's/-/|/'
```

**Why this structure matters:**
- `raw/` - Original data that you never modify
- `src/` - Your code and processing scripts  
- `out/` - Generated files you can delete without worry
- Clear separation prevents accidentally corrupting source data

## Step 2: Understand the Problem and Data

We're analyzing chess games in PGN (Portable Game Notation) format to count wins/losses/draws.

**Sample PGN format:**
```
[Event "F/S Return Match"]
[Site "Belgrade, Serbia Yugoslavia|JUG"] 
[Date "1992.11.04"]
[Round "29"]
[White "Fischer, Robert J."]
[Black "Spassky, Boris V."]
[Result "1-0"]
(actual chess moves follow...)
```

**What we care about:**
- `[Result "1-0"]` = White wins
- `[Result "0-1"]` = Black wins  
- `[Result "1/2-1/2"]` = Draw
- `[Result "*"]` = Ongoing/unknown (ignore)

## Step 3: Download Chess Data

Let's get some real chess data and learn to examine files:

```bash
# Move to raw data directory
cd raw/

# Download some sample chess data (these are example URLs - you may need to find current ones)
curl -o sample.pgn "https://www.chess.com/games/download/pgn"

# For this demo, let's create a sample PGN file to work with
cat > sample.pgn << 'EOF'
[Event "Sample Tournament"]
[Site "Online"]
[Date "2024.01.15"] 
[Round "1"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 1-0

[Event "Another Game"]
[Site "Club Match"]
[Date "2024.01.16"]
[Round "2"] 
[White "Player C"]
[Black "Player D"]
[Result "0-1"]

1. d4 d5 2. c4 e6 3. Nc3 0-1

[Event "Draw Example"]
[Site "Tournament"]
[Date "2024.01.17"]
[Round "3"]
[White "Player E"] 
[Black "Player F"]
[Result "1/2-1/2"]

1. e4 c5 2. Nf3 d6 1/2-1/2
EOF

# Check what we have
ls -lh
```

### Learn File Examination Commands

Now let's learn essential commands for examining our data:

```bash
# Count lines in files
wc -l sample.pgn              # Count lines 
wc -l *.pgn                   # Count lines in all PGN files
wc -w sample.pgn              # Count words
wc -c sample.pgn              # Count characters

# Look at file contents
cat sample.pgn                # Show entire file content
head sample.pgn               # Show first 10 lines
head -5 sample.pgn            # Show first 5 lines
tail sample.pgn               # Show last 10 lines  
tail -5 sample.pgn            # Show last 5 lines

# Look at specific parts
grep "Result" sample.pgn      # Find lines containing "Result"
grep -n "Event" sample.pgn    # Show line numbers (-n flag)
grep -i "WHITE" sample.pgn    # Case-insensitive search (-i flag)
```

### Understanding PGN Structure

```bash
# Let's examine the structure of our chess data
echo "=== First few lines ==="
head -10 sample.pgn

echo -e "\n=== All Result lines ==="
grep "Result" sample.pgn

echo -e "\n=== Count different result types ==="
grep "Result" sample.pgn | sort | uniq -c

echo -e "\n=== File statistics ==="
echo "Total lines: $(wc -l < sample.pgn)"
echo "Result lines: $(grep -c "Result" sample.pgn)"
echo "Games: $(grep -c "Event" sample.pgn)"
```

## Step 4: Build the Basic Pipeline

Let's start with Adam Drake's approach, then improve it.

### Original approach (simple but slow):

```bash
cd ../  # Back to project root

# Simple pipeline - counts all results
cat raw/*.pgn | grep "Result" | sort | uniq -c
```

### Faster approach with awk (but hard to read):

```bash
# Adam Drake's optimized version - but awk is cryptic!
cat raw/*.pgn | grep "Result" | awk '{ split($0, a, "-"); res = substr(a[1], length(a[1]), 1); if (res == 1) white++; if (res == 0) black++; if (res == 2) draw++;} END { print white+black+draw, white, black, draw }'
```

## Step 5: Replace AWK with Readable Python

Let's create a Python script that's much easier to understand and maintain:

```bash
# Create our Python parser
cat > src/parse_chess_results.py << 'EOF'
#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer",
# ]
# ///

"""
Modern replacement for the arcane awk chess parser.
Reads chess game results from stdin and outputs counts.
"""

import sys
import re
import json
import typer

app = typer.Typer(help="Parse chess game results from PGN files")

def parse_result_line(line: str) -> str | None:
    """Extract result from a PGN Result line."""
    # Look for [Result "1-0"] style lines
    match = re.search(r'\[Result\s+"([^"]+)"\]', line)
    if not match:
        return None
    
    result = match.group(1)
    
    # Map results to our categories
    if result == "1-0":
        return "white_wins"
    elif result == "0-1": 
        return "black_wins"
    elif result == "1/2-1/2":
        return "draws"
    else:
        return "other"

@app.command()
def count_results(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Count chess game results from stdin."""
    
    counts = {
        "white_wins": 0,
        "black_wins": 0,
        "draws": 0,
        "other": 0
    }
    
    total_lines = 0
    for line in sys.stdin:
        total_lines += 1
        
        # Only process Result lines
        if "Result" not in line:
            continue
            
        result = parse_result_line(line.strip())
        if result:
            counts[result] += 1
    
    # Output results
    total_games = counts["white_wins"] + counts["black_wins"] + counts["draws"]
    
    if json_output:
        output = {
            **counts,
            "total_games": total_games,
            "total_lines_processed": total_lines
        }
        print(json.dumps(output))
    else:
        print(f"Total games: {total_games}")
        print(f"White wins: {counts['white_wins']}")
        print(f"Black wins: {counts['black_wins']}")
        print(f"Draws: {counts['draws']}")
        print(f"Other: {counts['other']}")

if __name__ == "__main__":
    app()
EOF

# Make it executable
chmod +x src/parse_chess_results.py
```

## Step 6: Test the Python Pipeline

```bash
# Test with a single file first
cat raw/sample.pgn | grep "Result" | ./src/parse_chess_results.py

# Test with JSON output
cat raw/sample.pgn | grep "Result" | ./src/parse_chess_results.py --json

# Full pipeline with all files
cat raw/*.pgn | grep "Result" | ./src/parse_chess_results.py
```

Compare this to the cryptic awk version - much more readable and maintainable!

## Step 7: Optimize with Parallel Processing

Let's reproduce Adam Drake's parallel optimization, but with our Python script:

```bash
# Sequential processing (baseline)
time (cat raw/*.pgn | grep "Result" | ./src/parse_chess_results.py)

# Parallel processing with xargs
time (find raw/ -name "*.pgn" -print0 | \
      xargs -0 -n1 -P4 grep "Result" | \
      ./src/parse_chess_results.py)
```

**What's happening:**
- `find raw/ -name "*.pgn" -print0` - Find all PGN files, null-terminated
- `xargs -0 -n1 -P4` - Run grep on each file in parallel (4 processes)
- Final Python script aggregates all results

## Step 8: Store Results in SQLite Database

Now let's enhance our pipeline to store results in a database:

```bash
# Create enhanced version that outputs structured data
cat > src/parse_chess_to_db.py << 'EOF'
#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer",
# ]
# ///

"""
Parse chess results and output JSONL for database insertion.
"""

import sys
import re
import json
from datetime import datetime
import typer

def parse_game_metadata(content: str) -> dict:
    """Extract game metadata from PGN content."""
    metadata = {}
    
    # Extract common PGN tags
    patterns = {
        'event': r'\[Event\s+"([^"]+)"\]',
        'site': r'\[Site\s+"([^"]+)"\]', 
        'date': r'\[Date\s+"([^"]+)"\]',
        'white': r'\[White\s+"([^"]+)"\]',
        'black': r'\[Black\s+"([^"]+)"\]',
        'result': r'\[Result\s+"([^"]+)"\]'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        metadata[key] = match.group(1) if match else None
    
    return metadata

@app.command()
def main():
    """Parse chess games and output JSONL records."""
    
    game_buffer = []
    current_game = ""
    
    for line in sys.stdin:
        current_game += line
        
        # End of game indicated by empty line after moves
        if line.strip() == "" and current_game.strip():
            if "[Result" in current_game:
                metadata = parse_game_metadata(current_game)
                
                # Add processing timestamp
                metadata['processed_at'] = datetime.now().isoformat()
                
                # Categorize result
                result = metadata.get('result', '*')
                if result == "1-0":
                    metadata['result_category'] = "white_wins"
                elif result == "0-1":
                    metadata['result_category'] = "black_wins" 
                elif result == "1/2-1/2":
                    metadata['result_category'] = "draws"
                else:
                    metadata['result_category'] = "other"
                
                # Output as JSONL
                print(json.dumps(metadata))
            
            current_game = ""

app = typer.Typer()
app.command()(main)

if __name__ == "__main__":
    app()
EOF

chmod +x src/parse_chess_to_db.py
```

## Step 9: Build Complete Data Pipeline

Now let's create the full pipeline that processes chess files and stores in SQLite:

```bash
# Process files and store in database
find raw/ -name "*.pgn" -print0 | \
    xargs -0 -n1 -P4 cat | \
    ./src/parse_chess_to_db.py | \
    sqlite-utils insert out/chess_games.db games - --pk=event --pk=white --pk=black --pk=date

# Query the results
sqlite-utils query out/chess_games.db "
    SELECT 
        result_category,
        COUNT(*) as game_count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM games) as percentage
    FROM games 
    GROUP BY result_category
"

# More detailed analysis
sqlite-utils query out/chess_games.db "
    SELECT 
        substr(date, 1, 4) as year,
        result_category,
        COUNT(*) as games
    FROM games 
    WHERE date IS NOT NULL 
    GROUP BY year, result_category
    ORDER BY year, result_category
" --table
```

## Step 10: Performance Comparison and Benchmarking

Let's measure our pipeline performance:

```bash
# Create benchmark script
cat > src/benchmark.py << 'EOF' 
#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer",
# ]
# ///

import subprocess
import time
import typer

def run_pipeline(description: str, command: str):
    """Time a pipeline command."""
    print(f"\n🏃 {description}")
    print(f"Command: {command}")
    
    start = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end = time.time()
    
    duration = end - start
    print(f"⏱️  Duration: {duration:.2f} seconds")
    
    if result.returncode == 0:
        print("✅ Success")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
    else:
        print("❌ Failed")
        print(f"Error: {result.stderr}")
    
    return duration

@typer.command()
def main():
    """Benchmark different pipeline approaches."""
    
    # Test with available data
    pipelines = [
        ("Simple grep + Python", 
         "cat raw/*.pgn | grep 'Result' | ./src/parse_chess_results.py"),
        
        ("Parallel grep + Python",
         "find raw/ -name '*.pgn' -print0 | xargs -0 -n1 -P4 grep 'Result' | ./src/parse_chess_results.py"),
        
        ("Full parallel pipeline to database",
         "find raw/ -name '*.pgn' -print0 | xargs -0 -n1 -P4 cat | ./src/parse_chess_to_db.py | wc -l")
    ]
    
    print("🎯 Chess Pipeline Benchmarks")
    print("=" * 50)
    
    results = []
    for desc, cmd in pipelines:
        duration = run_pipeline(desc, cmd)
        results.append((desc, duration))
    
    print("\n📊 Summary:")
    print("-" * 30)
    for desc, duration in results:
        print(f"{desc}: {duration:.2f}s")
    
    # Calculate speedup
    if len(results) > 1:
        baseline = results[0][1]
        for desc, duration in results[1:]:
            speedup = baseline / duration if duration > 0 else 0
            print(f"   → {speedup:.1f}x faster than baseline")

if __name__ == "__main__":
    typer.run(main)
EOF

chmod +x src/benchmark.py

# Run benchmarks
./src/benchmark.py
```

## Step 11: Advanced Analysis Queries

Now that we have structured data, we can do sophisticated analysis:

```bash
# Top events by game count
sqlite-utils query out/chess_games.db "
    SELECT event, COUNT(*) as games 
    FROM games 
    GROUP BY event 
    ORDER BY games DESC 
    LIMIT 10
" --table

# Win rates by player (for players with many games)
sqlite-utils query out/chess_games.db "
    WITH player_stats AS (
        SELECT white as player, 
               SUM(CASE WHEN result_category = 'white_wins' THEN 1 ELSE 0 END) as wins,
               COUNT(*) as total_games
        FROM games 
        GROUP BY white
        HAVING total_games >= 10
    )
    SELECT player, wins, total_games, 
           ROUND(wins * 100.0 / total_games, 2) as win_percentage
    FROM player_stats
    ORDER BY win_percentage DESC
    LIMIT 10
" --table

# Temporal patterns - draws over time
sqlite-utils query out/chess_games.db "
    SELECT substr(date, 1, 4) as year,
           AVG(CASE WHEN result_category = 'draws' THEN 1.0 ELSE 0.0 END) as draw_rate
    FROM games 
    WHERE date IS NOT NULL AND date != '????.??.??'
    GROUP BY year
    ORDER BY year
" --table
```

## Step 12: Create Reusable Pipeline Scripts

Let's package this into reusable scripts:

```bash
# Create main pipeline runner
cat > src/run_analysis.sh << 'EOF'
#!/bin/bash
# Complete chess analysis pipeline

set -e  # Exit on error

echo "🏁 Starting chess analysis pipeline..."

# Check dependencies
echo "📋 Checking dependencies..."
command -v sqlite-utils >/dev/null || { echo "❌ sqlite-utils not found"; exit 1; }

# Create output directory
mkdir -p out/

# Run analysis
echo "⚡ Processing chess files..."
find raw/ -name "*.pgn" -print0 | \
    xargs -0 -n1 -P$(nproc) cat | \
    ./src/parse_chess_to_db.py | \
    sqlite-utils insert out/chess_games.db games - --replace

echo "📊 Analysis complete!"
echo "Database: out/chess_games.db"

# Show summary
echo -e "\n📈 Summary:"
sqlite-utils query out/chess_games.db "
    SELECT 
        result_category,
        COUNT(*) as games,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM games), 1) as percentage
    FROM games 
    GROUP BY result_category
    ORDER BY games DESC
" --table

echo -e "\n✅ Pipeline complete! Query the database with:"
echo "   sqlite-utils query out/chess_games.db 'YOUR_SQL_HERE'"
EOF

chmod +x src/run_analysis.sh

# Run the complete pipeline
./src/run_analysis.sh
```

## Key Learning Points

- **Stream processing beats batch processing** for many tasks - no need to load everything into memory
- **Parallel pipelines** can dramatically improve performance using `xargs -P`
- **Replace arcane tools** (like complex awk) with readable Python while keeping performance
- **Proper directory structure** keeps raw data safe and outputs organized  
- **SQLite is powerful** for analysis - much better than just counting with scripts
- **Unix philosophy** - small composable tools that work together

## Performance Insights

Adam Drake's original findings:
- **Hadoop cluster (7 machines)**: 26 minutes for 1.75GB = ~1.14MB/sec
- **Optimized shell pipeline**: 12 seconds for 3.46GB = ~270MB/sec  
- **Result**: 235x faster than Hadoop!

Our modernized version maintains the performance benefits while being much more:
- **Readable** - Python instead of cryptic awk
- **Maintainable** - proper structure and error handling
- **Extensible** - SQLite database enables complex analysis
- **Reproducible** - clear workflow and dependencies

## Next Steps

- Add data validation and error handling
- Implement incremental processing for new files
- Create visualization dashboards using the SQLite data
- Experiment with other parallel processing tools
- Scale up to even larger datasets
- Compare with modern big data tools (Spark, DuckDB, etc.)
