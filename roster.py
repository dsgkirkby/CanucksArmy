import requests
import re
import sys
import html5lib
import helpers
from bs4 import BeautifulSoup

ID = 0
NAME = 1
DOB = 3
HOMETOWN = 4
HEIGHT = 5
WEIGHT = 6
SHOOTS = 7

METRIC = 0
IMPERIAL = 1

""" ROSTER PARSER """


def get_player_rosters(league, season):
    league = str(league)
    season = str(season)

    results_array = [['Name', 'Position', 'Season', 'League', 'Team', 'DOB', 'Hometown', 'Height', 'Weight', 'Shoots']]
    player_ids = []

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

    teams = team_table.findall('.//{0}tbody/{0}tr/{0}td[2]/{0}a'.format(html_prefix))
    team_urls = []

    on_first_row = True

    for team in teams:
        if on_first_row:
            on_first_row = False
            continue
        team_urls.append(team.attrib['href'])

    """ Get the players """

    for teamUrl in team_urls:
        team_search_request = requests.get('http://www.eliteprospects.com/{0}'.format(teamUrl))
        team_page = BeautifulSoup(team_search_request.text, "html.parser")

        def global_nav_tag(tag):
            return tag.has_attr('id') and tag.attrs['id'] == 'globalnav'

        def team_name_tag(tag):
            return tag.has_attr('id') and tag.attrs['id'] == 'fontHeader'

        player_table = team_page.find(global_nav_tag).next_sibling

        players = player_table.find_all('tr')

        team_name = team_page.find(team_name_tag).text

        """ Row 0 is the title row """
        for playerIndex in range(1, len(players)):
            player = players[playerIndex]
            player_stats = player.find_all('td')

            """ Only add to the array if the row isn't blank """
            if player_stats[ID].font is not None:
                continue

            player_id = helpers.get_player_id(player_stats)
            if player_id in player_ids:
                break

            player_ids.append(player_id)
            results_array.append([
                player_stats[NAME].a.text,
                player_stats[NAME].font.text.strip()[1:-1],
                season,
                league,
                team_name,
                player_stats[DOB].text,
                player_stats[HOMETOWN].a.text,
                player_stats[HEIGHT].find_all('span')[METRIC].text,
                player_stats[WEIGHT].find_all('span')[METRIC].text,
                player_stats[SHOOTS].text])

    return results_array


""" MAIN """


def main():
    if len(sys.argv) < 3:
        print("Usage: expects 2 arguments - name of league (i.e. 'QMJHL') and season (end year only, i.e. '2015' for 2014-15)")
        return
    league = sys.argv[1]
    season = sys.argv[2]
    helpers.export_array_to_csv(get_player_rosters(league, season), '{0}-{1}-rosters.csv'.format(league, season))


main()
