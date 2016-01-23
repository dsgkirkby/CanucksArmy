import requests
import re
from bs4 import BeautifulSoup

ID = 0
NAME = 1
TEAM = 2
GAMES = 3
GOALS = 4
ASSISTS = 5
POINTS = 6
PIM = 8
PLUSMINUS = 9

""" PLAYER STAT PARSER """


def get_player_stats(league, season, results_array=None):
    league = str(league)

    if results_array is None or len(results_array) == 0:
        results_array.append(['Name', 'Position', 'Season', 'League', 'Team', 'GP', 'G', 'A', 'TP', 'PIM', '+/-'])

    player_ids = []
    page_index = 1
    done = False

    while not done:
        url = "http://www.eliteprospects.com/league.php?currentpage={0}&season={1}&leagueid={2}".format(str(page_index), str(int(season) - 1), league)
        r = requests.get(url)

        regex = re.compile('PLAYER STATS')

        page_text = r.text.replace('<br>', '<br/>')

        soup = BeautifulSoup(page_text, "html.parser")
        player_table = soup.find(text=regex).parent.parent.find_all("table")[2]

        players = player_table.find_all('tr')

        """ Row 0 is the title row """
        for playerIndex in range(1, len(players)):
            player = players[playerIndex]
            player_stats = player.find_all('td')

            """ Only add to the array if the row isn't blank """
            if player_stats[NAME].a is None or '-' in player_stats[GOALS]:
                continue

            player_id = player_stats[NAME].text + player_stats[ID].text
            if player_id in player_ids:
                done = True
                break

            player_team = player_stats[TEAM].text
            if player_team == 'totals':
                player_team = 'multiple'

            player_ids.append(player_id)
            results_array.append([
                player_stats[NAME].a.text,
                player_stats[NAME].font.text.strip()[1:-1],
                season,
                league,
                player_team,
                player_stats[GAMES].text,
                player_stats[GOALS].text,
                player_stats[ASSISTS].text,
                player_stats[POINTS].text,
                player_stats[PIM].text,
                player_stats[PLUSMINUS].text])

        page_index += 1

    return results_array
