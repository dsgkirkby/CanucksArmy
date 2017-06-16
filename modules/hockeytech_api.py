import multiprocessing
import functools
import re
from modules.helpers import listmap, flatten, strip_extra_spaces, get_json


SECONDS_PER_MINUTE = 60
height_regex = re.compile('([3-8])[^\d]{0,2}([0-9]+)?')


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
    return strip_extra_spaces(
        (player['first_name'] + ' ' + player['last_name']) if player['player_id'] is not None else ''
    )


def player_height(player):
    raw = player['height']

    if len(raw) is 0:
        return ''

    regex_result = height_regex.search(raw)

    if regex_result is None:
        print("Unrecognized height format: {0}".format(raw))
        return ''

    (feet, *inches) = regex_result.groups()
    inches = inches[0] if len(inches) > 0 and inches[0] is not None else '0'
    inches = '0' + inches if len(inches) == '1' else inches
    return feet + '.' + inches


def player_team(player):
    if int(player['num_teams']) > 1:
        return ' / '.join(listmap(player['team_breakdown'], lambda team: team['team_name'].strip()))
    else:
        return player['team_name']


def season_type_label(season):
    is_playoffs = season['playoff'] == '1'
    return is_playoffs, 'Playoffs' if season['playoff'] == '1' else 'Season'


def season_year(season):
    return season['end_date'][0:4]


def get_game_info(game_info, season_info, league):
    game_summary = get_json('http://cluster.leaguestat.com/feed/index.php?feed=gc&key={0}&client_code={1}&game_id={2}&lang_code=en&fmt=json&tab=gamesummary'.format(get_api_key(league), get_league_code(league), game_info['game_id']))['GC']['Gamesummary']

    home_team = team_name(game_summary['home'])
    away_team = team_name(game_summary['visitor'])

    home_roster = team_roster(game_summary['home_team_lineup']) if type(game_summary['home_team_lineup']) is not list else ''
    away_roster = team_roster(game_summary['visitor_team_lineup']) if type(game_summary['visitor_team_lineup']) is not list else ''

    season = season_year(season_info)
    is_playoff_game, season_type = season_type_label(season_info)
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
        if 'player_penalized_info' not in penalty:
            return False

        # Some penalties weirdly have empty player info, with player_id: -1
        # Bench penalties have player_id: 0, and we want to keep them
        penalized_player_info = penalty['player_penalized_info']
        return 'player_id' in penalized_player_info and int(penalized_player_info['player_id']) > -1

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
        listmap(game_summary['goals'], convert_goal) if game_summary['goals'] is not None else [],
        listmap(filter(filter_penalty, game_summary['penalties']), convert_penalty)
        if game_summary['penalties'] is not None else
        [],
        game_result,
    )


def get_season_stats(
        season,
        league,
        goals_results: list,
        penalties_results: list,
        games_results: list,
        players_results: list
):
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

    if len(players_results) is 0:
        players_results.append([
            'Player',
            'Position',
            'Season',
            'Season Type',
            'League',
            'Team',
            'Age',
            'Birthdate',
            'Birthplace',
            'Height',
            'Weight',
            'Shot',
            'GP',
        ])

    schedule = get_json('http://cluster.leaguestat.com/feed/?feed=modulekit&view=schedule&key={0}&fmt=json&client_code={1}&lang=en&season_id={2}&team_id=undefined&league_code=&fmt=json'.format(get_api_key(league), get_league_code(league), season['season_id']))['SiteKit']['Schedule']

    players = get_json('http://cluster.leaguestat.com/feed/?feed=modulekit&view=statviewtype&type=topscorers&key={0}&fmt=json&client_code={1}&lang=en&league_code=&season_id={2}&first=0&limit=10000&sort=points&stat=all&order_direction='.format(get_api_key(league), get_league_code(league), season['season_id']))['SiteKit']['Statviewtype']

    (_, season_type) = season_type_label(season)

    def convert_player(player):
        return [
            player_name(player),
            player['position'],
            season_year(season),
            season_type,
            league,
            player_team(player),
            player['age'],
            player['birthdate'],
            player['homeplace'],
            player_height(player),
            player['weight'],
            player['shoots'],
            player['games_played'],
        ]

    season_players = listmap(players, convert_player)

    raw_results = multiprocessing.Pool(6).map(
        functools.partial(get_game_info, season_info=season, league=league),
        schedule
    )
    (game_goal_results, game_penalty_results, game_result) = zip(*raw_results)

    goals_results += flatten(game_goal_results)
    penalties_results += flatten(game_penalty_results)
    games_results += game_result
    players_results += season_players
