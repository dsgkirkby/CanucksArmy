import requests
import html5lib
from modules import team_stats, helpers


def get_player_stats(league, season, results_array=None, goalie_results_array=None):
    league = str(league)
    season = str(season)

    if results_array is None:
        results_array = []
    if goalie_results_array is None:
        goalie_results_array = []
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
        team_stats.get_player_stats(
            team_url, season, league, results_array, goalie_results_array)

    return results_array
