#!/usr/bin/awk -f

# AWK script to parse chess game results from PGN files
# Usage: cat *.pgn | ./parse.awk
# or: awk -f parse.awk *.pgn

/Result/ {
    if ($2 ~ /"1-0"/) white++
    else if ($2 ~ /"0-1"/) black++
    else if ($2 ~ /"1\/2-1\/2"/) draw++
}

END {
    total = white + black + draw
    print "=== Chess Game Analysis ==="
    print "Total games analyzed:", total
    print "White wins:", white, "(" int(white/total*100) "%)"
    print "Black wins:", black, "(" int(black/total*100) "%)"
    print "Draws:", draw, "(" int(draw/total*100) "%)"
    print ""
    print "Raw counts (for piping):", total, white, black, draw
}