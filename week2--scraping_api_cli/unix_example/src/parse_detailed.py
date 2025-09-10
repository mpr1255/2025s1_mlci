#!/usr/bin/env uv run --quiet --script
# /// script  
# dependencies = []
# ///

import sys
import json
import re

def main():
    game_data = []
    current_game = {}
    
    for line in sys.stdin:
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            # Parse metadata
            match = re.match(r'\[(\w+)\s+"([^"]+)"\]', line)
            if match:
                key, value = match.groups()
                if key == 'Event' and current_game:
                    # Start of new game, save previous
                    if 'result' in current_game:
                        game_data.append(current_game)
                    current_game = {}
                current_game[key.lower()] = value
    
    # Don't forget the last game
    if current_game and 'result' in current_game:
        game_data.append(current_game)
    
    # Output as JSONL for sqlite-utils
    for game in game_data:
        print(json.dumps(game))

if __name__ == "__main__":
    main()