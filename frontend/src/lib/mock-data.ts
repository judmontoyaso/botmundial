import type { Team, Match, MyPrediction, AIPrediction, GroupStanding, PredictionStats } from '@/types';

export const mockTeams: Team[] = [
  { code: "MEX", name: "Mexico", group: "A", flag: "🇲🇽", fifa_ranking: 15, confederation: "CONCACAF", stats: { played: 3, wins: 6, draws: 4, losses: 0, goals_for: 15, goals_against: 10, goal_difference: 0, points: 0 } },
  { code: "KOR", name: "South Korea", group: "A", flag: "🇰🇷", fifa_ranking: 22, confederation: "AFC", stats: { played: 3, wins: 4, draws: 3, losses: 3, goals_for: 13, goals_against: 10, goal_difference: 0, points: 0 } },
  { code: "RSA", name: "South Africa", group: "A", flag: "🇿🇦", fifa_ranking: 58, confederation: "CAF", stats: { played: 3, wins: 4, draws: 2, losses: 4, goals_for: 11, goals_against: 12, goal_difference: 0, points: 0 } },
  { code: "CZE", name: "Czechia", group: "A", flag: "🇨🇿", fifa_ranking: 36, confederation: "UEFA", stats: { played: 3, wins: 3, draws: 3, losses: 4, goals_for: 12, goals_against: 11, goal_difference: 0, points: 0 } },
  { code: "CAN", name: "Canada", group: "B", flag: "🇨🇦", fifa_ranking: 49, confederation: "CONCACAF", stats: { played: 3, wins: 6, draws: 1, losses: 3, goals_for: 12, goals_against: 13, goal_difference: 0, points: 0 } },
  { code: "SUI", name: "Switzerland", group: "B", flag: "🇨🇭", fifa_ranking: 19, confederation: "UEFA", stats: { played: 3, wins: 5, draws: 3, losses: 2, goals_for: 14, goals_against: 9, goal_difference: 0, points: 0 } },
  { code: "QAT", name: "Qatar", group: "B", flag: "🇶🇦", fifa_ranking: 34, confederation: "AFC", stats: { played: 3, wins: 5, draws: 1, losses: 4, goals_for: 12, goals_against: 15, goal_difference: 0, points: 0 } },
  { code: "BIH", name: "Bosnia-Herzegovina", group: "B", flag: "🇧🇦", fifa_ranking: 71, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 1, losses: 3, goals_for: 10, goals_against: 14, goal_difference: 0, points: 0 } },
  { code: "BRA", name: "Brazil", group: "C", flag: "🇧🇷", fifa_ranking: 5, confederation: "CONMEBOL", stats: { played: 3, wins: 7, draws: 2, losses: 1, goals_for: 20, goals_against: 7, goal_difference: 0, points: 0 } },
  { code: "MAR", name: "Morocco", group: "C", flag: "🇲🇦", fifa_ranking: 12, confederation: "CAF", stats: { played: 3, wins: 6, draws: 2, losses: 2, goals_for: 16, goals_against: 8, goal_difference: 0, points: 0 } },
  { code: "SCO", name: "Scotland", group: "C", flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿", fifa_ranking: 39, confederation: "UEFA", stats: { played: 3, wins: 7, draws: 2, losses: 1, goals_for: 11, goals_against: 13, goal_difference: 0, points: 0 } },
  { code: "HAI", name: "Haiti", group: "C", flag: "🇭🇹", fifa_ranking: 90, confederation: "CONCACAF", stats: { played: 3, wins: 3, draws: 3, losses: 4, goals_for: 9, goals_against: 18, goal_difference: 0, points: 0 } },
  { code: "USA", name: "United States", group: "D", flag: "🇺🇸", fifa_ranking: 11, confederation: "CONCACAF", stats: { played: 3, wins: 5, draws: 3, losses: 2, goals_for: 16, goals_against: 9, goal_difference: 0, points: 0 } },
  { code: "PAR", name: "Paraguay", group: "D", flag: "🇵🇾", fifa_ranking: 56, confederation: "CONMEBOL", stats: { played: 3, wins: 3, draws: 1, losses: 6, goals_for: 10, goals_against: 11, goal_difference: 0, points: 0 } },
  { code: "AUS", name: "Australia", group: "D", flag: "🇦🇺", fifa_ranking: 24, confederation: "AFC", stats: { played: 3, wins: 4, draws: 4, losses: 2, goals_for: 13, goals_against: 11, goal_difference: 0, points: 0 } },
  { code: "TUR", name: "Turkiye", group: "D", flag: "🇹🇷", fifa_ranking: 40, confederation: "UEFA", stats: { played: 3, wins: 7, draws: 3, losses: 0, goals_for: 14, goals_against: 12, goal_difference: 0, points: 0 } },
  { code: "GER", name: "Germany", group: "E", flag: "🇩🇪", fifa_ranking: 16, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 3, losses: 1, goals_for: 18, goals_against: 10, goal_difference: 0, points: 0 } },
  { code: "ECU", name: "Ecuador", group: "E", flag: "🇪🇨", fifa_ranking: 31, confederation: "CONMEBOL", stats: { played: 3, wins: 5, draws: 4, losses: 1, goals_for: 12, goals_against: 10, goal_difference: 0, points: 0 } },
  { code: "CIV", name: "Ivory Coast", group: "E", flag: "🇨🇮", fifa_ranking: 38, confederation: "CAF", stats: { played: 3, wins: 5, draws: 1, losses: 4, goals_for: 14, goals_against: 11, goal_difference: 0, points: 0 } },
  { code: "CUW", name: "Curaçao", group: "E", flag: "🇨🇼", fifa_ranking: 91, confederation: "CONCACAF", stats: { played: 3, wins: 6, draws: 3, losses: 1, goals_for: 8, goals_against: 16, goal_difference: 0, points: 0 } },
  { code: "NED", name: "Netherlands", group: "F", flag: "🇳🇱", fifa_ranking: 6, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 2, losses: 2, goals_for: 17, goals_against: 8, goal_difference: 0, points: 0 } },
  { code: "JPN", name: "Japan", group: "F", flag: "🇯🇵", fifa_ranking: 18, confederation: "AFC", stats: { played: 3, wins: 7, draws: 1, losses: 2, goals_for: 15, goals_against: 9, goal_difference: 0, points: 0 } },
  { code: "TUN", name: "Tunisia", group: "F", flag: "🇹🇳", fifa_ranking: 41, confederation: "CAF", stats: { played: 3, wins: 5, draws: 3, losses: 2, goals_for: 10, goals_against: 12, goal_difference: 0, points: 0 } },
  { code: "SWE", name: "Sweden", group: "F", flag: "🇸🇪", fifa_ranking: 26, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 1, losses: 3, goals_for: 15, goals_against: 10, goal_difference: 0, points: 0 } },
  { code: "BEL", name: "Belgium", group: "G", flag: "🇧🇪", fifa_ranking: 3, confederation: "UEFA", stats: { played: 3, wins: 5, draws: 2, losses: 3, goals_for: 18, goals_against: 8, goal_difference: 0, points: 0 } },
  { code: "IRN", name: "Iran", group: "G", flag: "🇮🇷", fifa_ranking: 20, confederation: "AFC", stats: { played: 3, wins: 3, draws: 2, losses: 5, goals_for: 13, goals_against: 10, goal_difference: 0, points: 0 } },
  { code: "EGY", name: "Egypt", group: "G", flag: "🇪🇬", fifa_ranking: 37, confederation: "CAF", stats: { played: 3, wins: 7, draws: 3, losses: 0, goals_for: 12, goals_against: 11, goal_difference: 0, points: 0 } },
  { code: "NZL", name: "New Zealand", group: "G", flag: "🇳🇿", fifa_ranking: 104, confederation: "OFC", stats: { played: 3, wins: 3, draws: 3, losses: 4, goals_for: 9, goals_against: 15, goal_difference: 0, points: 0 } },
  { code: "ESP", name: "Spain", group: "H", flag: "🇪🇸", fifa_ranking: 8, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 3, losses: 1, goals_for: 19, goals_against: 7, goal_difference: 0, points: 0 } },
  { code: "URU", name: "Uruguay", group: "H", flag: "🇺🇾", fifa_ranking: 15, confederation: "CONMEBOL", stats: { played: 3, wins: 4, draws: 4, losses: 2, goals_for: 15, goals_against: 9, goal_difference: 0, points: 0 } },
  { code: "KSA", name: "Saudi Arabia", group: "H", flag: "🇸🇦", fifa_ranking: 53, confederation: "AFC", stats: { played: 3, wins: 6, draws: 4, losses: 0, goals_for: 11, goals_against: 14, goal_difference: 0, points: 0 } },
  { code: "CPV", name: "Cape Verde", group: "H", flag: "🇨🇻", fifa_ranking: 65, confederation: "CAF", stats: { played: 3, wins: 6, draws: 1, losses: 3, goals_for: 10, goals_against: 13, goal_difference: 0, points: 0 } },
  { code: "FRA", name: "France", group: "I", flag: "🇫🇷", fifa_ranking: 2, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 4, losses: 0, goals_for: 21, goals_against: 7, goal_difference: 0, points: 0 } },
  { code: "SEN", name: "Senegal", group: "I", flag: "🇸🇳", fifa_ranking: 17, confederation: "CAF", stats: { played: 3, wins: 5, draws: 4, losses: 1, goals_for: 14, goals_against: 9, goal_difference: 0, points: 0 } },
  { code: "NOR", name: "Norway", group: "I", flag: "🇳🇴", fifa_ranking: 46, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 4, losses: 0, goals_for: 13, goals_against: 11, goal_difference: 0, points: 0 } },
  { code: "IRQ", name: "Iraq", group: "I", flag: "🇮🇶", fifa_ranking: 58, confederation: "AFC", stats: { played: 3, wins: 3, draws: 4, losses: 3, goals_for: 10, goals_against: 12, goal_difference: 0, points: 0 } },
  { code: "ARG", name: "Argentina", group: "J", flag: "🇦🇷", fifa_ranking: 1, confederation: "CONMEBOL", stats: { played: 3, wins: 4, draws: 2, losses: 4, goals_for: 20, goals_against: 6, goal_difference: 0, points: 0 } },
  { code: "AUT", name: "Austria", group: "J", flag: "🇦🇹", fifa_ranking: 25, confederation: "UEFA", stats: { played: 3, wins: 5, draws: 4, losses: 1, goals_for: 14, goals_against: 11, goal_difference: 0, points: 0 } },
  { code: "ALG", name: "Algeria", group: "J", flag: "🇩🇿", fifa_ranking: 43, confederation: "CAF", stats: { played: 3, wins: 5, draws: 4, losses: 1, goals_for: 13, goals_against: 10, goal_difference: 0, points: 0 } },
  { code: "JOR", name: "Jordan", group: "J", flag: "🇯🇴", fifa_ranking: 70, confederation: "AFC", stats: { played: 3, wins: 5, draws: 2, losses: 3, goals_for: 11, goals_against: 14, goal_difference: 0, points: 0 } },
  { code: "POR", name: "Portugal", group: "K", flag: "🇵🇹", fifa_ranking: 7, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 3, losses: 1, goals_for: 19, goals_against: 8, goal_difference: 0, points: 0 } },
  { code: "COL", name: "Colombia", group: "K", flag: "🇨🇴", fifa_ranking: 14, confederation: "CONMEBOL", stats: { played: 3, wins: 5, draws: 2, losses: 3, goals_for: 15, goals_against: 8, goal_difference: 0, points: 0 } },
  { code: "UZB", name: "Uzbekistan", group: "K", flag: "🇺🇿", fifa_ranking: 64, confederation: "AFC", stats: { played: 3, wins: 6, draws: 3, losses: 1, goals_for: 11, goals_against: 13, goal_difference: 0, points: 0 } },
  { code: "COD", name: "DR Congo", group: "K", flag: "🇨🇩", fifa_ranking: 63, confederation: "CAF", stats: { played: 3, wins: 4, draws: 2, losses: 4, goals_for: 10, goals_against: 14, goal_difference: 0, points: 0 } },
  { code: "ENG", name: "England", group: "L", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", fifa_ranking: 4, confederation: "UEFA", stats: { played: 3, wins: 6, draws: 4, losses: 0, goals_for: 18, goals_against: 7, goal_difference: 0, points: 0 } },
  { code: "CRO", name: "Croatia", group: "L", flag: "🇭🇷", fifa_ranking: 10, confederation: "UEFA", stats: { played: 3, wins: 7, draws: 3, losses: 0, goals_for: 14, goals_against: 9, goal_difference: 0, points: 0 } },
  { code: "PAN", name: "Panama", group: "L", flag: "🇵🇦", fifa_ranking: 44, confederation: "CONCACAF", stats: { played: 3, wins: 5, draws: 1, losses: 4, goals_for: 11, goals_against: 13, goal_difference: 0, points: 0 } },
  { code: "GHA", name: "Ghana", group: "L", flag: "🇬🇭", fifa_ranking: 67, confederation: "CAF", stats: { played: 3, wins: 5, draws: 2, losses: 3, goals_for: 12, goals_against: 12, goal_difference: 0, points: 0 } },
];

