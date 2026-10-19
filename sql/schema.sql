-- Normalised schema for TFT match data (SQLite).
-- One match has 8 participants; each participant has many active traits and units.

DROP TABLE IF EXISTS participant_units;
DROP TABLE IF EXISTS participant_traits;
DROP TABLE IF EXISTS participants;
DROP TABLE IF EXISTS matches;

CREATE TABLE matches (
    match_id       TEXT PRIMARY KEY,
    patch          TEXT NOT NULL,      -- e.g. '11'
    set_number     INTEGER,            -- NULL for the original v1 data
    game_datetime  INTEGER,            -- epoch ms; NULL for the original v1 data
    sample_tier    TEXT NOT NULL       -- HIGH_ELO, GOLD, PLATINUM, ...
);

CREATE TABLE participants (
    participant_id  INTEGER PRIMARY KEY,
    match_id        TEXT NOT NULL REFERENCES matches(match_id),
    puuid           TEXT,
    placement       INTEGER NOT NULL CHECK (placement BETWEEN 1 AND 8),
    level           INTEGER,
    last_round      INTEGER,
    gold_left       INTEGER,
    time_eliminated REAL
);

CREATE TABLE participant_traits (
    participant_id  INTEGER NOT NULL REFERENCES participants(participant_id),
    trait           TEXT NOT NULL,
    tier            INTEGER,
    PRIMARY KEY (participant_id, trait)
);

CREATE TABLE participant_units (
    participant_id  INTEGER NOT NULL REFERENCES participants(participant_id),
    slot            INTEGER NOT NULL,
    character_id    TEXT NOT NULL,
    PRIMARY KEY (participant_id, slot)
);

CREATE INDEX idx_participants_match ON participants(match_id);
CREATE INDEX idx_traits_trait ON participant_traits(trait);
CREATE INDEX idx_units_char ON participant_units(character_id);
