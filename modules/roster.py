import requests
import html5lib
from modules import teamroster, helpers


def get_player_rosters(league, season, results_array=None, multiple_teams=False, full_dob=False):
    league = str(league)
    season = str(season)

    if results_array is None:
        results_array = []
    player_ids = []
    team_urls = []

    """ Get the league link """

    team_search_url = "http://www.eliteprospects.com/standings.php?league={0}&startdate={1}".format(
        league, str(int(season) - 1))
    team_search_request = requests.get(team_search_url)

    # All tag names have this prepended to them
    html_prefix = '{http://www.w3.org/1999/xhtml}'
    team_search_page = html5lib.parse(team_search_request.text)
    team_table = team_search_page.find(
        './body/section[2]/div/div[1]/div[4]/div[2]/div[1]/div/div[3]/table'.replace('/', '/' + html_prefix))

    teams_by_conference = helpers.get_ep_table_rows(team_table)

    for conference in teams_by_conference:
        for team in conference:
            team_urls.append(
                team.find('.//{0}td[2]/{0}span/{0}a'.format(html_prefix)).attrib['href'] +
                f"/{int(season) - 1}-{season}"
            )

    """ Get the players """

    for team_url in team_urls:
        teamroster.get_team_roster(
            team_url, season, league, player_ids, results_array, multiple_teams, full_dob=full_dob)

    return results_array
