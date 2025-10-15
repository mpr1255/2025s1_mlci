-- Sample SQL Queries for SpeakGer Database
-- Run these in sqlite3 or TablePlus to explore the data
-- Usage: sqlite3 speakger.db < week6_sample_queries.sql

-- ====================
-- BASIC QUERIES
-- ====================

-- How many speeches total?
SELECT COUNT(*) as total_speeches
FROM speeches;

-- How many unique speakers?
SELECT COUNT(DISTINCT MPID) as unique_speakers
FROM speeches
WHERE MPID > 0;

-- Date range of speeches
SELECT
  MIN(Date) as earliest_speech,
  MAX(Date) as latest_speech
FROM speeches
WHERE Date IS NOT NULL;

-- ====================
-- PARTY ANALYSIS
-- ====================

-- Count speeches by party
SELECT
  Party,
  COUNT(*) as num_speeches
FROM speeches
WHERE Party != '[]' AND Party IS NOT NULL
GROUP BY Party
ORDER BY num_speeches DESC;

-- Average speech length by party
SELECT
  Party,
  COUNT(*) as num_speeches,
  AVG(LENGTH(Speech)) as avg_speech_length,
  MAX(LENGTH(Speech)) as longest_speech
FROM speeches
WHERE Party != '[]'
GROUP BY Party
ORDER BY avg_speech_length DESC;

-- ====================
-- SPEAKER ANALYSIS (requires JOIN to mps_meta)
-- ====================

-- Top 10 most active speakers
SELECT
  m.Name,
  m.SexOrGender,
  COUNT(*) as num_speeches,
  MIN(s.Date) as first_speech,
  MAX(s.Date) as last_speech
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.MPID > 0
GROUP BY m.Name, m.SexOrGender
ORDER BY num_speeches DESC
LIMIT 10;

-- Speaker participation by gender
SELECT
  m.SexOrGender,
  COUNT(DISTINCT m.MPID) as num_speakers,
  COUNT(*) as num_speeches,
  AVG(LENGTH(s.Speech)) as avg_speech_length
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
WHERE m.SexOrGender IS NOT NULL AND s.MPID > 0
GROUP BY m.SexOrGender;

-- ====================
-- TIME-SERIES ANALYSIS
-- ====================

-- Speeches per year
SELECT
  strftime('%Y', Date) as year,
  COUNT(*) as num_speeches
FROM speeches
WHERE Date IS NOT NULL
GROUP BY year
ORDER BY year;

-- Speeches per month (for recent data)
SELECT
  strftime('%Y-%m', Date) as month,
  COUNT(*) as num_speeches
FROM speeches
WHERE Date IS NOT NULL AND Date >= '2020-01-01'
GROUP BY month
ORDER BY month;

-- ====================
-- CONTENT ANALYSIS
-- ====================

-- Find speeches mentioning specific topics
SELECT
  m.Name,
  s.Date,
  s.Party,
  substr(s.Speech, 1, 200) as preview
FROM speeches s
LEFT JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.Speech LIKE '%Klimawandel%'
   OR s.Speech LIKE '%Klima %'
ORDER BY s.Date DESC
LIMIT 10;

-- Count mentions of different topics
SELECT
  'Klima' as topic,
  COUNT(*) as mentions
FROM speeches
WHERE Speech LIKE '%Klima%'
UNION ALL
SELECT
  'Migration',
  COUNT(*)
FROM speeches
WHERE Speech LIKE '%Migration%'
UNION ALL
SELECT
  'Wirtschaft',
  COUNT(*)
FROM speeches
WHERE Speech LIKE '%Wirtschaft%';

-- ====================
-- CHAIR vs REGULAR SPEECHES
-- ====================

-- Compare chair speeches to regular speeches
SELECT
  Chair,
  COUNT(*) as num_speeches,
  AVG(LENGTH(Speech)) as avg_length
FROM speeches
GROUP BY Chair;

