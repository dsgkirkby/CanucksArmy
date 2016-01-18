#!/usr/bin/python

import requests
import re
import sys
import csv
import helpers
from bs4 import BeautifulSoup

__author__ = 'dylan'

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


def get_player_points(league, season):
    league = str(league)

    resultsArray = [['Name', 'Position', 'Season', 'League', 'Team', 'GP', 'G', 'A', 'TP', 'PIM', '+/-']]
    playerIds = []
    pageIndex = 1
    done = False

    while not done:
        url = "http://www.eliteprospects.com/league.php?currentpage={0}&season={1}&leagueid={2}".format(str(pageIndex), str(int(season) - 1), league)
        r = requests.get(url)

        regex = re.compile('PLAYER STATS')

        pageText = r.text.replace('<br>', '<br/>')

        soup = BeautifulSoup(pageText, "html.parser")
        playerTable = soup.find(text=regex).parent.parent.find_all("table")[2]

        players = playerTable.find_all('tr')

        for playerIndex in range(0, len(players)):
            """ Discard the title row """
            if playerIndex == 0:
                continue
            else:
                player = players[playerIndex]
                playerStats = player.find_all('td')

                """ Only add to the array if the row isn't blank """
                if playerStats[NAME].a is None or '-' in playerStats[GOALS]:
                    continue

                playerId = helpers.get_player_id(playerStats)
                if playerId in playerIds:
                    done = True
                    break

                playerTeam = playerStats[TEAM].text
                if (playerTeam == 'totals'):
                    playerTeam = 'multiple'

                playerIds.append(playerId)
                resultsArray.append([
                    playerStats[NAME].a.text,
                    playerStats[NAME].font.text.strip()[1:-1],
                    season,
                    league,
                    playerTeam,
                    playerStats[GAMES].text,
                    playerStats[GOALS].text,
                    playerStats[ASSISTS].text,
                    playerStats[POINTS].text,
                    playerStats[PIM].text,
                    playerStats[PLUSMINUS].text])

        pageIndex += 1

    with open('{0}-{1}-stats.csv'.format(league, season), 'w', newline='') as csvFile:
        csvWriter = csv.writer(csvFile)
        for resultRow in resultsArray:
            csvWriter.writerow(resultRow)

    print("Scraping completed successfully.")


""" MAIN """


def main():
    if len(sys.argv) < 3:
        print("Usage: expects 2 arguments - name of league (i.e. 'QMJHL') and season (start year only, i.e. '2015' for 2014-15)")
        return
    get_player_points(sys.argv[1], sys.argv[2])


main()
