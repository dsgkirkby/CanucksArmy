#!/usr/bin/python

__author__ = 'dylan'

import requests
import re
import sys
import csv
import html5lib
from bs4 import BeautifulSoup

""" ROSTER PARSER """

def get_player_rosters(league, season):

	league = str(league)
	season = str(season)

	resultsArray = [[]]
	namesArray = []

	""" Find the link to the league's team list """

	leagueSearchUrl = "http://www.eliteprospects.com/league_central.php"
	leagueSearchRequest = requests.get(leagueSearchUrl)

	""" Find an <a> tag with the league name in its text """
	def league_link(tag):
		return tag.name == 'a' and tag.text.strip().lower() == league.lower() and len(re.findall('league_home.php', tag.attrs['href'], re.IGNORECASE)) > 0

	leagueSearchPage = leagueSearchRequest.text.replace('<br>', '<br/>')
	leagueSearchPage = BeautifulSoup(leagueSearchPage, "html.parser")
	leagueLink = leagueSearchPage.find(league_link)

	""" Find all team IDs """

	def roster_title(tag):
		return tag.name == 'div' and tag.text.strip().lower() == 'team rosters'

	teamSearchUrl = "http://www.eliteprospects.com/" + leagueLink.attrs['href'] + "&startdate=" + season
	teamSearchRequest = requests.get(teamSearchUrl)

	# All tag names have this prepended to them
	htmlPrefix = '{http://www.w3.org/1999/xhtml}'
	teamSearchPage = html5lib.parse(teamSearchRequest.text)
	#xpath: /html/body/div[2]/table[3]/tbody/tr/td[5]/table[3]
	teamTable = teamSearchPage.find('./{0}body/{0}div[2]/{0}table[3]/{0}tbody/{0}tr/{0}td[5]/{0}table[3]'.format(htmlPrefix))
	
	teams = teamTable.findall('.//{0}tbody/{0}tr/{0}td/{0}a'.format(htmlPrefix))

	teamUrls = []

	for team in teams:
		teamUrls.append(team.attrib['href'])

	for teamUrl in teamUrls:
		teamPageRequest = requests.get('http://www.eliteprospects.com/{0}&year0={1}'.format(teamUrl, season))
		teamPage = BeautifulSoup(teamPageRequest.text, "html.parser")
		def global_nav(tag):
			return tag.has_attr('id') and tag.attrs['id'] == 'globalnav'
		playerTable = teamPage.find(global_nav).next_sibling
		print(playerTable)
		break


""" MAIN """

def main():
	if len(sys.argv) < 3:
		print("Usage: expects 2 arguments - name of league (i.e. 'QMJHL') and season (start year only, i.e. '2015' for 2014-15)")
		return
	get_player_rosters(sys.argv[1], sys.argv[2])

main()
