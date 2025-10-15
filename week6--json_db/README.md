# Week 6 Database Tutorial Files

## What's Included

This folder contains a complete 90-minute tutorial for teaching students how to:
1. Download CSV data from public APIs
2. Design relational database schemas
3. Load data into SQLite
4. Query and visualize the results

## Files

### Main Tutorial
- **`week6_database_tutorial.md`** - Complete step-by-step tutorial (paste this into Notion)

### Supporting Scripts
- **`week6_visualize.R`** - R script that queries SQLite and creates a histogram
- **`week6_pipeline.sh`** - Shell script that automates the entire pipeline

## Quick Start for Students

```bash
# Make sure you have uv installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the complete pipeline
./week6_pipeline.sh 1000

# This will:
# - Download metadata + 1000 sample speeches
# - Create speakger.db
# - Run queries
# - Generate visualization (if R is installed)
```

## For Instructors

### Tutorial Structure (90 minutes)

| Section | Time | Activity |
|---------|------|----------|
| Setup & Installation | 10 min | Install tools, verify environment |
| Download & Inspect | 15 min | curl, head, tail, wc commands |
| Schema Design | 15 min | dbdiagram.io, discuss PK/FK |
| Load into SQLite | 20 min | sqlite-utils, understand what happens |
| Query the Database | 15 min | SQL in terminal and TablePlus |
| Visualize with R | 10 min | Run R script, discuss results |
| Discussion | 5 min | Reflection questions |

### Learning Outcomes

Students will be able to:
- ✅ Use curl with redirects (-L flag)
- ✅ Inspect CSV files with Unix tools
- ✅ Explain primary vs foreign keys
- ✅ Design normalized schemas
- ✅ Use sqlite-utils to load CSV into SQLite
- ✅ Write SQL JOINs across multiple tables
- ✅ Create indexes for query optimization
- ✅ Connect R to SQLite for visualization
- ✅ Build automated pipelines

### Data Source

**SpeakGer Corpus** from BERD@NFDI:
- 15+ million speeches from German parliaments (1949-2025)
- Public, open access (CC BY 4.0)
- Real relational structure (3 tables that join on MPID)

**Why this dataset?**
- Real data, not toy examples
- Manageable size for teaching (can sample)
- Clear foreign key relationships
- Interesting queries (politics, gender, time-series)
- Publicly accessible, no auth required

### Schema Overview

```
mps_meta (MPID [PK])
  ↓
speeches (MPID [FK])
  ↓
mps_mapping (MPID [FK])
```

## Testing the Tutorial

All commands have been tested and work as of 2025-10-10.

Key verified items:
- ✅ curl downloads work with -L flag
- ✅ CSV delimiters correct (semicolon for meta, comma for speeches)
- ✅ sqlite-utils loads data correctly
- ✅ SQL queries return expected results
- ✅ R script generates visualization

## Customization

To change sample size:
```bash
./week6_pipeline.sh 5000  # Get 5000 speeches instead of 1000
```

To use a different state (smaller/larger):
```bash
# Edit pipeline.sh and change Bremen.csv to:
# - Saarland.csv (337MB, smaller)
# - Hamburg.csv (477MB)
# - Bundestag.csv (1.8GB, largest)
```

## Troubleshooting

### "curl: command not found"
- macOS/Linux: should be installed by default
- Windows: install Git Bash or use WSL2

### "sqlite3: command not found"
- macOS: should be installed by default
- Linux: `sudo apt install sqlite3`
- Windows: download from https://sqlite.org/download.html

### "uvx: command not found"
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### "Rscript: command not found"
Install R from https://cloud.r-project.org/

### CSV loading errors
Check delimiter:
- `all_mps_meta.csv` uses **semicolon** (`;`)
- Speech files use **comma** (`,`)

Use `--delimiter=";"` for semicolon files

## Extensions for Advanced Students

1. **Time-series analysis**: Track how parties' speech patterns change over decades
2. **Word frequency**: Most common words by party/speaker
3. **Network analysis**: Who responds to whom (interjections)
4. **Gender analysis**: Speech length/frequency by gender
5. **Streamlit dashboard**: Interactive web UI for exploring the data
6. **Full-text search**: Load all 15M speeches, enable FTS5
7. **Docker container**: Package entire pipeline for reproducibility

## License

Tutorial materials: CC BY 4.0
SpeakGer data: CC BY 4.0 (cite original paper)

## Citation

When using SpeakGer data:
```
Lange, K.-R., Jentsch, C. (2023). SpeakGer: A meta-data enriched speech
corpus of German state and federal parliaments. Proceedings of the 3rd
Workshop on Computational Linguistics for Political Text Analysis@KONVENS 2023.
```

## Questions?

Contact: [your contact info]
Course repo: [link to github]
