import requests
from bs4 import BeautifulSoup

NAME = 0
POS = 2
TEAM = 3
SHOTS = 17
TOI = 19


def get_nhl_season_icetime(season: int, results_array=None):
    if results_array is None:
        results_array = []

    if len(results_array) == 0:
        results_array.append(['Name', 'Position', 'Season', 'Team', 'Shots', 'TOI'])

    team_search_request = requests.get('http://www.hockey-reference.com/leagues/NHL_{0}_skaters.html'.format(season))
    team_page = BeautifulSoup(team_search_request.text, "html.parser")

    def stats_table(tag):
        return tag.has_attr('id') and tag.attrs['id'] == 'stats'

    player_table = team_page.find(stats_table).find('tbody')

    def player_row(tag):
        return tag.name == 'tr' and not (tag.has_attr('class') and 'thead' in tag.attrs['class'])

    players = player_table.find_all(player_row)

    for playerIndex in range(0, len(players)):
        player = players[playerIndex]
        player_stats = player.find_all('td')

        name = player_stats[NAME].a.text.strip()
        position = player_stats[POS].text.strip()
        team = player_stats[TEAM].text.strip()
        shots = player_stats[SHOTS].text.strip()
        toi = player_stats[TOI].text.strip()

        results_array.append([
            name,
            position,
            season,
            team,
            shots,
            toi,
        ])
