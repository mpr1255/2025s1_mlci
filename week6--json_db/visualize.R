#!/usr/bin/env Rscript

# Visualize SpeakGer database: Create histogram of speeches over time
# Usage: ./visualize.R [database_path]
# Default database_path: speakger.db in current directory

# Install packages if needed
packages <- c("DBI", "RSQLite", "ggplot2", "dplyr")
for (pkg in packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    message(paste("Installing", pkg, "..."))
    install.packages(pkg, repos = "https://cloud.r-project.org", quiet = TRUE)
    library(pkg, character.only = TRUE)
  }
}

# Get database path from command line args
args <- commandArgs(trailingOnly = TRUE)
db_path <- if (length(args) > 0) args[1] else "speakger.db"

if (!file.exists(db_path)) {
  stop(paste("Database not found:", db_path))
}

cat("📊 Connecting to database:", db_path, "\n")

# Connect to database
con <- dbConnect(RSQLite::SQLite(), db_path)

# Query: count speeches per year
query <- "
SELECT
  strftime('%Y', Date) as year,
  COUNT(*) as num_speeches
FROM speeches
WHERE Date IS NOT NULL
  AND Date != ''
  AND year IS NOT NULL
GROUP BY year
ORDER BY year
"

cat("🔍 Running query...\n")
df <- dbGetQuery(con, query)

# Show summary
cat(sprintf("Found %d years of data (%s to %s)\n",
            nrow(df),
            min(df$year),
            max(df$year)))

dbDisconnect(con)

# Convert year to numeric
df$year <- as.numeric(df$year)

# Filter out any invalid years (< 1900 or > current year)
current_year <- as.numeric(format(Sys.Date(), "%Y"))
df <- df %>%
  filter(year >= 1900 & year <= current_year)

# Create histogram
p <- ggplot(df, aes(x = year, y = num_speeches)) +
  geom_col(fill = "steelblue", width = 0.8) +
  labs(
    title = "German Parliamentary Speeches Over Time",
    subtitle = "Data from SpeakGer corpus (Bremen sample)",
    x = "Year",
    y = "Number of Speeches",
    caption = "Source: BERD@NFDI SpeakGer Dataset"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 16, face = "bold"),
    plot.subtitle = element_text(size = 12, color = "gray40"),
    axis.title = element_text(size = 11),
    plot.caption = element_text(size = 9, color = "gray50", hjust = 0)
  )

# Save plot
output_file <- "speeches_histogram.png"
ggsave(output_file, p, width = 10, height = 6, dpi = 300)

cat("✅ Plot saved to:", normalizePath(output_file), "\n")

# Also save a CSV summary
summary_file <- "speeches_by_year.csv"
write.csv(df, summary_file, row.names = FALSE)
cat("📄 Summary data saved to:", normalizePath(summary_file), "\n")
