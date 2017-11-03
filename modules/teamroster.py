import requests
from bs4 import BeautifulSoup
from modules import helpers

JERSEY_NUMBER = 1
NAME = 2
DOB = 4
HOMETOWN = 5
HEIGHT = 6
WEIGHT = 7
SHOOTS = 8

METRIC = 0
IMPERIAL = 1


def get_team_roster(team_url, season, player_ids=None, results_array=None, multiple_teams=False, league=''):
    if results_array is None:
        results_array = []

    if player_ids is None:
        player_ids = []

    if len(results_array) == 0:
        results_array.append(['Number', 'Name', 'Position', 'Season', 'League', 'Team', 'DOB', 'Hometown', 'Height', 'Weight', 'Shoots'])

    team_search_request = requests.get('http://www.eliteprospects.com/{0}'.format(team_url))
    team_page = BeautifulSoup(team_search_request.text, "html.parser")

    def global_nav_tag(tag):
        return tag.has_attr('id') and tag.attrs['id'] == 'globalnav'

    def team_name_tag(tag):
        return tag.has_attr('id') and tag.attrs['id'] == 'fontHeader'

    def league_name_tag(tag):
        return tag.has_attr('id') and tag.attrs['id'] == 'fontMainlink2'

    league_name = league if len(league) > 0 else team_page.find(global_nav_tag).find_parent().find(league_name_tag).text.strip()

    player_table = team_page.find(global_nav_tag).find_next_sibling('table')

    players = player_table.find_all('tr')

    team_name = team_page.find(team_name_tag).text

    """ Row 0 is the title row """
    for playerIndex in range(1, len(players) - 1):
        player = players[playerIndex]
        player_stats = player.find_all('td')

        """ Only add to the array if the row isn't blank """
        if player_stats[NAME].a is None:
            continue

        try:
            name = player_stats[NAME].a.text.strip()
            id = helpers.get_player_id_from_url(player_stats[NAME].a.attrs['href'])
            number = player_stats[JERSEY_NUMBER].text.strip()[1:]
            if not number:
                number = '-'
            position = player_stats[NAME].font.text.strip()[1:-1]
            dob = player_stats[DOB].text.strip()
            hometown = player_stats[HOMETOWN].a.text.strip()
            height = player_stats[HEIGHT].find_all('span')[METRIC].text
            weight = player_stats[WEIGHT].find_all('span')[METRIC].text
            shoots = player_stats[SHOOTS].text
        except IndexError:
            continue

        if not multiple_teams:
            player_id = name + dob + hometown
            if player_id in player_ids:
                index = player_ids.index(player_id)
                results_array[index][4] = 'multiple'
                continue

            player_ids.append(player_id)

        results_array.append([
            number,
            name,
            position,
            season,
            league_name,
            team_name,
            dob,
            hometown,
            height,
            weight,
            shoots,
            id,
        ])
