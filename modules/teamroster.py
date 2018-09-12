import requests
import html5lib
from modules import helpers

JERSEY_NUMBER = 1
NAME = 3
DOB = 5
HOMETOWN = 6
HEIGHT = 7
WEIGHT = 8
SHOOTS = 9


def get_team_roster(team_url, season, player_ids=None, results_array=None, multiple_teams=False, full_dob=False):
    if results_array is None:
        results_array = []

    if player_ids is None:
        player_ids = []

    if len(results_array) == 0:
        results_array.append(['Number', 'Name', 'Position', 'Season', 'League',
                              'Team', 'DOB', 'Hometown', 'Height', 'Weight', 'Shoots', 'ID'])

    team_search_request = requests.get(team_url)
    team_page = html5lib.parse(team_search_request.text)

    league_name = team_page.find('./body/section[2]/div/div[1]/div[4]/div[1]/div/div[1]/div[3]/small/span/a'.replace(
        '/', '/' + helpers.html_prefix)).text.strip()

    team_name = team_page.find('./body/section[2]/div/div[1]/div[4]/div[1]/div/div[1]/div[3]'.replace(
        '/', '/' + helpers.html_prefix)).text.strip()

    player_table = team_page.find(
        './body/section[2]/div/div[1]/div[4]/div[2]/div[1]/div[1]/div[1]/div[3]/table'.replace('/', '/' + helpers.html_prefix))

    players_by_position = helpers.get_ep_table_rows(player_table)

    for position in players_by_position:
        for player in position:
            player_stats = player.findall(
                './{}td'.format(helpers.html_prefix))

            try:
                name_link = player_stats[NAME].find(
                    './{0}span/{0}a'.format(helpers.html_prefix))
                name_raw = name_link.text.strip()
                name_parts = name_raw.split('(')
                name = name_parts[0].strip()
                position = name_parts[1][:-1].strip()
                id = helpers.get_player_id_from_url(
                    name_link.attrib['href'])
                number = player_stats[JERSEY_NUMBER].text.strip()[1:]
                dob = player_stats[DOB].text.strip()
                if full_dob:
                    player_page = requests.get(name_link.attrib['href'])
                    dob = html5lib.parse(player_page.text).find(
                        './body/section[2]/div/div[1]/div[4]/div[1]/div[1]/div[2]/section/div[4]/div[1]/div[1]/ul/li[1]/div[2]/a'.replace(
                            '/', '/' + helpers.html_prefix)
                    ).text.strip()
                hometown = player_stats[HOMETOWN].find(
                    './{}a'.format(helpers.html_prefix)).text.strip()
                height = player_stats[HEIGHT].text.strip()
                weight = player_stats[WEIGHT].text.strip()
                shoots = player_stats[SHOOTS].text.strip()
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
