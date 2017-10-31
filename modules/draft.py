import requests
import html5lib

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
        results_array.append(['Year', 'Round', 'Number', 'Team', 'Name', 'Position', 'Seasons', 'Games', 'Goals', 'Assists', 'Points', 'PIM', 'Birthday'])

    url = 'http://www.eliteprospects.com/draft.php?year={0}'.format(str(season))
    r = requests.get(url)

    # All tag names have this prepended to them
    html_prefix = '{http://www.w3.org/1999/xhtml}'
    draft_page = html5lib.parse(r.text)
    # xpath: /html/body/div/table[3]/tbody/tr/td[5]/p[2]/table[1]
    draft_table = draft_page.find(
        './{0}body/{0}div[2]/{0}div/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}p[2]/{0}table[1]'.format(html_prefix))

    players = draft_table.findall('.//{0}tbody/{0}tr'.format(html_prefix))
    pick_number = 1
    round_number = 0

    """ Row 0 is the title row """
    for playerIndex in range(1, len(players)):
        player = players[playerIndex]
        columns = player.findall('.//{0}td'.format(html_prefix))

        if len(columns[NUMBER].text.strip()) < 1:
            round_header = columns[TEAM].find('.//{0}strong'.format(html_prefix))
            if round_header is not None:
                round_number += 1
            continue

        player_birthday = ''

        try:
            name_link = columns[NAME].find('{0}a'.format(html_prefix))
            name = name_link.text.strip()
            position = name_link.find('{0}font'.format(html_prefix)).text.strip()[1:-1]

            if show_extra:
                player_request = requests.get('http://www.eliteprospects.com/' + name_link.attrib['href'])
                player_page = html5lib.parse(player_request.text)

                player_birthday = player_page.find('./{0}body/{0}div[2]/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}p/{0}table[2]/{0}tbody/{0}tr/{0}td[1]/{0}table/{0}tbody/{0}tr[1]/{0}td[2]/{0}a'.format(html_prefix)).text
        except AttributeError:
            name = 'No selection made'
            position = 'N/A'

        results_array.append([
            season,
            round_number,
            pick_number,
            columns[TEAM].text,
            name,
            position,
            columns[SEASONS].text,
            columns[GAMES].text or '',
            columns[GOALS].text or '',
            columns[ASSISTS].text or '',
            columns[POINTS].text or '',
            columns[PIM].text or '',
            player_birthday
        ])

        pick_number += 1

    return results_array

