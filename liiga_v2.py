import sys
import datetime
import requests
from os import path
from urllib.parse import urlencode

from modules import helpers

API_URL = 'https://liiga.fi/api/v1/'

SEASON_TYPES = {
    'preseason': 'valmistavat_ottelut',
    'season': 'runkosarja',
    'playoffs': 'playoffs'
}


def get_schedule(season: str, season_type: str):
    teams_url = path.join(API_URL, 'teams', 'info')
    teams = requests.get(teams_url).json()['teams']

    games_url = path.join(API_URL, 'games') + '?' + urlencode({'tournament': SEASON_TYPES[season_type], 'season': season})
    all_games = requests.get(games_url).json()

    result = []
    for game in all_games:
        home_team = teams[game['homeTeam']['teamId']]['name']
        away_team = teams[game['awayTeam']['teamId']]['name']
        home_goals = game['homeTeam']['goals']
        away_goals = game['awayTeam']['goals']
        if home_goals == away_goals:
            raise ValueError('Unexpected: game ended with a tied score.')

        game_url = path.join(API_URL, 'games', season, str(game['id'])) + '?' + urlencode({'tournament': SEASON_TYPES[season_type]})
        game_info = requests.get(game_url).json()
        home_roster, away_roster = (
            ', '.join(f"{player['firstName'].title()} {player['lastName'].title()}" for player in game_info[roster])
            for roster in ['homeTeamPlayers', 'awayTeamPlayers']
        )

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
            'Visitor Roster': away_roster,
            'Home Roster': home_roster,
            'Total Time': game['gameTime'] / 60,
        })

    helpers.export_dict_array_to_csv(result, f'Liiga-{season}-{season_type}-schedule.csv')


def convert_toi(toi):
    minutes = toi // 60
    seconds = toi % 60
    return f'{str(minutes).zfill(2)}:{str(seconds).zfill(2)}'


def get_birthplace(player):
    birth_locality = player['birth_locality']
    if not birth_locality:
        return ''
    return ", ".join([
        birth_locality['name'],
        birth_locality['country']['code']
    ])


def get_players(season_raw: str, season_type: str):
    season = str(int(season_raw) - 1)  # wtf Liiga, different season representation for players vs games??
    players_url = path.join(API_URL, 'players', 'stats', season, SEASON_TYPES[season_type])
    all_players = requests.get(players_url).json()

    result = []
    for player in all_players:
        result.append({
            'Player ID': player['fiha_id'],
            'Player': player['full_name'],
            'Position': player['current_position'],
            'Season': season,
            'Season Type': season_type,
            'League': 'Liiga',
            'Team': player['team'],
            'Birthdate': player['date_of_birth'],
            'Birthplace': get_birthplace(player),
            'Height': player['height'],
            'Weight': player['weight'],
            'Shoots': player['handedness'],
            'GP': player['games'],
            'Shots on Goal': player['shots_into_goal'],
            'TOI': convert_toi(player['time_on_ice_avg']),
        })

    helpers.export_dict_array_to_csv(result, f'Liiga-{season_raw}-{season_type}-players.csv')


if __name__ == '__main__':
    _, season, season_type = sys.argv
    get_schedule(season, season_type)
    get_players(season, season_type)
