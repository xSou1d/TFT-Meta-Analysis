-- "Great at high elo, bad at low elo": compare each trait across ranks, set-wide.
-- Lower tiers have a lower trait-weighted average placement for EVERY trait
-- (losing boards there activate fewer traits), so each trait is first measured
-- against its own tier-and-patch baseline. gap > 0 = relatively weaker in
-- Gold/Plat than in high elo, i.e. the trait rewards high-elo execution.
WITH trait_games AS (
    SELECT CASE WHEN m.sample_tier = 'HIGH_ELO' THEN 'HIGH_ELO' ELSE 'GOLD_PLAT' END AS bracket,
           m.sample_tier, m.patch, t.trait, p.placement
    FROM participant_traits t
    JOIN participants p ON p.participant_id = t.participant_id
    JOIN matches m      ON m.match_id = p.match_id
),
baseline AS (
    SELECT sample_tier, patch, AVG(placement) AS base
    FROM trait_games
    GROUP BY sample_tier, patch
),
rel AS (
    SELECT g.bracket, g.trait, g.placement - b.base AS rel_placement
    FROM trait_games g
    JOIN baseline b USING (sample_tier, patch)
),
per_bracket AS (
    SELECT bracket, trait, COUNT(*) AS n, AVG(rel_placement) AS rel
    FROM rel
    GROUP BY bracket, trait
    HAVING COUNT(*) >= 100
)
SELECT hi.trait,
       hi.n AS n_high_elo, lo.n AS n_gold_plat,
       ROUND(hi.rel, 3) AS rel_high_elo,
       ROUND(lo.rel, 3) AS rel_gold_plat,
       ROUND(lo.rel - hi.rel, 3) AS gap
FROM per_bracket hi
JOIN per_bracket lo ON lo.trait = hi.trait AND lo.bracket = 'GOLD_PLAT'
WHERE hi.bracket = 'HIGH_ELO'
ORDER BY gap DESC;
