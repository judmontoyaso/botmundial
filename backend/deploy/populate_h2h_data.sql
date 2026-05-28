-- Historical head-to-head records for key World Cup 2026 national team matchups
-- Format: (team_a_code, team_b_code, wins_a, wins_b, draws)
-- Stored alphabetically (team_a < team_b) for consistency

INSERT INTO head_to_head (team_a_code, team_b_code, h2h_wins_a, h2h_wins_b, h2h_draws)
VALUES
-- South America rivalries
('ARG', 'BRA',  40, 44, 22),  -- Brazil slight historical edge
('ARG', 'CHI',  53, 36, 18),  -- Argentina dominates
('ARG', 'COL',  43, 27, 22),  -- Argentina dominates
('ARG', 'ECU',  31, 14,  9),  -- Argentina dominates
('ARG', 'PAR',  41, 24, 21),  -- Argentina dominates
('ARG', 'PER',  43, 12, 19),  -- Argentina dominates
('ARG', 'URU',  55, 37, 26),  -- Argentina dominates
('ARG', 'VEN',  27,  5,  9),  -- Argentina dominates
('BRA', 'CHI',  33, 12, 10),  -- Brazil dominates
('BRA', 'COL',  29, 18, 15),  -- Brazil dominates
('BRA', 'ECU',  33, 11,  7),  -- Brazil dominates
('BRA', 'PAR',  44, 16, 17),  -- Brazil dominates
('BRA', 'PER',  31,  9, 10),  -- Brazil dominates
('BRA', 'URU',  52, 34, 26),  -- Brazil dominates
('BRA', 'VEN',  32,  3,  9),  -- Brazil dominates
('COL', 'ECU',  31, 22, 10),  -- Colombia edge
('COL', 'URU',  30, 30, 15),  -- balanced
('COL', 'VEN',  33,  8, 13),  -- Colombia dominates
('CHI', 'URU',  27, 33, 17),  -- Uruguay edge
-- Europe rivalries
('AUT', 'GER',  14, 22,  5),  -- Germany dominates
('BEL', 'FRA',  13, 22,  6),  -- France edge
('BEL', 'NED',  27, 34, 13),  -- Netherlands edge
('CRO', 'ENG',   3,  5,  2),  -- England slight edge
('CRO', 'FRA',   2,  6,  1),  -- France dominates
('CRO', 'GER',   2,  7,  2),  -- Germany dominates
('CRO', 'POR',   3,  4,  0),  -- balanced
('CZE', 'GER',   5, 13,  4),  -- Germany dominates
('DEN', 'ENG',   8, 16,  9),  -- England edge
('DEN', 'NED',  12, 20,  6),  -- Netherlands edge
('ENG', 'FRA',  17,  9,  6),  -- England historical edge (France better recently)
('ENG', 'GER',  13, 17,  6),  -- Germany edge
('ENG', 'ITA',  11, 10,  7),  -- balanced
('ENG', 'NED',  14,  9,  6),  -- England slight edge
('ENG', 'POR',   9,  3,  3),  -- England dominates
('ENG', 'ESP',   9, 12,  4),  -- Spain slight edge (modern era)
('ESP', 'FRA',  14, 14,  6),  -- perfectly balanced
('ESP', 'GER',  14,  8,  2),  -- Spain edge (recent era)
('ESP', 'ITA',  10, 10,  5),  -- balanced
('ESP', 'NED',  10,  6,  4),  -- Spain slight edge
('ESP', 'POR',  19, 14, 10),  -- Spain slight edge
('FRA', 'GER',  14, 13,  4),  -- very close
('FRA', 'ITA',  14, 13,  9),  -- very close
('FRA', 'NED',  13,  6,  5),  -- France dominates
('FRA', 'POR',  18, 17, 10),  -- very close
('FRA', 'SUI',  20,  8,  6),  -- France dominates
('GER', 'ITA',  15, 18,  9),  -- Italy slight edge
('GER', 'NED',  15,  9,  5),  -- Germany edge
('GER', 'POL',  16,  5,  5),  -- Germany dominates
('GER', 'POR',  15,  8,  4),  -- Germany dominates
('GER', 'SUI',  17,  8,  4),  -- Germany dominates
('GER', 'TUR',  12,  5,  4),  -- Germany dominates
('HUN', 'GER',   5, 11,  3),  -- Germany dominates
('ITA', 'NED',   9,  5,  3),  -- Italy edge
('ITA', 'POR',   7,  4,  2),  -- Italy edge
('ITA', 'TUR',   8,  4,  3),  -- Italy edge
('NED', 'POR',   3,  5,  2),  -- Portugal slight edge
-- CONCACAF rivalries
('CAN', 'MEX',  12, 31, 14),  -- Mexico dominates
('CAN', 'USA',  17, 22, 10),  -- USA slight edge
('CRC', 'MEX',  14, 37, 15),  -- Mexico dominates
('CRC', 'USA',  13, 21,  8),  -- USA dominates
('HON', 'MEX',   7, 38, 11),  -- Mexico dominates
('HON', 'USA',   9, 20,  7),  -- USA dominates
('MEX', 'PAN',  10,  2,  3),  -- Mexico dominates
('MEX', 'USA',  36, 23, 19),  -- Mexico leads all-time
('PAN', 'USA',   2,  8,  2),  -- USA dominates
-- Cross-confederation notable
('ARG', 'ENG',   8,  7,  2),  -- Argentina slight edge
('ARG', 'ESP',   3,  5,  3),  -- Spain dominates
('ARG', 'FRA',   7,  4,  1),  -- Argentina edge (2022 WC)
('ARG', 'GER',   8,  7,  3),  -- very close
('ARG', 'ITA',  10,  7,  7),  -- Argentina slight edge
('ARG', 'MEX',  14,  2,  1),  -- Argentina dominates
('ARG', 'NED',   5,  4,  3),  -- very close
('ARG', 'POR',   4,  2,  0),  -- Argentina edge
('BRA', 'ENG',  10,  4,  4),  -- Brazil dominates
('BRA', 'ESP',  10,  9,  3),  -- very close
('BRA', 'FRA',   7,  4,  1),  -- Brazil slight edge
('BRA', 'GER',  12,  7,  3),  -- Brazil dominates
('BRA', 'ITA',  10,  5,  5),  -- Brazil dominates
('BRA', 'MEX',  15,  2,  2),  -- Brazil dominates
('BRA', 'NED',   7,  4,  3),  -- Brazil edge
('BRA', 'POR',  13,  4,  6),  -- Brazil dominates
('BRA', 'USA',  10,  2,  3),  -- Brazil dominates
('COL', 'USA',  11,  6,  4),  -- Colombia dominates
('ENG', 'USA',   9,  1,  1),  -- England dominates
('FRA', 'MAR',   7,  1,  1),  -- France dominates (MAR upset 2022 SF)
('GER', 'MEX',   8,  2,  0),  -- Germany dominates
('GER', 'USA',   8,  2,  2),  -- Germany dominates
('ITA', 'USA',  10,  4,  5),  -- Italy dominates
('JPN', 'KOR',  14, 25, 24),  -- Korea leads
('JPN', 'AUS',  24, 11,  6),  -- Japan dominates
('KOR', 'AUS',  15, 12,  9),  -- Korea slight edge
('MAR', 'ESP',   1,  3,  1),  -- Spain dominates
('MAR', 'POR',   0,  3,  1),  -- Portugal dominates (MAR won 2022 WC QF)
('MAR', 'SEN',  15, 17, 10),  -- Senegal slight edge
('MAR', 'NGA',  10, 13,  7),  -- Nigeria slight edge
('MEX', 'ARG',   2, 14,  1),  -- Argentina dominates
('MEX', 'BRA',   2, 15,  2),  -- Brazil dominates
('NGA', 'EGY',  28, 25, 12),  -- Nigeria slight edge
('NGA', 'SEN',  17, 20,  8),  -- Senegal slight edge
('POR', 'USA',   5,  2,  1),  -- Portugal dominates
('URU', 'ENG',   3,  6,  3),  -- England edge
('URU', 'FRA',   3,  7,  3),  -- France dominates
('URU', 'GER',   2,  5,  2),  -- Germany dominates
('USA', 'AUS',   8,  5,  1),  -- USA edge
('USA', 'MEX',  23, 36, 19),  -- Mexico leads all-time
ON CONFLICT (team_a_code, team_b_code) DO UPDATE
  SET h2h_wins_a = EXCLUDED.h2h_wins_a,
      h2h_wins_b = EXCLUDED.h2h_wins_b,
      h2h_draws  = EXCLUDED.h2h_draws,
      last_updated = now();
