import requests
import csv
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup

#############################################################
#                                                           #
# KHL.py                                                    #
#   This scraper will gather information from all Russian   #
#   KHL games.                                              #
#                                                           #
#############################################################

###############
## FUNCTIONS ##
###############

def findnth(haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)

def name_swap(fullname):
    #name_split = fullname.split(" ")
    lastname = fullname[:fullname.index(" ")]
    firstname = fullname[fullname.index(" ")+1:]
    name = firstname + " " + lastname
    return name
    
def numbers_to_names(name_dict, onice):
    names = []
    for oniceIndex in range(0, len(onice)):
        player_num = onice[oniceIndex]
        try:
            names.append([
                name_dict[player_num]
            ])
        except KeyError:
            names.append(player_num)
    onice_new = ','.join(''.join(elems) for elems in names)
    return onice_new

def format_time(time):
    minutes = int(time[:time.index(":")])
    seconds = int(time[time.index(":")+1:])
    if minutes >= 60:
        period = 4
        minutes = minutes - 60
    elif minutes >= 40:
        period = 3
        minutes = minutes - 40
    elif minutes >= 20:
        period = 2
        minutes = minutes - 20
    else:
        period = 1
    if seconds < 10:
        new_time = str(minutes) + ":0" + str(seconds)
    else:
        new_time = str(minutes) + ":" + str(seconds)
    return new_time

# Large scale arrays to be used in this program
player_array = []
letters_array = []
player_teams_array = []
game_id_array = []
schedule_array = []
goal_array = []
penalty_array = []
goalie_array = []
away_onice_array = []
home_onice_array = []
away_roster_array = []
home_roster_array = []

# Create new dictionaries
name_dict = {}
player_dict = {}

stats_baseurl = "https://en.khl.ru/stat/players/{0}/skaters/"
# Where {0} is the season code
players_baseurl = "https://en.khl.ru/players/season/{0}/"
# Where {0} is the first letter
schedule_baseurl = "https://en.khl.ru/calendar/{0}/00/"
# Where {0} is the season code
game_baseurl = "https://en.khl.ru/game/{0}/{1}/protocol/"
# Where {0} is the season code and {1} is the game code

# Initialize array values
game_id_array.append(['Game ID'])
player_array.append(['Player', 'Position', 'Season', 'Season Type', 'League', 'Team',
                     'Age', 'Birthdate', 'Birthplace', 'Height', 'Weight', 'Shot', 'GP'])

schedule_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                       'Visiting Team', 'Home Team', 'Visitor GF', 'Home GF',
                       'Winning Team', 'Losing Team', 'Away Roster', 'Home Roster'])

goal_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                   'GF Team', 'GA Team', 'Period', 'Time',
                   'Scorer', 'Assist1', 'Assist2',
                   'Score State', 'Strength', 'Plus', 'Minus', 'Situation'])

letters_array.append(['A','B','C','D','E','F','G','H','I','J','K','L','M','N',
                      'O','P','Q','R','S','T','U','V','W','X','Y','Z'])

# Constants
season_id = 671
# For 2018-19
season = 2019
season_type = "Season"
league = "KHL"

print("Gathering...")

##-----------##-------------##-------------------------------------------------##
## SECTION 1 ##   PLAYERS   ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...player list")

##--------------##
## PLAYER STATS ##
##--------------##

##stats_url = stats_baseurl.format(season_id)
##stats_request = requests.get(stats_url,
##                            data=None,
##                            headers={
##                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
##                                }
##                            )
##stats_page = BeautifulSoup(stats_request.text, 'html.parser')
##stats_scripts = stats_page.find_all('script')
##
##for script_index in range(0, len(stats_scripts)):
##    if "var skaters_Data" in stats_scripts[script_index].text:
##        stats_table_script = script_index
##
##stats_rows = stats_scripts[stats_table_script].text.split("[")
##
##print(stats_rows[0])
##
### For full table, use len(stats_rows)        
##for rows_index in range(1, len(stats_rows)):
##    if "," in stats_rows[rows_index]:
##        player_data = stats_rows[rows_index].split(",")
##        try:
##            player_id = player_data[0].split("<")[2].split("/")[2]
##            player_gp = int(player_data[3].replace('"','').replace(' ',''))
##            player_dict[player_id] = player_gp
##        except: None

##-------------##
## PLAYER BIOS ##
##-------------##

##for letter_index in range(0, 1):
##    letter = letters_array[0][letter_index]
##    print(letter_index) ##
##    print(letter) ##
    
