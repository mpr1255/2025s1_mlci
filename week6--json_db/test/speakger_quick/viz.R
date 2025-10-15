library(DBI); library(RSQLite); library(ggplot2)
con <- dbConnect(SQLite(), "speakger.db")

# Top speakers by gender
df <- dbGetQuery(con, "
  SELECT m.Name, m.SexOrGender as Gender, COUNT(*) as speeches
  FROM speeches s JOIN mps_meta m ON s.MPID = m.MPID
  WHERE s.MPID > 0 AND m.SexOrGender IS NOT NULL
  GROUP BY m.Name, m.SexOrGender
  ORDER BY speeches DESC LIMIT 15
")
dbDisconnect(con)

ggplot(df, aes(x=reorder(Name, speeches), y=speeches, fill=Gender)) +
  geom_col() + coord_flip() +
  scale_fill_manual(values=c("male"="#4A90E2", "female"="#E24A90")) +
  labs(title="Top 15 Speakers in Bremen Parliament",
       subtitle="Colored by gender",
       x=NULL, y="Number of Speeches") +
  theme_minimal() + theme(legend.position="top")
ggsave("speeches.png", width=10, height=7)
cat("Saved speeches.png\n")
