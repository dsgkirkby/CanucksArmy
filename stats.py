import requests
import re
import sys
import helpers
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


def get_player_points(league, season, results_array=None):
    league = str(league)

    if results_array is None:
        results_array = [['Name', 'Position', 'Season', 'League', 'Team', 'GP', 'G', 'A', 'TP', 'PIM', '+/-']]

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

        for playerIndex in range(1, len(players)):
            player = players[playerIndex]
            player_stats = player.find_all('td')

            """ Only add to the array if the row isn't blank """
            if player_stats[NAME].a is None or '-' in player_stats[GOALS]:
                continue

            player_id = helpers.get_player_id(player_stats)
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


""" MAIN """


def main():
    if len(sys.argv) < 3:
        print("Usage: expects 2 arguments - name of league (i.e. 'QMJHL') and season (start year only, i.e. '2015' for 2014-15)")
        return
    league = sys.argv[1]
    season = sys.argv[2]
    helpers.export_array_to_csv(get_player_points(league, season), '{0}-{1}-stats.csv'.format(league, season))


main()
