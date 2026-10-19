-- The units most often fielded with each trait in the latest patch, plus how
-- boards with that unit place. Useful context for a designer reading a trait shift.
WITH latest AS (
    SELECT MAX(CAST(patch AS INTEGER)) AS patch FROM matches
),
boards AS (
    SELECT t.trait, u.character_id, p.placement, p.participant_id
    FROM participant_traits t
    JOIN participants p      ON p.participant_id = t.participant_id
    JOIN matches m           ON m.match_id = p.match_id
    JOIN participant_units u ON u.participant_id = p.participant_id
    WHERE CAST(m.patch AS INTEGER) = (SELECT patch FROM latest)
      AND m.sample_tier = 'HIGH_ELO'
),
ranked AS (
    SELECT trait, character_id,
           COUNT(DISTINCT participant_id) AS boards,
           ROUND(AVG(placement), 3)       AS avg_placement,
           ROW_NUMBER() OVER (PARTITION BY trait ORDER BY COUNT(DISTINCT participant_id) DESC) AS rk
    FROM boards
    GROUP BY trait, character_id
)
SELECT trait, rk AS rank, character_id, boards, avg_placement
FROM ranked
WHERE rk <= 5
ORDER BY trait, rk;
