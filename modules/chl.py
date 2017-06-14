import multiprocessing
from modules.helpers import listmap, flatten, strip_extra_spaces, get_json


api_key = 'f109cf290fcf50d4'

league_codes = {
    'qmjhl': 'lhjmq',
    'ohl': 'ohl',
    'whl': 'whl',
}


def team_name(team):
    return strip_extra_spaces(team['city'] + ' ' + team['nickname'])


def team_roster(team_lineup):
    return ",".join(listmap(
        team_lineup['goalies'] + team_lineup['players'],
        player_name
    ))


def player_name(player):
    return strip_extra_spaces((player['first_name'] + ' ' + player['last_name']) if player['player_id'] is not None else '')


def get_game_info(game_info):
    league = game_info['league']
    game_summary = get_json('http://cluster.leaguestat.com/feed/index.php?feed=gc&key={0}&client_code={1}&game_id={2}&lang_code=en&fmt=json&tab=gamesummary'.format(api_key, league_codes[league], game_info['game_id']))['GC']['Gamesummary']

    home_team = team_name(game_summary['visitor'])
    away_team = team_name(game_summary['home'])

    home_roster = team_roster(game_summary['home_team_lineup']) if type(game_summary['home_team_lineup']) is not list else ''
    away_roster = team_roster(game_summary['visitor_team_lineup']) if type(game_summary['visitor_team_lineup']) is not list else ''

    # 0-0 game
    if game_summary['goals'] is None:
        return []

    home_score = 0
    away_score = 0

    def convert_goal(goal):
        nonlocal home_score, away_score

        is_home_goal = goal['home'] == '1'
        to_return = [
            game_info['season'],
            game_info['league'],
            game_info['game_id'],
            game_summary['game_date'],
            away_team,
            home_team,
            home_team if is_home_goal else away_team,
            home_team if not is_home_goal else away_team,
            goal['period_id'],
            goal['time'],
            player_name(goal['goal_scorer']),
            player_name(goal['assist1_player']),
            player_name(goal['assist2_player']),
            home_score - away_score if is_home_goal else away_score - home_score,
            (str(len(goal['plus'])) + 'v' + str(len(goal['minus']))) if len(goal['plus']) > 0 else '5v4',
            ",".join(listmap(goal['plus'], player_name)),
            ",".join(listmap(goal['minus'], player_name)),
            home_roster if is_home_goal else away_roster,
            home_roster if not is_home_goal else away_roster,
        ]
        if is_home_goal:
            home_score += 1
        else:
            away_score += 1
        return to_return

    return listmap(game_summary['goals'], convert_goal)


def get_season_stats(season, league, results_array: list=None):
    if results_array is None:
        results_array = [[
            'Season',
            'League',
            'GameID',
            'date',
            'visiting team',
            'home team',
            'GF team',
            'GA team',
            'period',
            'time',
            'scorer',
            'assist1',
            'assist2',
            'score state',
            'situation',
            'plus',
            'minus',
            'GF team roster',
            'GA team roster'
        ]]

    schedule = get_json('http://cluster.leaguestat.com/feed/?feed=modulekit&view=schedule&key={0}&fmt=json&client_code={1}&lang=en&season_id={2}&team_id=undefined&league_code=&fmt=json'.format(api_key, league_codes[league], season['season_id']))['SiteKit']['Schedule']

    pool = multiprocessing.Pool(4)

    def add_league_to_game(game):
        game['league'] = league
        game['season'] = season['end_date'][0:4]
        return game

    game_results = pool.map(get_game_info, map(add_league_to_game, schedule))

    results_array += flatten(game_results)