-- ====================
-- INTERJECTIONS ANALYSIS
-- ====================

-- How many speeches are interjections?
SELECT
  Interjection,
  COUNT(*) as num_speeches,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM speeches), 2) as percentage
FROM speeches
GROUP BY Interjection;

-- ====================
-- LONGEST & SHORTEST SPEECHES
-- ====================

-- Top 10 longest speeches
SELECT
  m.Name,
  s.Date,
  s.Party,
  LENGTH(s.Speech) as speech_length,
  substr(s.Speech, 1, 100) as preview
FROM speeches s
LEFT JOIN mps_meta m ON s.MPID = m.MPID
ORDER BY speech_length DESC
LIMIT 10;

-- Shortest non-empty speeches
SELECT
  m.Name,
  s.Date,
  LENGTH(s.Speech) as speech_length,
  s.Speech
FROM speeches s
LEFT JOIN mps_meta m ON s.MPID = m.MPID
WHERE LENGTH(s.Speech) > 0 AND LENGTH(s.Speech) < 50
ORDER BY speech_length ASC
LIMIT 10;

-- ====================
-- SPEAKER METADATA EXPLORATION
-- ====================

-- Most common occupations
SELECT
  Occupation,
  COUNT(*) as num_mps
FROM mps_meta
WHERE Occupation IS NOT NULL AND Occupation != '[]'
GROUP BY Occupation
ORDER BY num_mps DESC
LIMIT 20;

-- Age distribution (MPs alive during speeches)
SELECT
  strftime('%Y', Born) as birth_year,
  COUNT(*) as num_mps
FROM mps_meta
WHERE Born IS NOT NULL
GROUP BY birth_year
ORDER BY birth_year;

-- ====================
-- COMPLEX JOINS
-- ====================

-- Find all speeches by MPs born in a specific decade
SELECT
  m.Name,
  strftime('%Y', m.Born) as birth_year,
  COUNT(*) as num_speeches,
  AVG(LENGTH(s.Speech)) as avg_speech_length
FROM speeches s
JOIN mps_meta m ON s.MPID = m.MPID
WHERE m.Born >= '1960-01-01' AND m.Born < '1970-01-01'
GROUP BY m.Name, birth_year
ORDER BY num_speeches DESC;

-- Party affiliation changes over time (if mapping data is loaded)
-- Note: This query requires all_mps_mapping table
-- SELECT
--   m.Name,
--   p.Period,
--   p.Party
-- FROM mps_mapping p
-- JOIN mps_meta m ON p.MPID = m.MPID
-- WHERE m.Name = 'Angela Merkel'  -- Example name
-- ORDER BY p.Period;

-- ====================
-- USEFUL UTILITY QUERIES
-- ====================

-- Check data quality: find NULL or empty values
SELECT
  'NULL MPIDs' as issue,
  COUNT(*) as count
FROM speeches
WHERE MPID IS NULL OR MPID = 0
UNION ALL
SELECT
  'NULL Dates',
  COUNT(*)
FROM speeches
WHERE Date IS NULL OR Date = ''
UNION ALL
SELECT
  'Empty speeches',
  COUNT(*)
FROM speeches
WHERE Speech IS NULL OR LENGTH(Speech) = 0;

-- Verify foreign key integrity
SELECT
  COUNT(*) as orphaned_speeches
FROM speeches s
LEFT JOIN mps_meta m ON s.MPID = m.MPID
WHERE s.MPID > 0 AND m.MPID IS NULL;

-- ====================
-- EXPORT RESULTS
-- ====================

-- Export to CSV (run in sqlite3 command line)
-- .mode csv
-- .output speaker_stats.csv
-- SELECT m.Name, COUNT(*) as num_speeches
-- FROM speeches s
-- JOIN mps_meta m ON s.MPID = m.MPID
-- GROUP BY m.Name
-- ORDER BY num_speeches DESC;
-- .output stdout
-- .mode column
