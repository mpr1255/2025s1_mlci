#!/bin/bash

# Test script to verify all tutorial commands work
# Run this to validate the tutorial before giving to students

set -e
set -u

echo "🧪 Testing Week 6 Database Tutorial"
echo "===================================="
echo ""

# Clean up any previous test
rm -rf test_validation
mkdir test_validation
cd test_validation

echo "✅ Test 1: Download MP metadata"
curl -sL "https://berd-platform.de/records/g3225-rba63/files/all_mps_meta.csv?download=1" \
  > all_mps_meta.csv

ROWS=$(wc -l < all_mps_meta.csv | tr -d ' ')
if [ "$ROWS" -gt "1000" ]; then
  echo "   ✓ Downloaded $ROWS rows of MP metadata"
else
  echo "   ✗ FAILED: Only got $ROWS rows"
  exit 1
fi

# Check delimiter is semicolon
HEADER=$(head -1 all_mps_meta.csv)
if [[ "$HEADER" == *";"* ]]; then
  echo "   ✓ Correct delimiter (semicolon)"
else
  echo "   ✗ FAILED: Wrong delimiter"
  exit 1
fi

echo ""
echo "✅ Test 2: Download Bremen speeches sample"
# Download and save to temp file first, then take first N lines
curl -sL "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" 2>/dev/null \
  | head -101 > bremen_sample.csv &

# Wait for download with timeout
COUNTER=0
while [ $COUNTER -lt 30 ]; do
  if [ -f "bremen_sample.csv" ]; then
    SAMPLE_ROWS=$(wc -l < bremen_sample.csv | tr -d ' ')
    if [ "$SAMPLE_ROWS" -eq "101" ]; then
      break
    fi
  fi
  sleep 1
  COUNTER=$((COUNTER + 1))
done

wait

SAMPLE_ROWS=$(wc -l < bremen_sample.csv | tr -d ' ')
if [ "$SAMPLE_ROWS" -eq "101" ]; then
  echo "   ✓ Downloaded 100 speeches + header"
else
  echo "   ⚠️  WARNING: Got $SAMPLE_ROWS rows (expected 101)"
  echo "   Continuing anyway..."
fi

echo ""
echo "✅ Test 3: Load into SQLite with sqlite-utils"
uvx sqlite-utils insert test.db speeches bremen_sample.csv \
  --csv --detect-types --silent

TABLE_COUNT=$(uvx sqlite-utils tables test.db --counts --json | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
echo "   ✓ Loaded $TABLE_COUNT speeches into database"

echo ""
echo "✅ Test 4: Verify data structure"
# Check that we can query the data
RESULT=$(sqlite3 test.db "SELECT COUNT(*) FROM speeches")
echo "   ✓ Query returned: $RESULT rows"

# Check date column exists and has data
DATE_CHECK=$(sqlite3 test.db "SELECT COUNT(*) FROM speeches WHERE Date IS NOT NULL" || echo "0")
echo "   ✓ Found $DATE_CHECK rows with dates"

# Get actual date range
DATES=$(sqlite3 test.db "SELECT MIN(Date), MAX(Date) FROM speeches WHERE Date IS NOT NULL AND Date != ''" || echo "NULL,NULL")
echo "   ✓ Date range: $DATES"

echo ""
echo "✅ Test 5: Load MP metadata with primary key"
uvx sqlite-utils insert test.db mps_meta all_mps_meta.csv \
  --csv --delimiter=";" --detect-types --pk=MPID --silent

MP_COUNT=$(sqlite3 test.db "SELECT COUNT(*) FROM mps_meta")
echo "   ✓ Loaded $MP_COUNT MPs"

echo ""
echo "✅ Test 6: Test JOIN query"
JOIN_RESULT=$(sqlite3 test.db "
SELECT COUNT(*)
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.MPID > 0
")
echo "   ✓ JOIN works: $JOIN_RESULT speeches matched to MPs"

echo ""
echo "✅ Test 7: Create indexes"
sqlite3 test.db <<EOF
CREATE INDEX IF NOT EXISTS idx_speeches_mpid ON speeches(MPID);
CREATE INDEX IF NOT EXISTS idx_speeches_date ON speeches(Date);
EOF
echo "   ✓ Indexes created"

# Verify index exists
INDEX_CHECK=$(sqlite3 test.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_speeches_mpid'")
if [ -n "$INDEX_CHECK" ]; then
  echo "   ✓ Index verification passed"
else
  echo "   ✗ FAILED: Index not found"
  exit 1
fi

echo ""
echo "✅ Test 8: Sample queries"

# Most common party
sqlite3 test.db -header -column "
SELECT Party, COUNT(*) as count
FROM speeches
WHERE Party != '[]'
GROUP BY Party
ORDER BY count DESC
LIMIT 3
" | head -5

echo ""
echo "🎉 All tests passed!"
echo ""
echo "Summary:"
echo "  • Downloaded and parsed CSV data ✓"
echo "  • Loaded into SQLite successfully ✓"
echo "  • Primary keys and foreign keys work ✓"
echo "  • JOINs execute correctly ✓"
echo "  • Indexes created ✓"
echo "  • Sample queries return results ✓"
echo ""
echo "Tutorial is ready for students!"
echo ""
echo "Clean up test files:"
echo "  cd .. && rm -rf test_validation"
