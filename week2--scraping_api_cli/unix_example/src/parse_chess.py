#!/usr/bin/env uv run --quiet --script
# /// script
# dependencies = []
# ///

import sys

def main():
    white = black = draw = 0
    
    for line in sys.stdin:
        if 'Result' in line:
            if '"1-0"' in line:
                white += 1
            elif '"0-1"' in line:
                black += 1
            elif '"1/2-1/2"' in line:
                draw += 1
    
    total = white + black + draw
    print(f"{total} {white} {black} {draw}")

if __name__ == "__main__":
    main()