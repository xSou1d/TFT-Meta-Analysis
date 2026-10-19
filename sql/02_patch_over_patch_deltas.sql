-- Patch-over-patch change in each trait's average placement using a window function.
-- Positive delta = the trait got worse (higher placement number).
WITH per_patch AS (
    SELECT m.sample_tier, m.patch, t.trait,
           COUNT(*) AS n, AVG(p.placement) AS avg_placement
    FROM participant_traits t
    JOIN participants p ON p.participant_id = t.participant_id
    JOIN matches m      ON m.match_id = p.match_id
    GROUP BY m.sample_tier, m.patch, t.trait
),
with_prev AS (
    SELECT *,
           LAG(patch)         OVER w AS prev_patch,
           LAG(avg_placement) OVER w AS prev_avg_placement,
           LAG(n)             OVER w AS prev_n
    FROM per_patch
    WINDOW w AS (PARTITION BY sample_tier, trait ORDER BY CAST(patch AS INTEGER))
)
SELECT sample_tier, trait, prev_patch AS patch_from, patch AS patch_to,
       prev_n AS n_from, n AS n_to,
       ROUND(prev_avg_placement, 3) AS placement_from,
       ROUND(avg_placement, 3)      AS placement_to,
       ROUND(avg_placement - prev_avg_placement, 3) AS delta
FROM with_prev
WHERE prev_patch IS NOT NULL AND n >= 30 AND prev_n >= 30
ORDER BY ABS(avg_placement - prev_avg_placement) DESC;
