-- "Great at high elo, bad at low elo": compare each trait's average placement in
-- high elo against each lower tier within the same patch. Gap > 0 means the trait
-- performs worse in the lower tier than at the top.
WITH per_tier AS (
    SELECT m.sample_tier, m.patch, t.trait,
           COUNT(*) AS n, AVG(p.placement) AS avg_placement
    FROM participant_traits t
    JOIN participants p ON p.participant_id = t.participant_id
    JOIN matches m      ON m.match_id = p.match_id
    GROUP BY m.sample_tier, m.patch, t.trait
    HAVING COUNT(*) >= 30
)
SELECT lo.patch, lo.trait, lo.sample_tier AS tier,
       hi.n AS n_high_elo, lo.n AS n_tier,
       ROUND(hi.avg_placement, 3) AS placement_high_elo,
       ROUND(lo.avg_placement, 3) AS placement_tier,
       ROUND(lo.avg_placement - hi.avg_placement, 3) AS gap
FROM per_tier lo
JOIN per_tier hi
  ON hi.patch = lo.patch AND hi.trait = lo.trait AND hi.sample_tier = 'HIGH_ELO'
WHERE lo.sample_tier <> 'HIGH_ELO'
ORDER BY ABS(lo.avg_placement - hi.avg_placement) DESC;
