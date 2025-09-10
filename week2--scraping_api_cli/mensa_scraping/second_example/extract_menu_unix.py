#!/usr/bin/env uv run --quiet --script
# /// script
# dependencies = ["beautifulsoup4"]
# ///

"""
Unix-composable menu extractor using pup JSON output.
Reads file paths from stdin, extracts menu data as JSONL to stdout.

Usage examples:
  # Test on single file
  echo "data_wget/www.mensaplan.de/mainz/mensaria/index.html" | uv run extract_menu_unix.py
  
  # Full pipeline with rg
  rg -l "aw-weekly-menu" data_wget | uv run extract_menu_unix.py | jq -s '.' | sqlite-utils insert menu.db meals -
  
  # Test single file with rg
  rg -l "aw-weekly-menu" data_wget | head -1 | uv run extract_menu_unix.py
"""

import json
import subprocess
import sys
from pathlib import Path

def extract_menu_from_file(html_file_path):
    """Extract menu data from a single HTML file using pup"""
    path = Path(html_file_path.strip())
    
    if not path.exists():
        print(f"Warning: File not found: {path}", file=sys.stderr)
        return []
    
    city = path.parent.parent.name
    mensa = path.parent.name
    
    try:
        # Use pup to extract meal data as JSON
        result = subprocess.run([
            'pup', 'div.meal json{}', '--file', str(path)
        ], capture_output=True, text=True, check=True)
        
        meals_data = json.loads(result.stdout)
        extracted = []
        
        for meal in meals_data:
            if meal.get('class') == 'primary meal':
                meal_id = meal.get('id', '')
                
                # Extract description
                description = ""
                try:
                    desc_div = next(child for child in meal['children'] if child.get('class') == 'description')
                    description = desc_div['children'][0]['text']
                except (StopIteration, KeyError, IndexError):
                    pass
                
                # Extract prices with regex fallback
                price_students = price_staff = None
                try:
                    price_p = next(child for child in meal['children'] if child.get('class') == 'price')
                    spans = price_p['children']
                    
                    # Parse prices from span text (e.g., "3,40 €")
                    if len(spans) >= 1 and 'text' in spans[0]:
                        price_text = spans[0]['text'].replace('€', '').replace(',', '.').strip()
                        try:
                            price_students = float(price_text)
                        except ValueError:
                            pass
                    
                    if len(spans) >= 2 and 'text' in spans[1]:
                        price_text = spans[1]['text'].replace('€', '').replace(',', '.').strip()
                        try:
                            price_staff = float(price_text)
                        except ValueError:
                            pass
                            
                except (StopIteration, KeyError, IndexError):
                    pass
                
                extracted.append({
                    'city': city,
                    'mensa': mensa,
                    'meal_id': meal_id,
                    'description': description,
                    'price_students': price_students,
                    'price_staff': price_staff,
                    'source_file': str(path)
                })
        
        return extracted
        
    except subprocess.CalledProcessError as e:
        print(f"Error running pup on {path}: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {path}: {e}", file=sys.stderr)
        return []

def main():
    """Read file paths from stdin and output JSONL to stdout"""
    for line in sys.stdin:
        file_path = line.strip()
        if not file_path:
            continue
            
        meals = extract_menu_from_file(file_path)
        for meal in meals:
            print(json.dumps(meal))

if __name__ == '__main__':
    main()