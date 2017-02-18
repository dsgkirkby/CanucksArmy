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

GOALIE_ID = 0
GOALIE_NAME = 1
GOALIE_TEAM = 2
GOALIE_GP = 3
GOALIE_GAA = 4
GOALIE_SVP = 5

DUPLICATES_ALLOWED = 5


def get_player_stats(league, season, results_array, goalie_results_array, show_multiple_teams=False, playoffs=False):
    league = str(league)

    if results_array is None:
        results_array = []

    if len(results_array) == 0:
        results_array.append(['Name', 'Position', 'Season', 'League', 'Team', 'GP', 'G', 'A', 'TP', 'PIM', '+/-'])

    if goalie_results_array is None:
        goalie_results_array = []

    if len(goalie_results_array) == 0:
        goalie_results_array.append(['Name', 'Season', 'League', 'Team', 'GP', 'GAA', 'SV%'])

    player_ids = []
    goalie_ids = []
    page_index = 1
    player_duplicates_left = DUPLICATES_ALLOWED
    goalie_duplicates_left = DUPLICATES_ALLOWED

    while player_duplicates_left > 0 or goalie_duplicates_left > 0:
        baseurl = "http://www.eliteprospects.com/postseason.php?currentpage={0}&season={1}&leagueid={2}&postseasonid=Playoffs" if playoffs else "http://www.eliteprospects.com/league.php?currentpage={0}&season={1}&leagueid={2}"

        url = baseurl.format(str(page_index), str(int(season) - 1), league)
        r = requests.get(url)

        player_regex = re.compile('PLAYER STATS')

        page_text = r.text.replace('<br>', '<br/>')
        page_text = re.sub(r"<hr(.*)>", r"<hr\1/>", page_text)

        soup = BeautifulSoup(page_text, "html.parser")
        player_table = soup.find(text=player_regex).parent.parent.find_all("table")[2]

        #########################################################
        #  PLAYERS
        #########################################################

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

            # If there is no <a> in the player row, then this row is a continuation of a previous player
            if player_stats[NAME].a is not None:
                name = player_stats[NAME].a.text
                position = player_stats[NAME].font.text.strip()[1:-1]
                player_id = player_stats[NAME].a.attrs['href']

            current_player_id = player_id + (player_stats[TEAM].text if show_multiple_teams else '')
            if current_player_id in player_ids:
                player_duplicates_left -= 1
                if player_duplicates_left > 0:
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

            player_duplicates_left = DUPLICATES_ALLOWED

            player_ids.append(current_player_id)
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

        #########################################################
        #  GOALIES
        #########################################################

        goalie_table = soup.find(text=player_regex).parent.parent.find_all("table")[3]

        goalies = goalie_table.find_all('tr')

        # Row 0 is the title row
        for goalieIndex in range(1, len(goalies)):
            goalie = goalies[goalieIndex]
            goalie_stats = goalie.find_all('td')

            skip_row = goalie_stats[GOALIE_NAME].a is None

            # Only add to the array if the row isn't blank
            if skip_row:
                continue

            name = goalie_stats[GOALIE_NAME].a.text

            goalie_id = name

            if goalie_id in goalie_ids:
                goalie_duplicates_left -= 1
                if goalie_duplicates_left > 0:
                    continue
                else:
                    break

            team = goalie_stats[GOALIE_TEAM].text
            games = goalie_stats[GOALIE_GP].text
            gaa = goalie_stats[GOALIE_GAA].text
            svp = goalie_stats[GOALIE_SVP].text

            goalie_duplicates_left = DUPLICATES_ALLOWED

            goalie_ids.append(goalie_id)

            goalie_results_array.append([
                name,
                season,
                league,
                team,
                games,
                gaa,
                svp,
            ])

        page_index += 1

    return results_array
