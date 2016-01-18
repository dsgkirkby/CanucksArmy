#!/usr/bin/python

__author__ = 'dylan'

import requests
import re
import sys
import csv
import html5lib
from bs4 import BeautifulSoup

ID = 0
NAME = 1
DOB = 3
HOMETOWN = 4
HEIGHT = 5
WEIGHT = 6
SHOOTS = 7

METRIC = 0
IMPERIAL = 1

""" ROSTER PARSER """


def get_player_rosters(league, season):
    league = str(league)
    season = str(season)

    resultsArray = [['Name', 'Position', 'Season', 'League', 'DOB', 'Hometown', 'Height', 'Weight', 'Shoots']]
    playerIds = []

    """ Get the league link """

    leagueSearchUrl = "http://www.eliteprospects.com/league_central.php"
    leagueSearchRequest = requests.get(leagueSearchUrl)

    """ Find an <a> tag with the league name in its text """

    def league_link(tag):
        return tag.name == 'a' and tag.text.strip().lower() == league.lower() and len(
            re.findall('league_home.php', tag.attrs['href'], re.IGNORECASE)) > 0

    leagueSearchPage = leagueSearchRequest.text.replace('<br>', '<br/>')
    leagueSearchPage = BeautifulSoup(leagueSearchPage, "html.parser")
    leagueLink = leagueSearchPage.find(league_link)

    """ Get the teams' links """

    def roster_title(tag):
        return tag.name == 'div' and tag.text.strip().lower() == 'team rosters'

    teamSearchUrl = "http://www.eliteprospects.com/" + leagueLink.attrs['href'] + "&startdate=" + str(int(season) - 1)
    teamSearchRequest = requests.get(teamSearchUrl)

    # All tag names have this prepended to them
    htmlPrefix = '{http://www.w3.org/1999/xhtml}'
    teamSearchPage = html5lib.parse(teamSearchRequest.text)
    # xpath: /html/body/div[2]/table[3]/tbody/tr/td[5]/table[5]
    teamTable = teamSearchPage.find(
        './{0}body/{0}div[2]/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}table[5]'.format(htmlPrefix))

    teams = teamTable.findall('.//{0}tbody/{0}tr/{0}td[2]/{0}a'.format(htmlPrefix))
    teamUrls = []

    onFirstRow = True

    for team in teams:
        if onFirstRow:
            onFirstRow = False
            continue
        teamUrls.append(team.attrib['href'])

    """ Get the players """

    for teamUrl in teamUrls:
        teamPageRequest = requests.get('http://www.eliteprospects.com/{0}'.format(teamUrl))
        teamPage = BeautifulSoup(teamPageRequest.text, "html.parser")

        def global_nav(tag):
            return tag.has_attr('id') and tag.attrs['id'] == 'globalnav'

        playerTable = teamPage.find(global_nav).next_sibling

        players = playerTable.find_all('tr')

        for playerIndex in range(0, len(players)):
            """ Discard the title row """
            if playerIndex == 0:
                continue
            else:
                player = players[playerIndex]
                playerStats = player.find_all('td')

                """ Only add to the array if the row isn't blank """
                if playerStats[ID].font is not None:
                    continue

                playerId = get_player_id(playerStats)
                if playerId in playerIds:
                    break

                playerIds.append(playerId)
                resultsArray.append([
                    playerStats[NAME].a.text,
                    playerStats[NAME].font.text.strip()[1:-1],
                    season,
                    league,
                    playerStats[DOB].text,
                    playerStats[HOMETOWN].a.text,
                    playerStats[HEIGHT].find_all('span')[METRIC].text,
                    playerStats[WEIGHT].find_all('span')[METRIC].text,
                    playerStats[SHOOTS].text])

    with open('{0}-{1}-rosters.csv'.format(league, season), 'w', newline='') as csvFile:
        csvWriter = csv.writer(csvFile)
        for resultRow in resultsArray:
            csvWriter.writerow(resultRow)

    print("Scraping completed successfully.")


""" HELPER FUNCTIONS """


def get_player_id(player):
    return player[ID].text + player[NAME].a.text


""" MAIN """


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: expects 2 arguments - name of league (i.e. 'QMJHL') and season (end year only, i.e. '2015' for 2014-15)")
        return
    get_player_rosters(sys.argv[1], sys.argv[2])


main()