export const mockMatches: Match[] = [
  { id: 1, home_team: "MEX", away_team: "KOR", home_team_name: "Mexico", away_team_name: "South Korea", home_flag: "🇲🇽", away_flag: "🇰🇷", home_score: null, away_score: null, date: "2026-06-11", time: "15:00", venue: "SoFi Stadium", city: "Los Angeles", group: "A", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 2, home_team: "RSA", away_team: "CZE", home_team_name: "South Africa", away_team_name: "Czechia", home_flag: "🇿🇦", away_flag: "🇨🇿", home_score: null, away_score: null, date: "2026-06-11", time: "18:00", venue: "BC Place", city: "Vancouver", group: "A", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 3, home_team: "CAN", away_team: "SUI", home_team_name: "Canada", away_team_name: "Switzerland", home_flag: "🇨🇦", away_flag: "🇨🇭", home_score: null, away_score: null, date: "2026-06-11", time: "15:00", venue: "MetLife Stadium", city: "East Rutherford", group: "B", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 4, home_team: "QAT", away_team: "BIH", home_team_name: "Qatar", away_team_name: "Bosnia-Herzegovina", home_flag: "🇶🇦", away_flag: "🇧🇦", home_score: null, away_score: null, date: "2026-06-11", time: "18:00", venue: "Hard Rock Stadium", city: "Miami", group: "B", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 5, home_team: "BRA", away_team: "MAR", home_team_name: "Brazil", away_team_name: "Morocco", home_flag: "🇧🇷", away_flag: "🇲🇦", home_score: null, away_score: null, date: "2026-06-12", time: "15:00", venue: "NRG Stadium", city: "Houston", group: "C", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 6, home_team: "SCO", away_team: "HAI", home_team_name: "Scotland", away_team_name: "Haiti", home_flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿", away_flag: "🇭🇹", home_score: null, away_score: null, date: "2026-06-12", time: "18:00", venue: "AT&T Stadium", city: "Arlington", group: "C", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 7, home_team: "USA", away_team: "PAR", home_team_name: "United States", away_team_name: "Paraguay", home_flag: "🇺🇸", away_flag: "🇵🇾", home_score: null, away_score: null, date: "2026-06-12", time: "15:00", venue: "Mercedes-Benz Stadium", city: "Atlanta", group: "D", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 8, home_team: "AUS", away_team: "TUR", home_team_name: "Australia", away_team_name: "Turkiye", home_flag: "🇦🇺", away_flag: "🇹🇷", home_score: null, away_score: null, date: "2026-06-12", time: "18:00", venue: "Lincoln Financial Field", city: "Philadelphia", group: "D", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 9, home_team: "GER", away_team: "ECU", home_team_name: "Germany", away_team_name: "Ecuador", home_flag: "🇩🇪", away_flag: "🇪🇨", home_score: null, away_score: null, date: "2026-06-13", time: "15:00", venue: "Levi's Stadium", city: "Santa Clara", group: "E", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 10, home_team: "CIV", away_team: "CUW", home_team_name: "Ivory Coast", away_team_name: "Curaçao", home_flag: "🇨🇮", away_flag: "🇨🇼", home_score: null, away_score: null, date: "2026-06-13", time: "18:00", venue: "Lumen Field", city: "Seattle", group: "E", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 11, home_team: "NED", away_team: "JPN", home_team_name: "Netherlands", away_team_name: "Japan", home_flag: "🇳🇱", away_flag: "🇯🇵", home_score: null, away_score: null, date: "2026-06-13", time: "15:00", venue: "Arrowhead Stadium", city: "Kansas City", group: "F", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 12, home_team: "TUN", away_team: "SWE", home_team_name: "Tunisia", away_team_name: "Sweden", home_flag: "🇹🇳", away_flag: "🇸🇪", home_score: null, away_score: null, date: "2026-06-13", time: "18:00", venue: "Gillette Stadium", city: "Foxborough", group: "F", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 13, home_team: "BEL", away_team: "IRN", home_team_name: "Belgium", away_team_name: "Iran", home_flag: "🇧🇪", away_flag: "🇮🇷", home_score: null, away_score: null, date: "2026-06-14", time: "15:00", venue: "BMO Field", city: "Toronto", group: "G", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 14, home_team: "EGY", away_team: "NZL", home_team_name: "Egypt", away_team_name: "New Zealand", home_flag: "🇪🇬", away_flag: "🇳🇿", home_score: null, away_score: null, date: "2026-06-14", time: "18:00", venue: "Estadio Akron", city: "Guadalajara", group: "G", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 15, home_team: "ESP", away_team: "URU", home_team_name: "Spain", away_team_name: "Uruguay", home_flag: "🇪🇸", away_flag: "🇺🇾", home_score: null, away_score: null, date: "2026-06-14", time: "15:00", venue: "Estadio BBVA", city: "Monterrey", group: "H", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 16, home_team: "KSA", away_team: "CPV", home_team_name: "Saudi Arabia", away_team_name: "Cape Verde", home_flag: "🇸🇦", away_flag: "🇨🇻", home_score: null, away_score: null, date: "2026-06-14", time: "18:00", venue: "Estadio Azteca", city: "Mexico City", group: "H", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 17, home_team: "FRA", away_team: "SEN", home_team_name: "France", away_team_name: "Senegal", home_flag: "🇫🇷", away_flag: "🇸🇳", home_score: null, away_score: null, date: "2026-06-15", time: "15:00", venue: "SoFi Stadium", city: "Los Angeles", group: "I", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 18, home_team: "NOR", away_team: "IRQ", home_team_name: "Norway", away_team_name: "Iraq", home_flag: "🇳🇴", away_flag: "🇮🇶", home_score: null, away_score: null, date: "2026-06-15", time: "18:00", venue: "BC Place", city: "Vancouver", group: "I", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 19, home_team: "ARG", away_team: "AUT", home_team_name: "Argentina", away_team_name: "Austria", home_flag: "🇦🇷", away_flag: "🇦🇹", home_score: null, away_score: null, date: "2026-06-15", time: "15:00", venue: "MetLife Stadium", city: "East Rutherford", group: "J", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 20, home_team: "ALG", away_team: "JOR", home_team_name: "Algeria", away_team_name: "Jordan", home_flag: "🇩🇿", away_flag: "🇯🇴", home_score: null, away_score: null, date: "2026-06-15", time: "18:00", venue: "Hard Rock Stadium", city: "Miami", group: "J", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 21, home_team: "POR", away_team: "COL", home_team_name: "Portugal", away_team_name: "Colombia", home_flag: "🇵🇹", away_flag: "🇨🇴", home_score: null, away_score: null, date: "2026-06-16", time: "15:00", venue: "NRG Stadium", city: "Houston", group: "K", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 22, home_team: "UZB", away_team: "COD", home_team_name: "Uzbekistan", away_team_name: "DR Congo", home_flag: "🇺🇿", away_flag: "🇨🇩", home_score: null, away_score: null, date: "2026-06-16", time: "18:00", venue: "AT&T Stadium", city: "Arlington", group: "K", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 23, home_team: "ENG", away_team: "CRO", home_team_name: "England", away_team_name: "Croatia", home_flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", away_flag: "🇭🇷", home_score: null, away_score: null, date: "2026-06-16", time: "15:00", venue: "Mercedes-Benz Stadium", city: "Atlanta", group: "L", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 24, home_team: "PAN", away_team: "GHA", home_team_name: "Panama", away_team_name: "Ghana", home_flag: "🇵🇦", away_flag: "🇬🇭", home_score: null, away_score: null, date: "2026-06-16", time: "18:00", venue: "Lincoln Financial Field", city: "Philadelphia", group: "L", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 25, home_team: "MEX", away_team: "RSA", home_team_name: "Mexico", away_team_name: "South Africa", home_flag: "🇲🇽", away_flag: "🇿🇦", home_score: null, away_score: null, date: "2026-06-17", time: "15:00", venue: "Levi's Stadium", city: "Santa Clara", group: "A", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 26, home_team: "CZE", away_team: "KOR", home_team_name: "Czechia", away_team_name: "South Korea", home_flag: "🇨🇿", away_flag: "🇰🇷", home_score: null, away_score: null, date: "2026-06-17", time: "18:00", venue: "Lumen Field", city: "Seattle", group: "A", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 27, home_team: "CAN", away_team: "QAT", home_team_name: "Canada", away_team_name: "Qatar", home_flag: "🇨🇦", away_flag: "🇶🇦", home_score: null, away_score: null, date: "2026-06-17", time: "15:00", venue: "Arrowhead Stadium", city: "Kansas City", group: "B", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 28, home_team: "BIH", away_team: "SUI", home_team_name: "Bosnia-Herzegovina", away_team_name: "Switzerland", home_flag: "🇧🇦", away_flag: "🇨🇭", home_score: null, away_score: null, date: "2026-06-17", time: "18:00", venue: "Gillette Stadium", city: "Foxborough", group: "B", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 29, home_team: "BRA", away_team: "SCO", home_team_name: "Brazil", away_team_name: "Scotland", home_flag: "🇧🇷", away_flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿", home_score: null, away_score: null, date: "2026-06-18", time: "15:00", venue: "BMO Field", city: "Toronto", group: "C", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 30, home_team: "HAI", away_team: "MAR", home_team_name: "Haiti", away_team_name: "Morocco", home_flag: "🇭🇹", away_flag: "🇲🇦", home_score: null, away_score: null, date: "2026-06-18", time: "18:00", venue: "Estadio Akron", city: "Guadalajara", group: "C", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 31, home_team: "USA", away_team: "AUS", home_team_name: "United States", away_team_name: "Australia", home_flag: "🇺🇸", away_flag: "🇦🇺", home_score: null, away_score: null, date: "2026-06-18", time: "15:00", venue: "Estadio BBVA", city: "Monterrey", group: "D", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 32, home_team: "TUR", away_team: "PAR", home_team_name: "Turkiye", away_team_name: "Paraguay", home_flag: "🇹🇷", away_flag: "🇵🇾", home_score: null, away_score: null, date: "2026-06-18", time: "18:00", venue: "Estadio Azteca", city: "Mexico City", group: "D", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 33, home_team: "GER", away_team: "CIV", home_team_name: "Germany", away_team_name: "Ivory Coast", home_flag: "🇩🇪", away_flag: "🇨🇮", home_score: null, away_score: null, date: "2026-06-19", time: "15:00", venue: "SoFi Stadium", city: "Los Angeles", group: "E", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 34, home_team: "CUW", away_team: "ECU", home_team_name: "Curaçao", away_team_name: "Ecuador", home_flag: "🇨🇼", away_flag: "🇪🇨", home_score: null, away_score: null, date: "2026-06-19", time: "18:00", venue: "BC Place", city: "Vancouver", group: "E", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 35, home_team: "NED", away_team: "TUN", home_team_name: "Netherlands", away_team_name: "Tunisia", home_flag: "🇳🇱", away_flag: "🇹🇳", home_score: null, away_score: null, date: "2026-06-19", time: "15:00", venue: "MetLife Stadium", city: "East Rutherford", group: "F", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 36, home_team: "SWE", away_team: "JPN", home_team_name: "Sweden", away_team_name: "Japan", home_flag: "🇸🇪", away_flag: "🇯🇵", home_score: null, away_score: null, date: "2026-06-19", time: "18:00", venue: "Hard Rock Stadium", city: "Miami", group: "F", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 37, home_team: "BEL", away_team: "EGY", home_team_name: "Belgium", away_team_name: "Egypt", home_flag: "🇧🇪", away_flag: "🇪🇬", home_score: null, away_score: null, date: "2026-06-20", time: "15:00", venue: "NRG Stadium", city: "Houston", group: "G", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 38, home_team: "NZL", away_team: "IRN", home_team_name: "New Zealand", away_team_name: "Iran", home_flag: "🇳🇿", away_flag: "🇮🇷", home_score: null, away_score: null, date: "2026-06-20", time: "18:00", venue: "AT&T Stadium", city: "Arlington", group: "G", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 39, home_team: "ESP", away_team: "KSA", home_team_name: "Spain", away_team_name: "Saudi Arabia", home_flag: "🇪🇸", away_flag: "🇸🇦", home_score: null, away_score: null, date: "2026-06-20", time: "15:00", venue: "Mercedes-Benz Stadium", city: "Atlanta", group: "H", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 40, home_team: "CPV", away_team: "URU", home_team_name: "Cape Verde", away_team_name: "Uruguay", home_flag: "🇨🇻", away_flag: "🇺🇾", home_score: null, away_score: null, date: "2026-06-20", time: "18:00", venue: "Lincoln Financial Field", city: "Philadelphia", group: "H", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 41, home_team: "FRA", away_team: "NOR", home_team_name: "France", away_team_name: "Norway", home_flag: "🇫🇷", away_flag: "🇳🇴", home_score: null, away_score: null, date: "2026-06-21", time: "15:00", venue: "Levi's Stadium", city: "Santa Clara", group: "I", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 42, home_team: "IRQ", away_team: "SEN", home_team_name: "Iraq", away_team_name: "Senegal", home_flag: "🇮🇶", away_flag: "🇸🇳", home_score: null, away_score: null, date: "2026-06-21", time: "18:00", venue: "Lumen Field", city: "Seattle", group: "I", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 43, home_team: "ARG", away_team: "ALG", home_team_name: "Argentina", away_team_name: "Algeria", home_flag: "🇦🇷", away_flag: "🇩🇿", home_score: null, away_score: null, date: "2026-06-21", time: "15:00", venue: "Arrowhead Stadium", city: "Kansas City", group: "J", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 44, home_team: "JOR", away_team: "AUT", home_team_name: "Jordan", away_team_name: "Austria", home_flag: "🇯🇴", away_flag: "🇦🇹", home_score: null, away_score: null, date: "2026-06-21", time: "18:00", venue: "Gillette Stadium", city: "Foxborough", group: "J", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 45, home_team: "POR", away_team: "UZB", home_team_name: "Portugal", away_team_name: "Uzbekistan", home_flag: "🇵🇹", away_flag: "🇺🇿", home_score: null, away_score: null, date: "2026-06-22", time: "15:00", venue: "BMO Field", city: "Toronto", group: "K", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 46, home_team: "COD", away_team: "COL", home_team_name: "DR Congo", away_team_name: "Colombia", home_flag: "🇨🇩", away_flag: "🇨🇴", home_score: null, away_score: null, date: "2026-06-22", time: "18:00", venue: "Estadio Akron", city: "Guadalajara", group: "K", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 47, home_team: "ENG", away_team: "PAN", home_team_name: "England", away_team_name: "Panama", home_flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", away_flag: "🇵🇦", home_score: null, away_score: null, date: "2026-06-22", time: "15:00", venue: "Estadio BBVA", city: "Monterrey", group: "L", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 48, home_team: "GHA", away_team: "CRO", home_team_name: "Ghana", away_team_name: "Croatia", home_flag: "🇬🇭", away_flag: "🇭🇷", home_score: null, away_score: null, date: "2026-06-22", time: "18:00", venue: "Estadio Azteca", city: "Mexico City", group: "L", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 49, home_team: "CZE", away_team: "MEX", home_team_name: "Czechia", away_team_name: "Mexico", home_flag: "🇨🇿", away_flag: "🇲🇽", home_score: null, away_score: null, date: "2026-06-23", time: "15:00", venue: "SoFi Stadium", city: "Los Angeles", group: "A", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 50, home_team: "KOR", away_team: "RSA", home_team_name: "South Korea", away_team_name: "South Africa", home_flag: "🇰🇷", away_flag: "🇿🇦", home_score: null, away_score: null, date: "2026-06-23", time: "18:00", venue: "BC Place", city: "Vancouver", group: "A", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 51, home_team: "BIH", away_team: "CAN", home_team_name: "Bosnia-Herzegovina", away_team_name: "Canada", home_flag: "🇧🇦", away_flag: "🇨🇦", home_score: null, away_score: null, date: "2026-06-23", time: "15:00", venue: "MetLife Stadium", city: "East Rutherford", group: "B", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 52, home_team: "SUI", away_team: "QAT", home_team_name: "Switzerland", away_team_name: "Qatar", home_flag: "🇨🇭", away_flag: "🇶🇦", home_score: null, away_score: null, date: "2026-06-23", time: "18:00", venue: "Hard Rock Stadium", city: "Miami", group: "B", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 53, home_team: "HAI", away_team: "BRA", home_team_name: "Haiti", away_team_name: "Brazil", home_flag: "🇭🇹", away_flag: "🇧🇷", home_score: null, away_score: null, date: "2026-06-24", time: "15:00", venue: "NRG Stadium", city: "Houston", group: "C", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 54, home_team: "MAR", away_team: "SCO", home_team_name: "Morocco", away_team_name: "Scotland", home_flag: "🇲🇦", away_flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿", home_score: null, away_score: null, date: "2026-06-24", time: "18:00", venue: "AT&T Stadium", city: "Arlington", group: "C", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 55, home_team: "TUR", away_team: "USA", home_team_name: "Turkiye", away_team_name: "United States", home_flag: "🇹🇷", away_flag: "🇺🇸", home_score: null, away_score: null, date: "2026-06-24", time: "15:00", venue: "Mercedes-Benz Stadium", city: "Atlanta", group: "D", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 56, home_team: "PAR", away_team: "AUS", home_team_name: "Paraguay", away_team_name: "Australia", home_flag: "🇵🇾", away_flag: "🇦🇺", home_score: null, away_score: null, date: "2026-06-24", time: "18:00", venue: "Lincoln Financial Field", city: "Philadelphia", group: "D", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 57, home_team: "CUW", away_team: "GER", home_team_name: "Curaçao", away_team_name: "Germany", home_flag: "🇨🇼", away_flag: "🇩🇪", home_score: null, away_score: null, date: "2026-06-25", time: "15:00", venue: "Levi's Stadium", city: "Santa Clara", group: "E", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 58, home_team: "ECU", away_team: "CIV", home_team_name: "Ecuador", away_team_name: "Ivory Coast", home_flag: "🇪🇨", away_flag: "🇨🇮", home_score: null, away_score: null, date: "2026-06-25", time: "18:00", venue: "Lumen Field", city: "Seattle", group: "E", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 59, home_team: "SWE", away_team: "NED", home_team_name: "Sweden", away_team_name: "Netherlands", home_flag: "🇸🇪", away_flag: "🇳🇱", home_score: null, away_score: null, date: "2026-06-25", time: "15:00", venue: "Arrowhead Stadium", city: "Kansas City", group: "F", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 60, home_team: "JPN", away_team: "TUN", home_team_name: "Japan", away_team_name: "Tunisia", home_flag: "🇯🇵", away_flag: "🇹🇳", home_score: null, away_score: null, date: "2026-06-25", time: "18:00", venue: "Gillette Stadium", city: "Foxborough", group: "F", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 61, home_team: "NZL", away_team: "BEL", home_team_name: "New Zealand", away_team_name: "Belgium", home_flag: "🇳🇿", away_flag: "🇧🇪", home_score: null, away_score: null, date: "2026-06-26", time: "15:00", venue: "BMO Field", city: "Toronto", group: "G", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 62, home_team: "IRN", away_team: "EGY", home_team_name: "Iran", away_team_name: "Egypt", home_flag: "🇮🇷", away_flag: "🇪🇬", home_score: null, away_score: null, date: "2026-06-26", time: "18:00", venue: "Estadio Akron", city: "Guadalajara", group: "G", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 63, home_team: "CPV", away_team: "ESP", home_team_name: "Cape Verde", away_team_name: "Spain", home_flag: "🇨🇻", away_flag: "🇪🇸", home_score: null, away_score: null, date: "2026-06-26", time: "15:00", venue: "Estadio BBVA", city: "Monterrey", group: "H", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 64, home_team: "URU", away_team: "KSA", home_team_name: "Uruguay", away_team_name: "Saudi Arabia", home_flag: "🇺🇾", away_flag: "🇸🇦", home_score: null, away_score: null, date: "2026-06-26", time: "18:00", venue: "Estadio Azteca", city: "Mexico City", group: "H", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 65, home_team: "IRQ", away_team: "FRA", home_team_name: "Iraq", away_team_name: "France", home_flag: "🇮🇶", away_flag: "🇫🇷", home_score: null, away_score: null, date: "2026-06-27", time: "15:00", venue: "SoFi Stadium", city: "Los Angeles", group: "I", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 66, home_team: "SEN", away_team: "NOR", home_team_name: "Senegal", away_team_name: "Norway", home_flag: "🇸🇳", away_flag: "🇳🇴", home_score: null, away_score: null, date: "2026-06-27", time: "18:00", venue: "BC Place", city: "Vancouver", group: "I", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 67, home_team: "JOR", away_team: "ARG", home_team_name: "Jordan", away_team_name: "Argentina", home_flag: "🇯🇴", away_flag: "🇦🇷", home_score: null, away_score: null, date: "2026-06-27", time: "15:00", venue: "MetLife Stadium", city: "East Rutherford", group: "J", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 68, home_team: "AUT", away_team: "ALG", home_team_name: "Austria", away_team_name: "Algeria", home_flag: "🇦🇹", away_flag: "🇩🇿", home_score: null, away_score: null, date: "2026-06-27", time: "18:00", venue: "Hard Rock Stadium", city: "Miami", group: "J", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 69, home_team: "COD", away_team: "POR", home_team_name: "DR Congo", away_team_name: "Portugal", home_flag: "🇨🇩", away_flag: "🇵🇹", home_score: null, away_score: null, date: "2026-06-28", time: "15:00", venue: "NRG Stadium", city: "Houston", group: "K", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 70, home_team: "COL", away_team: "UZB", home_team_name: "Colombia", away_team_name: "Uzbekistan", home_flag: "🇨🇴", away_flag: "🇺🇿", home_score: null, away_score: null, date: "2026-06-28", time: "18:00", venue: "AT&T Stadium", city: "Arlington", group: "K", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 71, home_team: "GHA", away_team: "ENG", home_team_name: "Ghana", away_team_name: "England", home_flag: "🇬🇭", away_flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", home_score: null, away_score: null, date: "2026-06-28", time: "15:00", venue: "Mercedes-Benz Stadium", city: "Atlanta", group: "L", stage: 'group', status: "scheduled", matchday: 1 },
  { id: 72, home_team: "CRO", away_team: "PAN", home_team_name: "Croatia", away_team_name: "Panama", home_flag: "🇭🇷", away_flag: "🇵🇦", home_score: null, away_score: null, date: "2026-06-28", time: "18:00", venue: "Lincoln Financial Field", city: "Philadelphia", group: "L", stage: 'group', status: "scheduled", matchday: 1 },
];


export const mockAIPredictions: AIPrediction[] = [
  {
    match_id: 1,
    home_team_name: 'Mexico',
    away_team_name: 'South Korea',
    home_flag: '🇲🇽',
    away_flag: '🇰🇷',
    predicted_home: 2,
    predicted_away: 1,
    home_win_prob: 0.55,
    draw_prob: 0.25,
    away_win_prob: 0.20,
    confidence: 0.70,
    analysis: 'Análisis preliminar de DeepSeek: México domina el historial reciente frente a rivales asiáticos, pero la velocidad en transición de Corea del Sur será un desafío. Se espera un partido ajustado donde el mediocampo mexicano haga la diferencia.',
    factors: [
      { name: 'Ranking', impact: 'positive', description: 'México #15 vs Corea #22', team: 'MEX' },
      { name: 'Velocidad', impact: 'negative', description: 'Corea del Sur es letal en contraataque', team: 'KOR' }
    ],
    date: '2026-06-11',
  },
  {
    match_id: 9,
    home_team_name: 'Brazil',
    away_team_name: 'Morocco',
    home_flag: '🇧🇷',
    away_flag: '🇲🇦',
    predicted_home: 3,
    predicted_away: 1,
    home_win_prob: 0.65,
    draw_prob: 0.20,
    away_win_prob: 0.15,
    confidence: 0.85,
    analysis: 'Análisis preliminar de DeepSeek: Brasil llega como uno de los máximos favoritos. Aunque Marruecos es defensivamente sólido, la calidad ofensiva de la delantera brasileña terminará rompiendo el cerco defensivo en la segunda mitad.',
    factors: [
      { name: 'Ataque', impact: 'positive', description: 'Brasil promedia 2.0 goles por partido', team: 'BRA' },
      { name: 'Defensa', impact: 'neutral', description: 'Marruecos concede muy pocos goles', team: 'MAR' }
    ],
    date: '2026-06-13',
  }
];

export const mockMyPredictions: MyPrediction[] = [];

function buildGroupStandings(): GroupStanding[] {
  const groups = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
  return groups.map(group => {
    const teamsInGroup = mockTeams
      .filter(t => t.group === group)
      .sort((a, b) => {
        if (b.stats.points !== a.stats.points) return b.stats.points - a.stats.points;
        if (b.stats.goal_difference !== a.stats.goal_difference) return b.stats.goal_difference - a.stats.goal_difference;
        return b.stats.goals_for - a.stats.goals_for;
      });

    return {
      group,
      teams: teamsInGroup.map((team, idx) => ({
        position: idx + 1,
        team_code: team.code,
        team_name: team.name,
        flag: team.flag,
        played: team.stats.played,
        wins: team.stats.wins,
        draws: team.stats.draws,
        losses: team.stats.losses,
        goals_for: team.stats.goals_for,
        goals_against: team.stats.goals_against,
        goal_difference: team.stats.goal_difference,
        points: team.stats.points,
      })),
    };
  });
}

export const mockGroupStandings: GroupStanding[] = buildGroupStandings();

export const mockPredictionStats: PredictionStats = {
  total_predictions: 0,
  exact_scores: 0,
  correct_winner: 0,
  wrong: 0,
  total_points: 0,
  accuracy: 0,
  points_history: [],
};

export function getUpcomingMatches(count: number = 5): Match[] {
  return mockMatches
    .filter(m => m.status === 'scheduled')
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(0, count);
}
export function getFinishedMatches(): Match[] { return mockMatches.filter(m => m.status === 'finished'); }
export function getTeamByCode(code: string): Team | undefined { return mockTeams.find(t => t.code === code); }
export function getMatchesByGroup(group: string): Match[] { return mockMatches.filter(m => m.group === group); }
export function getAIPredictionForMatch(matchId: number): AIPrediction | undefined { return mockAIPredictions.find(p => p.match_id === matchId); }
