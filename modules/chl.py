import requests
import json
import multiprocessing
from modules.helpers import listmap, flatten


api_key = 'f109cf290fcf50d4'

league_codes = {
    'qmjhl': 'lhjmq',
    'ohl': 'ohl',
    'whl': 'whl',
}


def get_json(url):
    request = requests.get(url)
    decoder = json.JSONDecoder()
    return decoder.decode(request.text)


def team_name(team):
    return team['city'] + ' ' + team['nickname']


def player_name(player):
    return (player['first_name'] + ' ' + player['last_name']) if player['player_id'] is not None else ''


def get_game_info(game_info):
    league = game_info['league']
    game_summary = get_json('http://cluster.leaguestat.com/feed/index.php?feed=gc&key={0}&client_code={1}&game_id={2}&lang_code=en&fmt=json&tab=gamesummary'.format(api_key, league_codes[league], game_info['game_id']))['GC']['Gamesummary']

    home_team = team_name(game_summary['visitor'])
    away_team = team_name(game_summary['home'])

    # 0-0 game
    if game_summary['goals'] is None:
        return []

    return listmap(game_summary['goals'], lambda goal: [
        game_info['game_id'],
        game_summary['game_date'],
        away_team,
        home_team,
        home_team if goal['home'] == '1' else away_team,
        home_team if goal['home'] == '0' else away_team,
        goal['period_id'],
        goal['time'],
        player_name(goal['goal_scorer']),
        player_name(goal['assist1_player']),
        player_name(goal['assist2_player']),
        str(len(goal['plus'])) + 'v' + str(len(goal['minus'])),
        ",".join(listmap(goal['plus'], player_name)),
        ",".join(listmap(goal['minus'], player_name)),
    ])


def get_season_stats(season, league):

    titles = [['GameID', 'date', 'visiting team', 'home team', 'GF team', 'GA team', 'period', 'time', 'scorer', 'assist1', 'assist2', 'situation', 'plus', 'minus']]

    schedule = get_json('http://cluster.leaguestat.com/feed/?feed=modulekit&view=schedule&key={0}&fmt=json&client_code={1}&lang=en&season_id={2}&team_id=undefined&league_code=&fmt=json'.format(api_key, league_codes[league], str(season)))['SiteKit']['Schedule']

    pool = multiprocessing.Pool(16)

    def add_league_to_game(game):
        game['league'] = league
        return game

    game_results = pool.map(get_game_info, map(add_league_to_game, schedule))

    return titles + flatten(game_results)
