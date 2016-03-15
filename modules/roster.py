import requests
import re
import html5lib
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


def get_player_rosters(league, season, results_array=None):
    league = str(league)
    season = str(season)

    if results_array is None or len(results_array) == 0:
        results_array.append(['Name', 'Position', 'Season', 'League', 'Team', 'DOB', 'Hometown', 'Height', 'Weight', 'Shoots'])
    player_ids = []

    """ Get the league link """

    try:
        int(league)
        team_search_url = "http://www.eliteprospects.com/league_home.php?leagueid=" + league + "&startdate=" + str(int(season) - 1)
    except ValueError:
        league_search_url = "http://www.eliteprospects.com/league_central.php"
        league_search_request = requests.get(league_search_url)

        """ Find an <a> tag with the league name in its text """

        def league_link_tag(tag):
            return tag.name == 'a' and tag.text.strip().lower() == league.lower() and len(
                re.findall('league_home.php', tag.attrs['href'], re.IGNORECASE)) > 0

        league_search_page = league_search_request.text.replace('<br>', '<br/>')
        league_search_page = BeautifulSoup(league_search_page, "html.parser")
        league_url = league_search_page.find(league_link_tag)

        if league_url is None:
            print("Invalid league name: {0}".format(league))
            return results_array

        """ Get the teams' links """

        team_search_url = "http://www.eliteprospects.com/" + league_url.attrs['href'] + "&startdate=" + str(int(season) - 1)

    team_search_request = requests.get(team_search_url)

    # All tag names have this prepended to them
    html_prefix = '{http://www.w3.org/1999/xhtml}'
    team_search_page = html5lib.parse(team_search_request.text)

    # /html/body/div[2]/table[3]/tbody/tr/td[5]/span
    rosters_table_header = team_search_page.find(
        './{0}body/{0}div[2]/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}span'.format(html_prefix))
    if 'TEAM ROSTERS' in rosters_table_header.text.upper():
        team_table_index = 5
    else:
        team_table_index = 4
    # xpath: /html/body/div[2]/table[3]/tbody/tr/td[5]/table[4/5]
    team_table = team_search_page.find(
        './{0}body/{0}div[2]/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}table[{1}]'.format(html_prefix, str(team_table_index)))

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

        player_table = team_page.find(global_nav_tag).find_next_sibling('table')

        players = player_table.find_all('tr')

        team_name = team_page.find(team_name_tag).text

        """ Row 0 is the title row """
        for playerIndex in range(1, len(players)):
            player = players[playerIndex]
            player_stats = player.find_all('td')

            """ Only add to the array if the row isn't blank """
            if player_stats[ID].font is not None:
                continue

            try:
                name = player_stats[NAME].a.text.strip()
                position = player_stats[NAME].font.text.strip()[1:-1]
                dob = player_stats[DOB].text.strip()
                hometown = player_stats[HOMETOWN].a.text.strip()
                height = player_stats[HEIGHT].find_all('span')[METRIC].text
                weight = player_stats[WEIGHT].find_all('span')[METRIC].text
                shoots = player_stats[SHOOTS].text
            except IndexError:
                continue

            player_id = name + dob + hometown
            if player_id in player_ids:
                index = player_ids.index(player_id)
                results_array[index][4] = 'multiple'
                continue

            player_ids.append(player_id)
            results_array.append([
                name,
                position,
                season,
                league,
                team_name,
                dob,
                hometown,
                height,
                weight,
                shoots
            ])

    return results_array
