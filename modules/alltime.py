import requests
import re
from bs4 import BeautifulSoup

ID = 0
NAME = 1
GAMES = 2
GOALS = 3
ASSISTS = 4
POINTS = 5

""" PLAYER STAT PARSER """


def get_all_time_stats(league, results_array=[]):
    league = str(league)

    if results_array is None or len(results_array) == 0:
        results_array.append(['Name', 'Position', 'League', 'Team', 'GP', 'G', 'A', 'TP'])

    player_ids = []
    page_index = 1
    done = False

    while not done:
        url = "http://www.eliteprospects.com/league_all-time_stats.php?currentpage={0}&league={1}&alltime=TP&leaguename={1}".format(str(page_index), league)
        r = requests.get(url)

        regex = re.compile('LEAGUE ALL-TIME POINTS')

        page_text = r.text.replace('<br>', '<br/>')

        soup = BeautifulSoup(page_text, "html.parser")
        player_table = soup.find(text=regex).parent.parent.find_all("table")[1]

        players = player_table.find_all('tr')

        """ Row 0 is the title row """
        for playerIndex in range(1, len(players)):
            player = players[playerIndex]
            player_stats = player.find_all('td')

            """ Only add to the array if the row isn't blank """
            if player_stats[NAME].a is None:
                continue

            player_id = player_stats[NAME].text + player_stats[ID].text
            if player_id in player_ids:
                done = True
                break

            player_ids.append(player_id)
            results_array.append([
                player_stats[NAME].a.text,
                player_stats[NAME].font.text.strip()[1:-1],
                league,
                player_stats[GAMES].text,
                player_stats[GOALS].text,
                player_stats[ASSISTS].text,
                player_stats[POINTS].text])

        page_index += 1

    return results_array
