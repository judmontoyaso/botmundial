-- ==============================================
-- BotMundial - Supabase Database Schema
-- FIFA World Cup 2026 Analysis Dashboard
-- ==============================================

-- Equipos del mundial
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(3) NOT NULL UNIQUE,
    group_letter CHAR(1) NOT NULL,
    fifa_ranking INTEGER,
    confederation VARCHAR(20),
    flag_emoji VARCHAR(10),
    stats JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partidos
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    match_number INTEGER UNIQUE,
    stage VARCHAR(30) NOT NULL DEFAULT 'group',
    group_letter CHAR(1),
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    match_date TIMESTAMPTZ,
    venue VARCHAR(200),
    city VARCHAR(100),
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mis predicciones para la polla
CREATE TABLE IF NOT EXISTS my_predictions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) UNIQUE,
    predicted_home_score INTEGER NOT NULL,
    predicted_away_score INTEGER NOT NULL,
    confidence INTEGER DEFAULT 50,
    ai_suggested_home INTEGER,
    ai_suggested_away INTEGER,
    notes TEXT,
    points_earned INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Predicciones AI (caché)
CREATE TABLE IF NOT EXISTS ai_predictions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    model_used VARCHAR(50),
    predicted_home_score INTEGER,
    predicted_away_score INTEGER,
    home_win_prob DECIMAL(5,4),
    draw_prob DECIMAL(5,4),
    away_win_prob DECIMAL(5,4),
    confidence_score DECIMAL(5,4),
    analysis_text TEXT,
    factors JSONB DEFAULT '[]'::jsonb,
    poisson_home_lambda DECIMAL(6,4) DEFAULT 1.2,
    poisson_away_lambda DECIMAL(6,4) DEFAULT 1.2,
    scoreline_matrix JSONB DEFAULT '[]'::jsonb,
    raw_stats JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Migración: añadir columnas Poisson si la tabla ya existe
ALTER TABLE ai_predictions ADD COLUMN IF NOT EXISTS poisson_home_lambda DECIMAL(6,4) DEFAULT 1.2;
ALTER TABLE ai_predictions ADD COLUMN IF NOT EXISTS poisson_away_lambda DECIMAL(6,4) DEFAULT 1.2;
ALTER TABLE ai_predictions ADD COLUMN IF NOT EXISTS scoreline_matrix JSONB DEFAULT '[]'::jsonb;
-- Cambiar precisión de columnas de probabilidad (si se creó antes con DECIMAL(5,2))
ALTER TABLE ai_predictions ALTER COLUMN home_win_prob TYPE DECIMAL(5,4);
ALTER TABLE ai_predictions ALTER COLUMN draw_prob TYPE DECIMAL(5,4);
ALTER TABLE ai_predictions ALTER COLUMN away_win_prob TYPE DECIMAL(5,4);
ALTER TABLE ai_predictions ALTER COLUMN confidence_score TYPE DECIMAL(5,4);

-- Índices
CREATE INDEX IF NOT EXISTS idx_matches_stage ON matches(stage);
CREATE INDEX IF NOT EXISTS idx_matches_group ON matches(group_letter);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_teams_group ON teams(group_letter);
CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code);
CREATE INDEX IF NOT EXISTS idx_my_predictions_match ON my_predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_match ON ai_predictions(match_id);

-- RLS Policies (deshabilitadas por ahora - sin auth)
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE my_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_predictions ENABLE ROW LEVEL SECURITY;

-- Permitir acceso público sin auth por ahora
CREATE POLICY "Allow public read on teams" ON teams FOR SELECT USING (true);
CREATE POLICY "Allow public all on teams" ON teams FOR ALL USING (true);

CREATE POLICY "Allow public read on matches" ON matches FOR SELECT USING (true);
CREATE POLICY "Allow public all on matches" ON matches FOR ALL USING (true);

CREATE POLICY "Allow public read on my_predictions" ON my_predictions FOR SELECT USING (true);
CREATE POLICY "Allow public all on my_predictions" ON my_predictions FOR ALL USING (true);

CREATE POLICY "Allow public read on ai_predictions" ON ai_predictions FOR SELECT USING (true);
CREATE POLICY "Allow public all on ai_predictions" ON ai_predictions FOR ALL USING (true);