##players_url = players_baseurl.format(season_id)
##print(players_url) ##
##players_request = requests.get(players_url,
##                            data=None,
##                            headers={
##                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
##                                }
##                            )
##players_page = BeautifulSoup(players_request.text, 'html.parser')
##
##players_scripts = players_page.find_all('script')
##
##print("1", len(players_scripts))
##print(players_scripts[27])
##for script_index in range(0, len(players_scripts)):
##    print("Script number:", script_index)
##    if "var _Data" in players_scripts[script_index].text:
##        print("Found var _Data")
##        players_table_script = script_index
##        print("1", players_scripts[players_table_script])
##
##        players_section = players_scripts[players_table_script].text.split("var _Data")[1]
##        print(players_section)
##        players_rows = players_section.text.split("[")
##
##        # For full table, use len(players_rows)        
##        for rows_index in range(1, len(players_rows)):
##            if "," in players_rows[rows_index]:
##                player_data = players_rows[rows_index].split(",")
##                try:
##                    player_id = player_data[0].split("<")[2].split("/")[2]
##                    player_gp = int(player_data[3].replace('"','').replace(' ',''))
##                    player_dict[player_id] = player_gp
##                except: None
    
##    players_table = players_page.find("table", id_="players_dataTable")
##    #players_sections = players_page.find_all("div", class_="b-content_section m-stats")
##    print(players_table)
##    players = players_table.find_all('tr')
##
##    # For full list, run to len(players)
##    for player_index in range(1, len(players)):
##        player = players[player_index].find_all('td')
##
##        ## Format name
##        player_name = player[0].text.replace('\n','')    
##        player_name = name_swap(player_name)
##
##        ## Find player ID
##        player_id = player[0].a.get('href').split("/")[2]
##
##        ## Format position
##        position = player[2].text[:1]
##        position = position.upper()
##
##        ## Format team(s)
##        team = player[1].text
##        if team.count(")") is 1:
##            team = team[:team.index("(")-1]
##        elif team.count(")") > 1:
##            teams = team.split(")")
##            for team_index in range(0, len(teams)-1):
##                player_teams_array.append(teams[team_index][:teams[team_index].index("(")-1])
##            team = ' / '.join(''.join(elems) for elems in player_teams_array)
##            player_teams_array.clear()
##                                          
##        ## Format birthdate
##        birthdate = player[3].text
##        while birthdate[0] is ' ':
##            birthdate = birthdate[1:]
##
##        ## Format nationality
##        nationality = player[5].text.replace('&nbsp;','').replace(' ','')
##
##        ## Import GP from Player Dictionary
##        try:
##            player_gp = player_dict[player_id]
##        except: player_gp = 0
##
##        player_array.append([
##            player_name,
##            position,
##            season,
##            season_type,
##            league,
##            team,
##            '',
##            birthdate,
##            nationality,
##            '',
##            '',
##            '',
##            player_gp,
##            player_id
##        ])

##-----------##-------------##-------------------------------------------------##
## SECTION 2 ##  SCHEDULE   ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...schedule")

schedule_url = schedule_baseurl.format(season_id)
schedule_request = requests.get(schedule_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )
schedule_page = BeautifulSoup(schedule_request.text, 'html.parser')
schedule = schedule_page.find(id="tab-calendar-last").find('div')
dates = schedule.find_all("div", class_="b-final_cup_date")
days = schedule.find_all("div", class_="m-future")

for day_index in range(0, len(days)):
    # Format date
    date = dates[day_index].b.text
    date = date[:date.index(",")]
    while date[0] is ' ':
            date = date[1:]
            
    day_games = days[day_index].find_all("li", class_="b-wide_tile_item")

    for game_index in range(0, len(day_games)):
        # Find game id
        game_id_link = day_games[game_index].find("div", class_="b-title-option-inner").ul.li.a.get('href').split("/")
        game_id = game_id_link[3]
        
        # Find teams
        team_names = day_games[game_index].find_all('h5')
        away_team = team_names[0].text
        home_team = team_names[1].text
        
        # Find score and home/away goals
        game_score = day_games[game_index].find('h3').text.split(" ")
        away_goals = int(game_score[0])
        home_goals = int(game_score[2])
        
        # Format winning team and losing teams
        if away_goals > home_goals:
            winning_team = away_team
            losing_team = home_team
        elif home_goals > away_goals:
            winning_team = home_team
            losing_team = away_team

        # Make sure season code matches (do not include All-Star games)
        if int(game_id_link[2]) == int(season_id):
        
            # Add game id to game_id_array
            game_id_array.append(game_id)

            # Add game information to schedule array
            schedule_array.append([
                season,
                season_type,
                league,
                game_id,
                date,
                away_team,
                home_team,
                away_goals,
                home_goals,
                winning_team,
                losing_team,
                '',''
            ])

##-----------##-------------##-------------------------------------------------##
## SECTION 3 ##    GAMES    ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...games")

