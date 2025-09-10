#!/bin/bash
# Convert markdown to HTML and open in browser for copying to Notion

if [ $# -eq 0 ]; then
    echo "Usage: ./md2notion.sh input.md"
    exit 1
fi

INPUT="$1"
TEMP_HTML="/tmp/notion_$(basename "$INPUT" .md).html"

echo "Converting $INPUT to HTML..."
uv run convert_to_notion.py "$INPUT" --font "Monaco" -o "$TEMP_HTML"

echo "Opening in browser..."
open "$TEMP_HTML"

echo "Now select all (Cmd+A) and copy (Cmd+C) from browser, then paste into Notion"