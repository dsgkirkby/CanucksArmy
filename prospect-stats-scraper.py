#!/usr/bin/python

__author__ = 'dylan'

import requests
import re
import sys
import csv
from bs4 import BeautifulSoup
NAME = 1
GAMES = 3
GOALS = 4
ASSISTS = 5
POINTS = 6
PIM = 8
PLUSMINUS = 9

""" PLAYER STAT PARSER """

def get_player_points(league, season):

	resultsArray = [['Name','GP','G','A','TP','PIM','+/-']]
	namesArray = []
	pageIndex = 1
	done = False

	while not done:
		url = "http://www.eliteprospects.com/league.php?currentpage={0}&season={1}&leagueid={2}".format(str(pageIndex), str(season), str(league))
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

				playerName = playerStats[NAME].a.text
				if playerName in namesArray:
					done = True
					break

				namesArray.append(playerName)
				resultsArray.append([
					playerName, 
					playerStats[GAMES].text,  
					playerStats[GOALS].text, 
					playerStats[ASSISTS].text, 
					playerStats[POINTS].text,
					playerStats[PIM].text,
					playerStats[PLUSMINUS].text])

		pageIndex += 1

	with open('{0}-{1}.csv'.format(str(league), str(season)), 'w', newline='') as csvFile:
		csvWriter = csv.writer(csvFile)
		for resultRow in resultsArray:
			csvWriter.writerow(resultRow)

	print("done")

""" MAIN """

def main():
	if len(sys.argv) < 3:
		print("Usage: expects 2 arguments - name of league (i.e. 'QMJHL') and season (start year only, i.e. '2015' for 2015-16)")
		return
	get_player_points(sys.argv[1], sys.argv[2])

main()