# For full list of games, go to len(game_id_array)
for game_index in range(1, len(game_id_array)):

    game_id = schedule_array[game_index][3]

    # Clear Name Dictionary for a new game
    name_dict.clear()

    game_url = game_baseurl.format(season_id, game_id)
    game_request = requests.get(game_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    game_page = BeautifulSoup(game_request.text, 'html.parser')
    game_scripts = game_page.find_all('script')

    # Format date, teams from schedule array
    date = schedule_array[game_index][4]
    away_team = schedule_array[game_index][5]
    home_team = schedule_array[game_index][6]
    # Reset score counters to zero
    home_score = 0
    away_score = 0

    for script_index in range(0, len(game_scripts)):
        if "var data_goals" in game_scripts[script_index].text:
            goals_script = script_index
        elif "var data_goalies_A" in game_scripts[script_index].text:
            roster_start_script = script_index

    ##---------##
    ## ROSTERS ##
    ##---------##
    for roster_index in range(roster_start_script, roster_start_script+6):
        players = game_scripts[roster_index].text.split("[")
        
        for player_index in range(1, len(players)):
            if "," in players[player_index]:
                player_data = players[player_index].split(",")

                player_num = player_data[0]
                player_name = player_data[1]
                try:
                    player_num = player_num[player_num.index("onice")+5:player_num.index("'>")]
                    player_name = player_name[player_name.index("/'>")+3:player_name.index("</a>")]
                    player_name = name_swap(player_name)
                except: None

                # Add name and number to Name Dictionary
                name_dict[player_num] = player_name

                # Add players to roster arrays
                if "Ap" in player_num:
                    away_roster_array.append(player_name)
                elif "Bp" in player_num:
                    home_roster_array.append(player_name)
    
    away_roster = ','.join(''.join(elems) for elems in away_roster_array)
    home_roster = ','.join(''.join(elems) for elems in home_roster_array)
    away_roster_array.clear()
    home_roster_array.clear()
    schedule_array[game_index][11] = away_roster
    schedule_array[game_index][12] = home_roster
   
    ##-------##
    ## GOALS ##
    ##-------##
    goals = game_scripts[goals_script].text.split("[")

    for goal_index in range(0, len(goals)):
        onice_start = findnth(goals[goal_index], ",", 7)
        
        if "," in goals[goal_index]:
            goal_data = goals[goal_index].split(",")

            period = goal_data[1].replace('"','').replace(' ','')

            ## Format time
            time = goal_data[2].replace('"','').replace("′′","").replace("′",":").replace(' ','')
            time = format_time(time)
                
            ## Format score
            score = goal_data[3].replace('"','').replace(' ','')
            score_split = score.split(":")
            if int(score_split[0]) > away_score:
                away_score = int(score_split[0])
                goal_side = 'away'
            elif int(score_split[1]) > home_score:
                home_score = int(score_split[1])
                goal_side = 'home'
            if goal_side is 'away':
                gf_team = away_team
                ga_team = home_team
            elif goal_side is 'home':
                gf_team = home_team
                ga_team = away_team
                
            ## Format goal scorer
            scorer = goal_data[5][goal_data[5].index(". ")+2:]
            if "(" in scorer:
                scorer = scorer[:goal_data[5].index("(")-1]
            scorer = name_swap(scorer)
            
            ## Format first assist
            if ". " in goal_data[6]:
                assist1 = goal_data[6][goal_data[6].index(". ")+2:goal_data[6].index("(")]
                assist1 = name_swap(assist1)
            else: assist1 = ''
            
            ## Format second assist
            if ". " in goal_data[7]:
                assist2 = goal_data[7][goal_data[7].index(". ")+2:goal_data[7].index("(")]
                assist2 = name_swap(assist2)
            else: assist2 = ''
            
            ## Format on-ice numbers
            onice_all = goals[goal_index][onice_start:].split("#onice")
            for onice_index in range(0, len(onice_all)):
                player_num = onice_all[onice_index][:onice_all[onice_index].index("'")]
                if "Ap" in player_num:
                    away_onice_array.append(player_num)
                elif "Bp" in player_num:
                    home_onice_array.append(player_num)
            away_onice = numbers_to_names(name_dict, away_onice_array)
            home_onice = numbers_to_names(name_dict, home_onice_array)
            if goal_side is 'home':
                gf_onice = home_onice
                ga_onice = away_onice
            elif goal_side is 'away':
                gf_onice = away_onice
                ga_onice = home_onice
          
            ## Format strength
            away_strength = len(away_onice_array)-1
            home_strength = len(home_onice_array)-1
            strength = str(away_strength) + "v" + str(home_strength)
            away_onice_array.clear()
            home_onice_array.clear()

            ## Add to Goals array
            goal_array.append([
                season,
                season_type,
                league,
                game_id,
                date,
                gf_team,
                ga_team,
                period,
                time,
                scorer,
                assist1,
                assist2,
                '',strength,
                gf_onice,
                ga_onice
            ])
                
# EXPORT ARRAYS TO CSV FILES
helpers.export_array_to_csv(player_array, '{0}-{1}-players.csv'.format(league, season))
helpers.export_array_to_csv(schedule_array, '{0}-{1}-schedule.csv'.format(league, season))
helpers.export_array_to_csv(goal_array, '{0}-{1}-goals.csv'.format(league, season))
#helpers.export_array_to_csv(boxscore_array, '{0}-{1}-playerbox.csv'.format(league, season))

print("Complete")
