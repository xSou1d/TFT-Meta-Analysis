-- Selection-bias check: compare each game with the average placement of everyone
-- who finished at the same level in the same patch (levels clipped to 7-10).
-- A trait with a negative avg_vs_level beats other boards at the same level.
WITH games AS (
    SELECT p.participant_id, m.sample_tier, m.patch, p.placement,
           MIN(MAX(p.level, 7), 10) AS level_bucket
    FROM participants p
    JOIN matches m ON m.match_id = p.match_id
),
baseline AS (
    SELECT sample_tier, patch, level_bucket, AVG(placement) AS level_avg
    FROM games
    GROUP BY sample_tier, patch, level_bucket
)
SELECT g.sample_tier, g.patch, t.trait, COUNT(*) AS n,
       ROUND(AVG(g.placement), 3)               AS avg_placement,
       ROUND(AVG(g.placement - b.level_avg), 3) AS avg_vs_level
FROM games g
JOIN baseline b USING (sample_tier, patch, level_bucket)
JOIN participant_traits t ON t.participant_id = g.participant_id
GROUP BY g.sample_tier, g.patch, t.trait
HAVING COUNT(*) >= 30
ORDER BY g.sample_tier, CAST(g.patch AS INTEGER), avg_vs_level;
