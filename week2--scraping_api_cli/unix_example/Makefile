# Simple Makefile for Unix Pipeline Tutorial
.PHONY: all clean download parse database help

# Default target
all: download parse database

help:
	@echo "Available targets:"
	@echo "  make download  - Download sample chess data"
	@echo "  make parse     - Parse PGN files and show statistics"
	@echo "  make database  - Create SQLite database from parsed data"
	@echo "  make clean     - Remove generated files (keeps raw data)"
	@echo "  make all       - Run complete pipeline"

download:
	@echo "Downloading chess data..."
	@mkdir -p raw
	@cd raw && \
	curl -O https://raw.githubusercontent.com/rozim/ChessData/master/mega2600_part_01.pgn && \
	curl -O https://raw.githubusercontent.com/rozim/ChessData/master/mega2600_part_02.pgn
	@echo "Downloaded $$(grep -c Result raw/*.pgn) games"

parse: parse.py
	@echo "Parsing chess games..."
	@chmod +x parse.py
	@find raw -name "*.pgn" -type f -print0 | xargs -0 -n1 ./parse.py

database: parse.py
	@echo "Creating database..."
	@chmod +x parse.py
	@find raw -name "*.pgn" -type f -print0 | \
		xargs -0 -n1 ./parse.py --format json | \
		sqlite-utils insert games.db games - --replace
	@echo "Database created: games.db"
	@sqlite-utils query games.db "SELECT COUNT(*) as total_games FROM games" --table

clean:
	@echo "Cleaning generated files..."
	@rm -f games.db analysis.db *.db
	@echo "Clean complete (raw data preserved)"