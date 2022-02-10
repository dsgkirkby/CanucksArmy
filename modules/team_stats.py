import requests
import html5lib
from modules import helpers

NAME = 2
GAMES = 3
GOALS = 4
ASSISTS = 5
POINTS = 6
PIM = 7
PLUSMINUS = 8

GOALIE_NAME = 2
GOALIE_GP = 3
GOALIE_GAA = 4
GOALIE_SVP = 5


def get_player_stats(team_url, season, league_name, results_array, goalie_results_array):
    if results_array is None:
        results_array = []

    if len(results_array) == 0:
        results_array.append(['Name', 'Position', 'Season', 'League',
                              'Team', 'GP', 'G', 'A', 'TP', 'PIM', '+/-', 'ID'])

    if goalie_results_array is None:
        goalie_results_array = []

    if len(goalie_results_array) == 0:
        goalie_results_array.append(
            ['Name', 'Season', 'League', 'Team', 'GP', 'GAA', 'SV%', 'ID'])

    team_search_request = requests.get(team_url + '?tab=stats#players')
    team_page = html5lib.parse(team_search_request.text)

    team_name = team_page.find('.//*[@id="name-and-logo"]/{0}h1'.format(helpers.html_prefix)).text.strip()

    player_table = team_page.find(
        './/*[@id="players"]/{0}div[1]/{0}div[4]/{0}table'.format(helpers.html_prefix))
    goalies_table = team_page.find(
        './/*[@id="players"]/{0}div[2]/{0}div[2]/{0}table'.format(helpers.html_prefix))

    players_grouped = helpers.get_ep_table_rows(player_table)
    goalies_grouped = helpers.get_ep_table_rows(goalies_table)

    for group in players_grouped:
        for player in group:
            player_stats = player.findall(
                './/{}td'.format(helpers.html_prefix))

            name_link = player_stats[NAME].find(
                './{0}span/{0}a'.format(helpers.html_prefix))
            name, position = helpers.get_info_from_player_name(name_link.text)
            id = helpers.get_player_id_from_url(
                name_link.attrib['href'])
            games = player_stats[GAMES].text.strip()
            goals = player_stats[GOALS].text.strip()
            assists = player_stats[ASSISTS].text.strip()
            points = player_stats[POINTS].text.strip()
            pim = player_stats[PIM].text.strip()
            plusminus = player_stats[PLUSMINUS].text.strip()

            results_array.append([
                name,
                position,
                season,
                league_name,
                team_name,
                games,
                goals,
                assists,
                points,
                pim,
                plusminus,
                id,
            ])

    for goalie_group in goalies_grouped:
        for goalie in goalie_group:
            goalie_stats = goalie.findall('./{}td'.format(helpers.html_prefix))

            name_link = goalie_stats[GOALIE_NAME].find(
                './{0}a'.format(helpers.html_prefix))
            name = name_link.text.strip()
            id = helpers.get_player_id_from_url(
                name_link.attrib['href'])

            games = goalie_stats[GOALIE_GP].text.strip()
            gaa = goalie_stats[GOALIE_GAA].text.strip()
            svp = goalie_stats[GOALIE_SVP].text.strip()

            goalie_results_array.append([
                name,
                season,
                league_name,
                team_name,
                games,
                gaa,
                svp,
                id,
            ])
