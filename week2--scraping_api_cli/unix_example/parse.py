#!/usr/bin/env uv run --quiet --script
# /// script
# dependencies = ["typer", "rich", "json"]
# ///

"""Parse chess PGN files and output game statistics."""

import sys
import json
import re
from pathlib import Path
from typing import Optional
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()


class OutputFormat(str, Enum):
    """Output format options."""
    text = "text"
    json = "json"
    csv = "csv"


def parse_pgn_file(filepath: Path) -> dict:
    """Parse a PGN file and extract game results.
    
    Args:
        filepath: Path to the PGN file
        
    Returns:
        Dictionary with game statistics
    """
    white_wins = 0
    black_wins = 0
    draws = 0
    games = []
    current_game = {}
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            
            # Parse metadata lines
            if line.startswith('[') and line.endswith(']'):
                match = re.match(r'\[(\w+)\s+"([^"]+)"\]', line)
                if match:
                    key, value = match.groups()
                    
                    # New game starts with Event tag
                    if key == 'Event' and current_game:
                        if 'result' in current_game:
                            games.append(current_game)
                        current_game = {}
                    
                    current_game[key.lower()] = value
                    
                    # Count results
                    if key == 'Result':
                        if value == '1-0':
                            white_wins += 1
                        elif value == '0-1':
                            black_wins += 1
                        elif value == '1/2-1/2':
                            draws += 1
        
        # Don't forget the last game
        if current_game and 'result' in current_game:
            games.append(current_game)
    
    total = white_wins + black_wins + draws
    
    return {
        'file': str(filepath),
        'total_games': total,
        'white_wins': white_wins,
        'black_wins': black_wins,
        'draws': draws,
        'white_win_pct': round(white_wins / total * 100, 1) if total > 0 else 0,
        'black_win_pct': round(black_wins / total * 100, 1) if total > 0 else 0,
        'draw_pct': round(draws / total * 100, 1) if total > 0 else 0,
        'games': games  # Individual game data for detailed analysis
    }


@app.command()
def main(
    file: Path = typer.Argument(
        ...,
        help="Path to PGN file to parse",
        exists=True,
        readable=True
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.text,
        "--format", "-f",
        help="Output format"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed", "-d",
        help="Include individual game details (JSON format only)"
    )
):
    """Parse a chess PGN file and output game statistics.
    
    Examples:
        ./parse.py game.pgn
        ./parse.py game.pgn --format json
        ./parse.py game.pgn --format json --detailed
    """
    try:
        results = parse_pgn_file(file)
        
        if format == OutputFormat.json:
            # For JSON, output just the data for easy piping
            if not detailed:
                # Remove individual games for summary output
                results.pop('games', None)
            # Output one JSON object per line for streaming
            for game in results.get('games', [results]):
                if isinstance(game, dict) and game != results:
                    # Individual game
                    print(json.dumps(game))
                else:
                    # Summary
                    print(json.dumps(results))
                    break
                    
        elif format == OutputFormat.csv:
            # CSV header and data
            if detailed:
                console.print("[yellow]CSV detailed output not implemented. Use --format json --detailed[/yellow]", err=True)
                sys.exit(1)
            print("file,total,white_wins,black_wins,draws,white_pct,black_pct,draw_pct")
            print(f"{results['file']},{results['total_games']},{results['white_wins']},"
                  f"{results['black_wins']},{results['draws']},{results['white_win_pct']},"
                  f"{results['black_win_pct']},{results['draw_pct']}")
                  
        else:  # text format
            # Create a nice table
            table = Table(title=f"Chess Game Analysis: {file.name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", justify="right", style="green")
            table.add_column("Percentage", justify="right", style="yellow")
            
            table.add_row("Total Games", str(results['total_games']), "-")
            table.add_row("White Wins", str(results['white_wins']), f"{results['white_win_pct']}%")
            table.add_row("Black Wins", str(results['black_wins']), f"{results['black_win_pct']}%")
            table.add_row("Draws", str(results['draws']), f"{results['draw_pct']}%")
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error parsing {file}: {e}[/red]", err=True)
        sys.exit(1)


if __name__ == "__main__":
    app()