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
NO_GOAL = 'VT0'
POWERPLAY = 'YV'
FIVE_ON_THREE = 'YV2'
UNKNOWN = ['SR', 'VT', 'AV', 'RL0', 'VL', 'TM', 'IM']


def convert_toi(toi):
    minutes = toi // 60
    seconds = toi % 60
    return f'{str(minutes).zfill(2)}:{str(seconds).zfill(2)}'


def get_situation(goal_types):
    if not goal_types:
        return ''
    if POWERPLAY in goal_types or FIVE_ON_THREE in goal_types:
        return 'PP'
    if any(unknown_type in goal_types for unknown_type in UNKNOWN):
        return ''
    return ''


def get_strength(goal_types):
    if not goal_types:
        return '5v5'
    if POWERPLAY in goal_types:
        return '5v4'
    if FIVE_ON_THREE in goal_types:
        return '5v3'
    if any(unknown_type in goal_types for unknown_type in UNKNOWN):
        return ''
    return ''


def get_goals_from_game_info(
        game_info,
        goal_events,
        scoring_team,
        scored_against_team,
        players_by_id,
        players_by_jersey_number,
        opposing_players_by_jersey_number
):

    return [{
        **game_info,
        'GF Team': scoring_team,
        'GA Team': scored_against_team,
        'Period': str(event['period']),
        'Time': convert_toi(event['gameTime'] - (event['period'] - 1) * 20),
        'Scorer': players_by_id[event['scorerPlayerId']],
        'Assist1': players_by_id[event['assistantPlayerIds'][0]] if len(event['assistantPlayerIds']) >= 1 else '',
        'Assist2': players_by_id[event['assistantPlayerIds'][1]] if len(event['assistantPlayerIds']) >= 2 else '',
        'Strength': get_strength(event['goalTypes']),
        'Plus': ' '.join(players_by_jersey_number[player] for player in event['plusPlayerIds'].split(' ')) if event['plusPlayerIds'] else '',
        'Minus': ' '.join(opposing_players_by_jersey_number[player] for player in event['minusPlayerIds'].split(' ')) if event['minusPlayerIds'] else '',
        'Situation': get_situation(event['goalTypes']),
    } for event in goal_events if NO_GOAL not in event['goalTypes']]


def get_schedule(season: str, season_type: str):
    teams_url = path.join(API_URL, 'teams', 'info')
    teams = requests.get(teams_url).json()['teams']

    games_url = path.join(API_URL, 'games') + '?' + urlencode({'tournament': SEASON_TYPES[season_type], 'season': season})
    all_games = requests.get(games_url).json()

    games_result = []
    goals_result = []

    for game in all_games:

        home_team = teams[game['homeTeam']['teamId']]['name']
        away_team = teams[game['awayTeam']['teamId']]['name']
        home_goals = game['homeTeam']['goals']
        away_goals = game['awayTeam']['goals']
        if home_goals == away_goals:
            raise ValueError('Unexpected: game ended with a tied score.')

        game_url = path.join(API_URL, 'games', season, str(game['id'])) + '?' + urlencode({'tournament': SEASON_TYPES[season_type]})
        game_info = requests.get(game_url).json()
        home_roster_by_jersey, away_roster_by_jersey = (
            {str(player['jersey']): f"{player['firstName'].title()} {player['lastName'].title()}" for player in game_info[roster]}
            for roster in ['homeTeamPlayers', 'awayTeamPlayers']
        )
        home_roster_by_id, away_roster_by_id = (
            {player['id']: f"{player['firstName'].title()} {player['lastName'].title()}" for player in game_info[roster]}
            for roster in ['homeTeamPlayers', 'awayTeamPlayers']
        )

        common_game_info = {
            'Season': season,
            'Season Type': season_type,
            'League': 'Liiga',
            'GameID': f"{season}{str(game['id']).zfill(3)}",
            'Date': datetime.datetime.fromisoformat((game['start'].replace('Z', '+00:00'))).date().isoformat(),
        }

        games_result.append({
            **common_game_info,
            'Visiting Team': home_team,
            'Home Team': away_team,
            'Visitor GF': away_goals,
            'Home GF': home_goals,
            'Winning Team': home_team if home_goals > away_goals else away_team,
            'Losing Team': away_team if home_goals > away_goals else home_team,
            'Visitor Roster': ', '.join(away_roster_by_jersey.values()),
            'Home Roster': ', '.join(home_roster_by_jersey.values()),
            'Total Time': game['gameTime'] / 60,
        })

        goals_result.extend(get_goals_from_game_info(
            common_game_info,
            game_info['game']['awayTeam']['goalEvents'],
            away_team,
            home_team,
            away_roster_by_id,
            away_roster_by_jersey,
            home_roster_by_jersey
        ))
        goals_result.extend(get_goals_from_game_info(
            common_game_info,
            game_info['game']['homeTeam']['goalEvents'],
            away_team,
            home_team,
            home_roster_by_id,
            home_roster_by_jersey,
            away_roster_by_jersey
        ))

    helpers.export_dict_array_to_csv(games_result, f'Liiga-{season}-{season_type}-schedule.csv')
    helpers.export_dict_array_to_csv(goals_result, f'Liiga-{season}-{season_type}-goals.csv')


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
