import requests
import re
import html5lib
from bs4 import BeautifulSoup

NAME = 1
GAMES = 2
GOALS_FOR = 8
GOALS_AGAINST = 9

""" ROSTER PARSER """


def get_league_standings(league, season, results_array=None):
    league = str(league)
    season = str(season)

    if results_array is None or len(results_array) == 0:
        results_array.append(['Team Name', 'League', 'Season', 'Games', 'GF', 'GA'])

    """ Get the league link """

    league_search_url = "http://www.eliteprospects.com/league_central.php"
    league_search_request = requests.get(league_search_url)

    """ Find an <a> tag with the league name in its text """

    def league_link_tag(tag):
        return tag.name == 'a' and tag.text.strip().lower() == league.lower() and len(
            re.findall('league_home.php', tag.attrs['href'], re.IGNORECASE)) > 0

    league_search_page = league_search_request.text.replace('<br>', '<br/>')
    league_search_page = BeautifulSoup(league_search_page, "html.parser")
    league_url = league_search_page.find(league_link_tag)

    """ Get the teams' links """

    team_search_url = "http://www.eliteprospects.com/" + league_url.attrs['href'] + "&startdate=" + str(int(season) - 1)
    team_search_request = requests.get(team_search_url)

    # All tag names have this prepended to them
    html_prefix = '{http://www.w3.org/1999/xhtml}'
    team_search_page = html5lib.parse(team_search_request.text)
    # xpath: /html/body/div[2]/table[3]/tbody/tr/td[5]/table[5]
    team_table = team_search_page.find(
        './{0}body/{0}div[2]/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}table[5]'.format(html_prefix))

    teams = team_table.findall('.//{0}tbody/{0}tr'.format(html_prefix))

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

        results_array.append([
            name,
            league,
            season,
            games,
            goals_for,
            goals_against
        ])

    return results_array
