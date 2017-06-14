import multiprocessing
from modules.helpers import listmap, flatten, strip_extra_spaces, get_json


SECONDS_PER_MINUTE = 60


def get_league_code(league):
    if league == 'qmjhl':
        return league[::-1]
    else:
        return league


def get_api_key(league):
    if league == 'ahl':
        return 'c680916776709578'
    else:
        return 'f109cf290fcf50d4'


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
    game_summary = get_json('http://cluster.leaguestat.com/feed/index.php?feed=gc&key={0}&client_code={1}&game_id={2}&lang_code=en&fmt=json&tab=gamesummary'.format(get_api_key(league), get_league_code(league), game_info['game_id']))['GC']['Gamesummary']

    home_team = team_name(game_summary['home'])
    away_team = team_name(game_summary['visitor'])

    home_roster = team_roster(game_summary['home_team_lineup']) if type(game_summary['home_team_lineup']) is not list else ''
    away_roster = team_roster(game_summary['visitor_team_lineup']) if type(game_summary['visitor_team_lineup']) is not list else ''

    is_playoff_game = game_info['playoff'] == '1'
    season = game_info['season']
    season_type = 'Playoffs' if is_playoff_game else 'Season'
    game_id = game_info['game_id']
    date = game_summary['meta']['date_played']
    home_goals = game_summary['totalGoals']['visitor']
    away_goals = game_summary['totalGoals']['home']
    end_clock = game_summary['meta']['game_clock']
    end_period = game_summary['meta']['period']
    regular_icetime_seconds = 3 * 20 * SECONDS_PER_MINUTE
    overtime_icetime_seconds = (
        (int(end_period) - 3)  # Number of OT periods
        * (20 if is_playoff_game else 5)  # Length of OT period
        * SECONDS_PER_MINUTE
        - (int(end_clock[3:5]) * SECONDS_PER_MINUTE + int(end_clock[6:8]))  # Remaining time if OT goal was scored
    )
    total_icetime_seconds = regular_icetime_seconds + overtime_icetime_seconds

    # 0-0 game
    if game_summary['goals'] is None:
        return None

    home_score = 0
    away_score = 0

    def convert_goal(goal):
        nonlocal home_score, away_score

        is_home_goal = goal['home'] == '1'
        to_return = [
            season,
            season_type,
            league,
            game_id,
            date,
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
        ]
        if is_home_goal:
            home_score += 1
        else:
            away_score += 1
        return to_return

    def filter_penalty(penalty):
        # Some penalties weirdly have empty player info, with player_id: -1
        # Bench penalties have player_id: 0, and we want to keep them
        return int(penalty['player_penalized_info']['player_id']) > -1

    def convert_penalty(penalty):
        return [
            season,
            season_type,
            league,
            game_id,
            home_team if penalty['home'] == '1' else away_team,
            'Bench' if penalty['bench'] == '1' else player_name(penalty['player_penalized_info']),
            penalty['lang_penalty_description'],
            penalty['minutes'],
            penalty['period_id'],
            penalty['time_off_formatted'],
            '',  # TODO strength
        ]

    game_result = [
        season,
        season_type,
        league,
        game_id,
        date,
        away_team,
        home_team,
        game_summary['totalGoals']['visitor'],
        game_summary['totalGoals']['home'],
        home_team if home_goals > away_goals else away_team,
        home_team if home_goals < away_goals else away_team,
        away_roster,
        home_roster,
        total_icetime_seconds / 60,
        '',  # TODO 5v5 icetime
    ]

    return (
        listmap(game_summary['goals'], convert_goal),
        listmap(filter(filter_penalty, game_summary['penalties']), convert_penalty),
        game_result,
    )


def get_season_stats(season, league, goals_results: list, penalties_results: list, games_results: list):
    if len(goals_results) is 0:
        goals_results.append([
            'Season',
            'Season Type',
            'League',
            'GameID',
            'date',
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
        ])

    if len(penalties_results) is 0:
        penalties_results.append([
            'Season',
            'Season Type',
            'League',
            'GameID',
            'Team',
            'Player',
            'Offense',
            'Minutes',
            'Period',
            'Time',
            'Strength',
        ])

    if len(games_results) is 0:
        games_results.append([
            'Season',
            'Season Type',
            'League',
            'GameID',
            'Date',
            'Visiting Team',
            'Home Team',
            'Visitor GF',
            'Home GF',
            'Winning Team',
            'Losing Team',
            'Visitor Roster',
            'Home Roster',
            'Total Time',
            '5v5 Time',
        ])

    schedule = get_json('http://cluster.leaguestat.com/feed/?feed=modulekit&view=schedule&key={0}&fmt=json&client_code={1}&lang=en&season_id={2}&team_id=undefined&league_code=&fmt=json'.format(get_api_key(league), get_league_code(league), season['season_id']))['SiteKit']['Schedule']

    pool = multiprocessing.Pool(4)

    def add_league_to_game(game):
        game['league'] = league
        game['season'] = season['end_date'][0:4]
        game['playoff'] = season['playoff']
        return game

    raw_results = filter(lambda result: result is not None, pool.map(get_game_info, map(add_league_to_game, schedule)))
    (game_goal_results, game_penalty_results, game_result) = zip(*raw_results)

    goals_results += flatten(game_goal_results)
    penalties_results += flatten(game_penalty_results)
    games_results += game_result
