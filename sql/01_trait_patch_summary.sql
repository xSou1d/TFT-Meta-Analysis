-- Average placement, top-4 rate and win rate per trait per patch, with 95% CIs.
-- Placement CI uses the normal approximation; rate CIs use the Wilson interval.
WITH base AS (
    SELECT m.sample_tier, m.patch, t.trait, p.placement
    FROM participant_traits t
    JOIN participants p ON p.participant_id = t.participant_id
    JOIN matches m      ON m.match_id = p.match_id
),
agg AS (
    SELECT sample_tier, patch, trait,
           COUNT(*)                                        AS n,
           AVG(placement)                                  AS avg_placement,
           AVG(placement * placement) - AVG(placement) * AVG(placement) AS var_pop,
           AVG(CASE WHEN placement <= 4 THEN 1.0 ELSE 0 END) AS top4_rate,
           AVG(CASE WHEN placement = 1 THEN 1.0 ELSE 0 END)  AS win_rate
    FROM base
    GROUP BY sample_tier, patch, trait
)
SELECT sample_tier, patch, trait, n,
       ROUND(avg_placement, 3) AS avg_placement,
       ROUND(avg_placement - 1.96 * SQRT(var_pop * n / (n - 1.0) / n), 3) AS avg_placement_lo,
       ROUND(avg_placement + 1.96 * SQRT(var_pop * n / (n - 1.0) / n), 3) AS avg_placement_hi,
       ROUND(top4_rate, 3) AS top4_rate,
       ROUND((top4_rate + 1.9208 / n - 1.96 * SQRT(top4_rate * (1 - top4_rate) / n + 0.9604 / (n * n)))
             / (1 + 3.8416 / n), 3) AS top4_lo,
       ROUND((top4_rate + 1.9208 / n + 1.96 * SQRT(top4_rate * (1 - top4_rate) / n + 0.9604 / (n * n)))
             / (1 + 3.8416 / n), 3) AS top4_hi,
       ROUND(win_rate, 3) AS win_rate
FROM agg
WHERE n > 1
ORDER BY sample_tier, CAST(patch AS INTEGER), avg_placement;
