import requests
import html5lib
from modules import helpers

html_prefix = helpers.html_prefix

NAME = 1
GAMES = 2
WINS = 3
TIES = 4
LOSSES = 5
OT_WINS = 6
OT_LOSSES = 7
GOALS_FOR = 8
GOALS_AGAINST = 9
POINTS = 11
POSTSEASON = 12

""" ROSTER PARSER """


def get_league_standings(league, season, results_array=None):
    league = str(league)
    season = str(season)

    if results_array is None or len(results_array) == 0:
        results_array.append(['Team ID', 'Team Name', 'League', 'Season', 'Games',
                              'W', 'L', 'OT', 'GF', 'GA', 'Points', 'PostSeason'])

    standings_url = 'http://www.eliteprospects.com/standings.php?league={0}&startdate={1}'.format(
        league, str(int(season) - 1))
    request = requests.get(standings_url)
    standings_page = html5lib.parse(request.text)

    standings_table = standings_page.find(
        './body/section[2]/div/div[1]/div[4]/div[2]/div[1]/div/div[3]/table'.replace('/', '/' + html_prefix))

    teams_by_conference = helpers.get_ep_table_rows(standings_table)

    """ Parse the team standings table """

    for conference in teams_by_conference:
        for team in conference:
            team_stats = team.findall('.//{0}td'.format(html_prefix))
            
            team_url: str = team.find('.//{0}td[2]/{0}span/{0}a'.format(html_prefix)).attrib['href']
            team_id = team_url.split("/")[4]

            name = team_stats[NAME].find(
                './/{0}span/{0}a'.format(html_prefix)).text.strip()
            games = team_stats[GAMES].text.strip()

            def parse_number(node):
                try:
                    return int(node.text)
                except (ValueError, Exception):
                    return 0

            wins = parse_number(team_stats[WINS])
            losses = parse_number(team_stats[LOSSES])
            ties = parse_number(team_stats[TIES])
            ot_wins = parse_number(team_stats[OT_WINS])
            ot_losses = parse_number(team_stats[OT_LOSSES])
            goals_for = team_stats[GOALS_FOR].text.strip()
            goals_against = team_stats[GOALS_AGAINST].text.strip()
            points = team_stats[POINTS].text.strip()
            postseason = ''.join(team_stats[POSTSEASON].itertext()).strip()

            results_array.append([
                team_id,
                name,
                league,
                season,
                games,
                wins + ot_wins,
                losses,
                ot_losses + ties,
                goals_for,
                goals_against,
                points,
                postseason
            ])

    return results_array
