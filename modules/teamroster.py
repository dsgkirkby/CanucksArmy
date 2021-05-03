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


def get_team_roster(team_url, season, league_name, player_ids=None, results_array=None, multiple_teams=False):
    if results_array is None:
        results_array = []

    if player_ids is None:
        player_ids = []

    if len(results_array) == 0:
        results_array.append(['ID', 'Name', 'Position', 'Season', 'League',
                              'Team', 'DOB', 'Hometown', 'Height', 'Weight', 'Shoots', 'Number', 'Team ID'])

    team_search_request = requests.get(team_url)
    team_page = html5lib.parse(team_search_request.text)

    try:
        team_name = team_page.find('./body/section[2]/div/div[1]/div[4]/div[1]/div/div[1]/div[2]/div[2]'.replace(
            '/', '/' + helpers.html_prefix)).text.strip()
    except:
        team_name = team_page.find('./body/section[2]/div/div[1]/div[4]/div[1]/div/div[1]/div[2]/div[1]'.replace(
            '/', '/' + helpers.html_prefix)).text.strip()
        
    team_id = team_url.split("/")[4]

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
                name, position = helpers.get_info_from_player_name(
                    name_link.text)
                id = helpers.get_player_id_from_url(
                    name_link.attrib['href'])
                number = player_stats[JERSEY_NUMBER].text.strip()[1:]
                dob = player_stats[DOB].get('title').strip()
                hometown = player_stats[HOMETOWN].find(
                    './{}a'.format(helpers.html_prefix)).text.strip()
                height_raw = player_stats[HEIGHT].text.strip()
                weight_raw = player_stats[WEIGHT].text.strip()
                shoots = player_stats[SHOOTS].text.strip()
            except IndexError:
                continue
                
            try:
                height_ft = height_raw.split("&#039;")[0]
                height_in = height_raw.split("&#039;")[1].split("&quot;")[0]
                height_in += height_ft * 12
                height_cm = round(float(height_in) * 2.54, 1)
                height = height_in
                
                weight = round(float(weight_raw) * 0.4536, 1)
            except IndexError:
                continue

            if not multiple_teams:
                player_id = name + dob + hometown
                if player_id in player_ids:
                    index = player_ids.index(player_id)
                    results_array[index][5] = 'multiple'
                    continue

                player_ids.append(player_id)

            results_array.append([
                id,
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
                number,
                team_id
            ])
