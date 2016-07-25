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

DUPLICATES_ALLOWED = 5


def get_player_stats(league, season, results_array, show_multiple_teams=False):
    league = str(league)

    if results_array is None:
        results_array = []

    if len(results_array) == 0:
        results_array.append(['Name', 'Position', 'Season', 'League', 'Team', 'GP', 'G', 'A', 'TP', 'PIM', '+/-'])

    player_ids = []
    page_index = 1
    duplicates_left = DUPLICATES_ALLOWED

    while duplicates_left > 0:
        url = "http://www.eliteprospects.com/league.php?currentpage={0}&season={1}&leagueid={2}".format(str(page_index), str(int(season) - 1), league)
        r = requests.get(url)

        regex = re.compile('PLAYER STATS')

        page_text = r.text.replace('<br>', '<br/>')

        soup = BeautifulSoup(page_text, "html.parser")
        player_table = soup.find(text=regex).parent.parent.find_all("table")[2]

        players = player_table.find_all('tr')

        # Row 0 is the title row
        for playerIndex in range(1, len(players)):
            player = players[playerIndex]
            player_stats = player.find_all('td')

            if show_multiple_teams:
                skip_row = player_stats[TEAM].text.strip() == ''
            else:
                skip_row = player_stats[NAME].a is None

            # Only add to the array if the row isn't blank
            if skip_row or '-' in player_stats[GOALS]:
                continue

            # if there is no value, use the old one
            if player_stats[NAME].a is not None:
                name = player_stats[NAME].a.text
                position = player_stats[NAME].font.text.strip()[1:-1]
                player_rank = player_stats[ID].text

            player_id = name + player_rank + (player_stats[TEAM].text if show_multiple_teams else '')
            if player_id in player_ids:
                duplicates_left -= 1
                if duplicates_left > 0:
                    continue
                else:
                    break

            team = player_stats[TEAM].text
            games = player_stats[GAMES].text
            goals = player_stats[GOALS].text
            assists = player_stats[ASSISTS].text
            points = player_stats[POINTS].text
            pim = player_stats[PIM].text
            plusminus = player_stats[PLUSMINUS].text

            if team == 'totals':
                if show_multiple_teams:
                    continue
                else:
                    team = 'multiple'

            duplicates_left = DUPLICATES_ALLOWED

            player_ids.append(player_id)
            results_array.append([
                name,
                position,
                season,
                league,
                team,
                games,
                goals,
                assists,
                points,
                pim,
                plusminus
            ])

        page_index += 1

    return results_array
