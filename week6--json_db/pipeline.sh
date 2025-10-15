#!/bin/bash

# Complete pipeline: Download → Load → Query → Visualize
# SpeakGer parliamentary speech database creation
# Usage: ./pipeline.sh [sample_size]
# Default sample_size: 1000 speeches

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
SAMPLE_SIZE=${1:-1000}
DATA_DIR="speakger_data"
DB_NAME="speakger.db"

echo "🚀 SpeakGer Database Pipeline"
echo "==============================="
echo "Sample size: $SAMPLE_SIZE speeches"
echo ""

# Create data directory
echo "📁 Creating data directory..."
mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

# Download metadata
echo "📥 Downloading MP metadata..."
if [ ! -f "all_mps_meta.csv" ]; then
  curl -sL -o all_mps_meta.csv \
    "https://berd-platform.de/records/g3225-rba63/files/all_mps_meta.csv?download=1"
  echo "   ✓ Downloaded all_mps_meta.csv ($(wc -l < all_mps_meta.csv) rows)"
else
  echo "   ↺ Using cached all_mps_meta.csv"
fi

# Download mapping data
echo "📥 Downloading MP mapping data..."
if [ ! -f "all_mps_mapping.csv" ]; then
  curl -sL -o all_mps_mapping.csv \
    "https://berd-platform.de/records/g3225-rba63/files/all_mps_mapping.csv?download=1"
  echo "   ✓ Downloaded all_mps_mapping.csv ($(wc -l < all_mps_mapping.csv) rows)"
else
  echo "   ↺ Using cached all_mps_mapping.csv"
fi

# Download speech sample
echo "📥 Downloading Bremen speeches (first $SAMPLE_SIZE)..."
TOTAL_LINES=$((SAMPLE_SIZE + 1))  # +1 for header
curl -sL "https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1" \
  | head -n "$TOTAL_LINES" > bremen_sample.csv
echo "   ✓ Downloaded bremen_sample.csv ($((TOTAL_LINES - 1)) speeches)"

echo ""
echo "🗄️  Creating database..."
# Remove old database if exists
[ -f "$DB_NAME" ] && rm "$DB_NAME"

# Load MP metadata with MPID as primary key
echo "   → Loading mps_meta table..."
uvx sqlite-utils insert "$DB_NAME" mps_meta all_mps_meta.csv \
  --csv \
  --delimiter=";" \
  --detect-types \
  --pk=MPID \
  --silent

# Load speeches
echo "   → Loading speeches table..."
uvx sqlite-utils insert "$DB_NAME" speeches bremen_sample.csv \
  --csv \
  --detect-types \
  --silent

# Show table counts
echo "   ✓ Database created:"
uvx sqlite-utils tables "$DB_NAME" --counts

echo ""
echo "🔍 Creating indexes..."
sqlite3 "$DB_NAME" <<EOF
CREATE INDEX IF NOT EXISTS idx_speeches_mpid ON speeches(MPID);
CREATE INDEX IF NOT EXISTS idx_speeches_date ON speeches(Date);
CREATE INDEX IF NOT EXISTS idx_speeches_party ON speeches(Party);
EOF
echo "   ✓ Created 3 indexes on speeches table"

echo ""
echo "📊 Database summary:"
sqlite3 "$DB_NAME" <<EOF
.mode column
.headers on
SELECT 'Total MPs' as metric, COUNT(*) as count FROM mps_meta
UNION ALL
SELECT 'Total speeches', COUNT(*) FROM speeches
UNION ALL
SELECT 'Unique speakers', COUNT(DISTINCT MPID) FROM speeches WHERE MPID > 0
UNION ALL
SELECT 'Date range', MIN(Date) || ' to ' || MAX(Date) FROM speeches WHERE Date IS NOT NULL;
EOF

echo ""
echo "🔎 Sample query: Top 10 most active speakers"
sqlite3 "$DB_NAME" <<EOF
.mode column
.headers on
SELECT
  m.Name as Speaker,
  COUNT(*) as Speeches
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.MPID > 0
GROUP BY m.Name
ORDER BY Speeches DESC
LIMIT 10;
EOF

echo ""
echo "📈 Running R visualization..."
cd ..
if command -v Rscript &> /dev/null; then
  Rscript visualize.R "$DATA_DIR/$DB_NAME"
else
  echo "   ⚠️  R not found, skipping visualization"
  echo "   Install R from https://cloud.r-project.org/"
fi

echo ""
echo "✨ Pipeline complete!"
echo ""
echo "Next steps:"
echo "  • Open database in TablePlus: $DATA_DIR/$DB_NAME"
echo "  • Run queries: sqlite3 $DATA_DIR/$DB_NAME"
echo "  • View visualization: open speeches_histogram.png"
echo ""
echo "To load full dataset:"
echo "  curl -L -o $DATA_DIR/Bremen.csv 'https://berd-platform.de/records/g3225-rba63/files/Bremen.csv?download=1'"
echo "  uvx sqlite-utils insert $DATA_DIR/$DB_NAME speeches_full $DATA_DIR/Bremen.csv --csv --detect-types"
