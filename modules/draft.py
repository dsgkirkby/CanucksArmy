import requests
import html5lib

from modules import helpers

NUMBER = 0
TEAM = 1
NAME = 2
SEASONS = 3
GAMES = 4
GOALS = 5
ASSISTS = 6
POINTS = 7
PIM = 8


def get_draft_picks(season, results_array=None, show_extra=False):
    if results_array is None:
        results_array = []
    if len(results_array) == 0:
        results_array.append(['Year', 'Round', 'Number', 'Team', 'Name', 'Position',
                              'Seasons', 'Games', 'Goals', 'Assists', 'Points', 'PIM', 'Birthday'])

    url = 'http://www.eliteprospects.com/draft.php?year={0}'.format(
        str(season))
    r = requests.get(url)

    # All tag names have this prepended to them
    html_prefix = '{http://www.w3.org/1999/xhtml}'
    draft_page = html5lib.parse(r.text)
    draft_table = draft_page.find(
        './body/section[2]/div/div[1]/div[4]/div[3]/div[1]/div[1]/div[3]/table'.replace('/', '/' + html_prefix))

    pick_number = 1

    rounds = helpers.get_ep_table_rows(draft_table)

    for round_number in range(1, len(rounds) + 1):
        players = rounds[round_number - 1]

        for playerIndex in range(0, len(players)):
            player = players[playerIndex]
            columns = player.findall('.//{0}td'.format(html_prefix))

            player_birthday = ''

            try:
                name_link = columns[NAME].find(
                    './{0}span/{0}a'.format(html_prefix))
                name, position = helpers.get_info_from_player_name(
                    name_link.text)
                if show_extra:
                    player_request = requests.get(name_link.attrib['href'])
                    player_page = html5lib.parse(player_request.text)

                    player_birthday = player_page.find(
                        './body/section[2]/div/div[1]/div[4]/div[1]/div[1]/div[2]/section/div[4]/div[1]/div[1]/ul/li[1]/div[2]/a'.replace(
                            '/', '/' + html_prefix)
                    ).text.strip()
            except AttributeError:
                name = 'No selection made'
                position = 'N/A'

            results_array.append([
                season,
                round_number,
                pick_number,
                columns[TEAM].find('./{}a'.format(html_prefix)).text,
                name,
                position,
                columns[SEASONS].text.strip(),
                columns[GAMES].text.strip() or '',
                columns[GOALS].text.strip() or '',
                columns[ASSISTS].text.strip() or '',
                columns[POINTS].text.strip() or '',
                columns[PIM].text.strip() or '',
                player_birthday
            ])

            pick_number += 1

    return results_array
