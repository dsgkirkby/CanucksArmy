import requests
import csv
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup
 
###################################################
#                                                 #
# inthesystem.py                                  #
#   This scraper will gather information from the #
#   'In the System' section of EliteProspects     #
#                                                 #
###################################################
 
# Large scale arrays to be used in this program
teams_array = []
system_array = []
team_dict = {}

system_array.append(['PlayerID','Name','Team','Pos'])

# Gather team id's

teams_url = "https://www.eliteprospects.com/league/nhl"

url = teams_url
teams_request = requests.get(url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )
teams_page = BeautifulSoup(teams_request.text, 'html.parser')

teams_list = teams_page.find("div", class_="list-as-columns")

# teams_list = teams_tables[15]

print(teams_list)


teams = teams_list.find_all('li')
for listIndex in range(0, len(teams)):
    team_link = teams[listIndex].a.get('href')
    team_code = team_link.split('/team/')[1]
    team_name = teams[listIndex].a.text
    team_name = helpers.strip_extra_spaces(team_name).replace('\n','')
    team_name = team_name[1:len(team_name)-1]   # to do: strip extra line breaks, start at [1]
    teams_array.append(team_code)

##    print(team_link)
##    print(team_code)
##    print(team_name)

##    teams_data = teams_rows[listIndex].find_all('td')
##    
##    for colIndex in range(0, len(teams_data)):
##        if teams_data[colIndex].a is not None:
##            team_link = teams_data[colIndex].a.get('href')
##            team_code = team_link.split('=')[1]
##            team_name = teams_data[colIndex].text.replace('\n ','')
##            if team_name[len(team_name)-1] is ' ':
##                team_name = team_name[:len(team_name)-1]
##            
##            teams_array.append(team_code)

    # Add team to dictionary
    team_dict[team_code] = team_name

print(team_dict)

# Gather players from In the System section of team pages

system_baseurl ="http://www.eliteprospects.com/in_the_system.php?team={0}"

for teamIndex in range(0, len(teams_array)):
    print("Scraping ",teams_array[teamIndex],team_dict[teams_array[teamIndex]])
    url = system_baseurl.format(teams_array[teamIndex])
    system_request = requests.get(url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    system_page = BeautifulSoup(system_request.text, 'html.parser')
    system_table = system_page.find("table", class_="table table-striped table-sortable in-the-system highlight-stats")
    

    system_rows = system_table.find('tbody').find_all('tr')
    
    #row one was header row (defunct)

    for rowIndex in range(0, len(system_rows)):
        player = system_rows[rowIndex].find_all('td')
        if '.' in player[0].text:
            player_link = player[2].a.get('href')
            playerid = player_link.split('player/')[1]
            playerid = playerid.split('/')[0]
            name_pos = player[2].span.text
            name = name_pos[1:name_pos.index('(')-1]    
            pos = name_pos[name_pos.index('(')+1:name_pos.index(')')]

            # Pull team name from dictionary
            team = team_dict[teams_array[teamIndex]]

            system_array.append([
                playerid,
                name,
                team,
                pos
            ])
        
# EXPORT ARRAYS TO CSV FILES
helpers.export_array_to_csv(system_array, 'EP-in-the-system.csv')

print("Complete")
    
