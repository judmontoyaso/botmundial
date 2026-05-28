-- H2H historical records between national teams
CREATE TABLE IF NOT EXISTS head_to_head (
  id BIGSERIAL PRIMARY KEY,
  team_a_code TEXT NOT NULL,
  team_b_code TEXT NOT NULL,
  h2h_wins_a INT NOT NULL DEFAULT 0,
  h2h_wins_b INT NOT NULL DEFAULT 0,
  h2h_draws INT NOT NULL DEFAULT 0,
  total_matches INT GENERATED ALWAYS AS (h2h_wins_a + h2h_wins_b + h2h_draws) STORED,
  last_updated TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT uq_h2h_pair UNIQUE(team_a_code, team_b_code)
);

-- Player absences: injuries, suspensions, doubtful
CREATE TABLE IF NOT EXISTS player_absences (
  id BIGSERIAL PRIMARY KEY,
  team_code TEXT NOT NULL,
  player_name TEXT NOT NULL,
  position TEXT,                        -- GK, DEF, MID, FWD
  importance INT NOT NULL DEFAULT 2,    -- 1=rotation, 2=starter, 3=key/star player
  reason TEXT DEFAULT 'injury',         -- injury | suspension | fitness
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_h2h_pair     ON head_to_head(team_a_code, team_b_code);
CREATE INDEX IF NOT EXISTS idx_abs_team     ON player_absences(team_code) WHERE is_active = TRUE;
