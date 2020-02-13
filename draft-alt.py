import requests
import csv
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup
 
###################################################
#                                                 #
# draft-alt.py                                    #
#   This scraper will gather information from the #
#   'Draft' section of EliteProspects             #
#                                                 #
###################################################

# CONSTANTS
#season = 2018
first_season = 2019
last_season = 2019

# Large scale arrays to be used in this program
draft_array = []

draft_array.append(['Year', 'Round', 'Number', 'Team', 'Name', 'Position', 'Seasons', 'Games', 'Goals', 'Assists', 'Points', 'PIM', 'Birthday', 'Player ID'])

draft_url = "https://www.eliteprospects.com/draft/nhl-entry-draft/{0}"

for seasonIndex in range(first_season, last_season + 1):
    print(seasonIndex)
    url = draft_url.format(seasonIndex)
    season = seasonIndex
    draft_request = requests.get(url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    draft_page = BeautifulSoup(draft_request.text, 'html.parser')
    draft_table = draft_page.find("table", class_="table table-striped players table-sortable highlight-stats")

    draft_rounds = draft_table.find_all('tbody')

    # the 1st tbody is the Round 1 Header
    for roundIndex in range(1, len(draft_rounds)):
        round_rows = draft_rounds[roundIndex].find_all('tr')
        for rowIndex in range(0, len(round_rows)):
            round_data = round_rows[rowIndex].find_all('td')

            if len(round_data) > 1:
                overall = round_data[0].text.replace(' ','').replace('#','').replace('\n','')
                team = round_data[1].text.replace('\n','')
                playerinfo = round_rows[rowIndex].find("td", class_="player")
                # pull player ID from link
                try:
                    player_link = playerinfo.a.get('href')
                    playercode = player_link.split('player/')[1]
                    playerid = playercode.split('/')[0]
                    name_pos = playerinfo.span.text.replace('\n','')
                    if "(" in name_pos:
                        playername = name_pos[0:name_pos.index('(')-1]    
                        pos = name_pos[name_pos.index('(')+1:name_pos.index(')')]
                    else:
                        playername = name_pos
                        pos = ""
                except:
                    playerid = ""
                    playername = "nul"
                    pos = ""
                # pull player name and position
                
                seasons = round_rows[rowIndex].find("td", class_="seasons").text.replace('\n','')
                games = round_rows[rowIndex].find("td", class_="gp").text.replace('\n','')
                goals = round_rows[rowIndex].find("td", class_="g").text.replace('\n','')
                assists = round_rows[rowIndex].find("td", class_="a").text.replace('\n','')
                points = round_rows[rowIndex].find("td", class_="tp").text.replace('\n','')
                pims = round_rows[rowIndex].find("td", class_="pim").text.replace('\n','')

                # Navigate to player page to find player birthday
    ##            try:
    ##                player_url = "https://www.eliteprospects.com/player/{0}".format(playercode)
    ##                player_request = requests.get(player_url,
    ##                                                data=None,
    ##                                                headers={
    ##                                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    ##                                                    }
    ##                                                )
    ##                player_page = BeautifulSoup(player_request.text, 'html.parser')
    ##                player_table = player_page.find("div", class_="table-view")
    ##                birthday = player_table.find('div').find('div').find('ul').find('li').find_all('div')[1].text.replace('\n','')
    ##                birthday = birthday[1:len(birthday)-1]
    ##                print(overall, player_url, birthday)
    ##            except:
    ##                birthday = ""
                birthday = ""

                draft_array.append([
                    season,
                    roundIndex,
                    overall,
                    team,
                    playername,
                    pos,
                    seasons,
                    games,
                    goals,
                    assists,
                    points,
                    pims,
                    birthday,
                    playerid
                ])

# EXPORT ARRAYS TO CSV FILES
helpers.export_array_to_csv(draft_array, 'draft-alternate-{0}-{1}.csv'.format(first_season, last_season))

print("Complete")
            
