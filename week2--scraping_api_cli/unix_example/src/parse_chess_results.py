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
