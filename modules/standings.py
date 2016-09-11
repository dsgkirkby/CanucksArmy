import requests
import html5lib

NAME = 1
GAMES = 2
GOALS_FOR = 8
GOALS_AGAINST = 9
POSTSEASON = 12

""" ROSTER PARSER """


def get_league_standings(league, season, results_array=None):
    league = str(league)
    season = str(season)

    if results_array is None or len(results_array) == 0:
        results_array.append(['Team Name', 'League', 'Season', 'Games', 'GF', 'GA', 'PostSeason'])

    standings_url = 'http://www.eliteprospects.com/standings.php?league={0}&startdate={1}'.format(league, str(int(season) - 1))
    request = requests.get(standings_url)

    # All tag names have this prepended to them
    html_prefix = '{http://www.w3.org/1999/xhtml}'
    standings_page = html5lib.parse(request.text)

    standings_table = standings_page.find(
        './{0}body/{0}div/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}table[3]'.format(html_prefix))

    teams = standings_table.findall('.//{0}tbody/{0}tr'.format(html_prefix))

    """ Parse the team standings table """

    is_first_row = True

    for team in teams:

        if is_first_row:
            is_first_row = False
            continue

        team_stats = team.findall('.//{0}td'.format(html_prefix))

        """ Exclude subtitle rows """
        if len(team_stats) < 2:
            continue

        name = team_stats[NAME].find('.//{0}a'.format(html_prefix)).text
        games = team_stats[GAMES].text
        goals_for = team_stats[GOALS_FOR].text
        goals_against = team_stats[GOALS_AGAINST].text
        postseason = ''.join(team_stats[POSTSEASON].itertext()).strip()

        results_array.append([
            name,
            league,
            season,
            games,
            goals_for,
            goals_against,
            postseason
        ])

    return results_array
