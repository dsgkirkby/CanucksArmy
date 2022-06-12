import sys
import datetime
import requests
from urllib.parse import urljoin, urlencode

from modules import helpers

API_URL = 'https://liiga.fi/api/v1/'

SEASON_TYPES = {
    'preseason': 'valmistavat_ottelut',
    'season': 'runkosarja',
    'playoffs': 'playoffs'
}


def get_schedule(season: str, season_type: str):
    teams_url = urljoin(API_URL, 'teams/info')
    teams = requests.get(teams_url).json()['teams']

    games_url = urljoin(API_URL, 'games') + '?' + urlencode({'tournament': SEASON_TYPES[season_type], 'season': season})
    all_games = requests.get(games_url).json()

    result = []
    for game in all_games:
        home_team = teams[game['homeTeam']['teamId']]['name']
        away_team = teams[game['awayTeam']['teamId']]['name']
        home_goals = game['homeTeam']['goals']
        away_goals = game['awayTeam']['goals']
        if home_goals == away_goals:
            raise ValueError('Unexpected: game ended with a tied score.')
        result.append({
            'Season': season,
            'Season Type': season_type,
            'League': 'Liiga',
            'GameID': f"{season}{str(game['id']).zfill(3)}",
            'Date': datetime.datetime.fromisoformat((game['start'].replace('Z', '+00:00'))).date().isoformat(),
            'Visiting Team': home_team,
            'Home Team': away_team,
            'Visitor GF': away_goals,
            'Home GF': home_goals,
            'Winning Team': home_team if home_goals > away_goals else away_team,
            'Losing Team': away_team if home_goals > away_goals else home_team,
            # TODO: rosters
            # TODO: shots
            'Total Time': game['gameTime'] / 60,
        })

    helpers.export_dict_array_to_csv(result, f'Liiga-{season}-{season_type}-schedule.csv')


if __name__ == '__main__':
    get_schedule(sys.argv[1], sys.argv[2])
