import multiprocessing
import functools
import re
from modules.helpers import listmap, flatten, strip_extra_spaces, get_json


# We treat double minors as if they behave like majors for simplicity TODO fix
MAJOR_PENALTY_TYPES = ['Major', 'Match', 'Double Minor']
PENALTY_END = 'penalty_end'
SECONDS_PER_MINUTE = 60
height_regex = re.compile('([3-8])[^\d]{0,2}([0-9]+)?')


def get_league_code(league):
    if league == 'qmjhl':
        return league[::-1]
    else:
        return league


def get_api_key(league):
    if league == 'ahl':
        return '50c2cd9b5e18e390'
    elif league == 'whl':
        return '41b145a848f4bd67'
    elif league == 'ohl':
        return '2976319eb44abe94'
    elif league == 'qmjhl':
        return 'f322673b6bcae299'
    elif league == 'ushl':
        return 'e828f89b243dc43f'
    elif league == 'bchl':
        return 'ca4e9e599d4dae55'


def team_name(team):
    city = team['city']
    nickname = team['nickname']
    name = team['name']

    if city == nickname:
        return name
    else:
        return strip_extra_spaces(city + ' ' + nickname)


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
    end_minute = int(end_clock[3:5])
    end_second = int(end_clock[6:8])
    end_period = game_summary['meta']['period']
    regular_icetime_seconds = 3 * 20 * SECONDS_PER_MINUTE
    ot_period_length = 20 if is_playoff_game else 5
    overtime_icetime_seconds = (
        (int(end_period) - 3)  # Number of OT periods
        * ot_period_length
        * SECONDS_PER_MINUTE
        - (end_minute * SECONDS_PER_MINUTE + end_second)  # Remaining time if OT goal was scored
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
            goal['strength'],
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
            penalty['strength'],
        ]

    goals = game_summary['goals'] if game_summary['goals'] is not None else []
    penalties = game_summary['penalties'] if game_summary['penalties'] is not None else []

    def get_time(x):
        time = x['time_off_formatted'] if 'time_off_formatted' in x else x['time']
        return x['period_id'] + ' ' + (time if len(time) is 5 else ('0' + time))

    def get_penalty_end(penalty):
        minute_start = int(penalty['time_off_formatted'][:-3])
        second_start = penalty['time_off_formatted'][-2:]
        period_start = int(penalty['period_id'])
        minute_end = minute_start + penalty['minutes']
        period_end = period_start

        if minute_end > 20 or minute_end == 20 and second_start != '00':
            period_end += 1
            minute_end -= 20

        return {
            'event': PENALTY_END,
            'period_id': str(period_end),
            'time': str(minute_end) + ':' + second_start,
            'pp': penalty['pp'],
            'home': penalty['home'],
            'penalty_class': penalty['penalty_class'],
        }

    penalty_ends = listmap(penalties, get_penalty_end)

    goals_and_penalties = sorted(
        goals + penalties + penalty_ends,
        key=get_time
    )

    ev_5v5_icetime = {
        'seconds': 0,
        'last_event_time': '0:00',
        'last_event_period': 1,
    }
    minor_penalties = {
        'home': 0,
        'away': 0,
    }
    recent_powerplay_goals = {
        'home': 0,
        'away': 0,
    }
    major_penalties = {
        'home': 0,
        'away': 0,
    }

    def track_event_5v5_icetime(event, is_5v5: bool):
        time = (event['time_off_formatted']
                if 'time_off_formatted' in event
                else event['time'])
        minute_start = int(ev_5v5_icetime['last_event_time'][:-3])
        second_start = int(ev_5v5_icetime['last_event_time'][-2:])
        period_start = int(ev_5v5_icetime['last_event_period'])
        minute_end = int(time[:-3])
        second_end = int(time[-2:])
        period_end = int(event['period_id'])

        icetime = (
            (period_end - period_start) * 20 * SECONDS_PER_MINUTE +
            (minute_end - minute_start) * SECONDS_PER_MINUTE +
            (second_end - second_start)
        )

        ev_5v5_icetime['last_event_period'] = period_end
        ev_5v5_icetime['last_event_time'] = time

        if is_5v5:
            ev_5v5_icetime['seconds'] += icetime

    def get_strength(team, is_ot=False):
        if is_ot and not is_playoff_game:
            other_team = 'away' if team == 'home' else 'home'
            return str(min(5, max(3, 3 + minor_penalties[other_team] + major_penalties[other_team])))
        else:
            return str(min(5, max(3, 5 - minor_penalties[team] - major_penalties[team])))

    def add_strength_to_goal_or_penalty(goal_or_penalty, minor_penalties, major_penalties, recent_powerplay_goals):
        primary_team = 'home' if goal_or_penalty['home'] == '1' else 'away'
        opposition_team = 'home' if goal_or_penalty['home'] == '0' else 'away'
        is_goal = goal_or_penalty['event'] == 'goal'
        is_penalty = goal_or_penalty['event'] == 'penalty'
        is_penalty_end = goal_or_penalty['event'] == PENALTY_END
        is_ot = int(goal_or_penalty['period_id']) > 3

        primary_strength = get_strength(primary_team, is_ot)
        opposition_strength = get_strength(opposition_team, is_ot)

        track_event_5v5_icetime(goal_or_penalty, primary_strength == opposition_strength == '5')

        if is_goal and len(goal_or_penalty['plus']) > 0:
            goal_or_penalty['strength'] = (
                str(len(goal_or_penalty['plus'])) + 'v' + str(len(goal_or_penalty['minus']))
            )
        else:
            # TODO empty net?
            goal_or_penalty['strength'] = primary_strength + 'v' + opposition_strength

        # powerplay goal
        if is_goal and primary_strength > opposition_strength and minor_penalties[opposition_team] > 0:
            minor_penalties[opposition_team] -= 1
            recent_powerplay_goals[primary_team] += 1
        # penalty start
        elif is_penalty and goal_or_penalty['pp'] == '1':
            if goal_or_penalty['penalty_class'] == 'Minor':
                minor_penalties[primary_team] += 1
            elif goal_or_penalty['penalty_class'] in MAJOR_PENALTY_TYPES:
                major_penalties[primary_team] += 1
        # penalty end
        elif is_penalty_end and goal_or_penalty['pp'] == '1':
            if recent_powerplay_goals[opposition_team] > 0 and goal_or_penalty['penalty_class'] == 'Minor':
                recent_powerplay_goals[opposition_team] -= 1
            elif goal_or_penalty['penalty_class'] == 'Minor':
                minor_penalties[primary_team] -= 1
            elif goal_or_penalty['penalty_class'] in MAJOR_PENALTY_TYPES:
                major_penalties[primary_team] -= 1

        return goal_or_penalty

    listmap(goals_and_penalties, functools.partial(
        add_strength_to_goal_or_penalty,
        minor_penalties=minor_penalties,
        major_penalties=major_penalties,
        recent_powerplay_goals=recent_powerplay_goals,
    ))

    end_minute_from_start = (ot_period_length if end_period != '3' else 20) - end_minute
    end_second_from_start = - end_second
    if end_second_from_start < 0:
        end_minute_from_start -= 1
        end_second_from_start += 60

    game_ends_in_ot = int(end_period) > 3

    # Add any 5v5 icetime at the end of the game
    track_event_5v5_icetime(
        {
            'time':
                str(end_minute_from_start) +
                ':' +
                ('0' if end_second_from_start < 10 else '') + str(end_second_from_start),
            'period_id': end_period
        },
        get_strength('home', game_ends_in_ot) == get_strength('away', game_ends_in_ot) == '5'
    )

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
        total_icetime_seconds / SECONDS_PER_MINUTE,
        ev_5v5_icetime['seconds'] / SECONDS_PER_MINUTE,
    ]

    return (
        listmap(goals, convert_goal),
        listmap(filter(filter_penalty, penalties), convert_penalty),
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
            'Shoots',
            'GP',
            'Shots on Goal',
            'Faceoffs',
            'Faceoff Wins',
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
            player.get('shots', None),
            player.get('faceoff_attempts', None),
            player.get('faceoff_wins', None),
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
