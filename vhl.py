import requests
import csv
import datetime
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
positions_array = []
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
away_name_dict = {}
home_name_dict = {}
player_dict = {}
player_team_dict = {}
player_shots_dict = {}
player_toi_dict = {}

stats_baseurl = "http://www.vhlru.ru/en/stats/players/{0}/"
# Where {0} is the season code
players_baseurl = "http://www.vhlru.ru/en/players/amplua/?type={0}#c"
# Where {0} is the first letter
schedule_baseurl = "http://www.vhlru.ru/en/calendar/{0}/"
# Where {0} is the season code
game_baseurl = "http://www.vhlru.ru/en/report/{0}/?idgame={1}"
# Where {0} is the season code and {1} is the game code

# Initialize array values
game_id_array.append(['Game ID'])
player_array.append(['Player', 'Position', 'Season', 'Season Type', 'League', 'Team',
                     'Age', 'Birthdate', 'Birthplace', 'Height', 'Weight', 'Hand', 'GP', 'TOI', 'Shots'])

schedule_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                       'Visiting Team', 'Home Team', 'Visitor GF', 'Home GF',
                       'Winning Team', 'Losing Team', 'Away Roster', 'Home Roster'])

goal_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                   'GF Team', 'GA Team', 'Period', 'Time',
                   'Scorer', 'Assist1', 'Assist2',
                   'Score State', 'Strength', 'Plus', 'Minus', 'Situation'])

letters_array.append(['A','B','C','D','E','F','G','H','I','J','K','L','M','N',
                      'O','P','Q','R','S','T','U','V','W','X','Y','Z'])

positions_array.append(['forward','defense'])

# Constants
season_id = 704
# For 2018-19
season = 2019
season_type = "Season"
league = "VHL"

print("Gathering...")

##-----------##-------------##-------------------------------------------------##
## SECTION 1 ##   PLAYERS   ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...player list")

##--------------##
## PLAYER STATS ##
##--------------##

stats_url = stats_baseurl.format(season_id)
stats_request = requests.get(stats_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )
stats_page = BeautifulSoup(stats_request.text, 'html.parser')
position_tables = stats_page.find_all("div", class_="playerstats")

for position_index in range(1, 3):
    print(position_tables[position_index].h2.text)
    player_rows = position_tables[position_index].find_all('tr')

    for player_index in range(2, len(player_rows)):
        player_data = player_rows[player_index].find_all('td')

        # Find and format player id
        player_id_link = player_data[0].a.get('href').split("players/")
        player_id = player_id_link[1].replace("/","")

        # Find and format player name
        player_name = player_data[0].text
        player_name = name_swap(player_name)

        # Find and format team name
        team_name = player_data[2].text

        # Find and format games played
        player_gp = player_data[3].text

        # Find and format shots on goal
        player_shots = player_data[14].text
        player_shots_dict[player_id] = player_shots

        # Find and format TOI (if available for skaters)
        try:
            player_toi = player_data[20].text.strip()
        except:
            player_toi = ''
        player_toi_dict[player_id] = player_toi

        # Add to player and team dictionaries
        player_dict[player_id] = player_gp
        player_team_dict[player_id] = team_name

##print(player_dict)
##print("")
##print(player_team_dict)

##-------------##
## PLAYER BIOS ##
##-------------##

for positions_array_index in range(0, len(positions_array[0])):
    position = positions_array[0][positions_array_index]
    players_url = players_baseurl.format(position)
    print(players_url) ##
    players_request = requests.get(players_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    players_page = BeautifulSoup(players_request.text, 'html.parser')
    player_table = players_page.find("table", class_="players_list uni_table")

    player_rows = player_table.find_all('tr')

    for row_index in range(1, len(player_rows)):
        player_data = player_rows[row_index].find_all('td')

        # Find and format player id
        player_id_link = player_data[0].a.get('href').split("players/")
        player_id = player_id_link[1].replace("/#c","")

        # Find and format player name
        player_name = player_data[0].text.replace('\n','').strip()
        player_name = name_swap(player_name)

        # Find and format position
        player_pos = player_data[1].text[0]

        # Find and format birthdate
        birthdate_split = player_data[3].text.split(".")
        year = int(birthdate_split[2])
        month = int(birthdate_split[1])
        day = int(birthdate_split[0])
        player_birthdate = str(datetime.date(year, month, day))

        # Get team and games played from dictionaries
        try:
            player_team = player_team_dict[player_id]
            player_gp = player_dict[player_id]
            player_shots = player_shots_dict[player_id]
            player_toi = player_toi_dict[player_id]
        except:
            player_team = ""
            player_gp = 0

        if int(player_gp) > 0:
            print(player_name, player_id, player_birthdate, player_team, player_gp)

            player_array.append([
                player_name,
                player_pos,
                season,
                season_type,
                league,
                player_team,
                '',
                player_birthdate,
                '',
                '',
                '',
                '',
                player_gp,
                player_shots,
                player_toi,
                player_id
            ])

            print(player_id, player_name, player_pos, player_birthdate, player_team, player_gp, player_toi, player_shots)

helpers.export_array_to_csv(player_array, '{0}-{1}-players.csv'.format(league, season))

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
schedule = schedule_page.find("table", class_="uni_table matches")
dates = schedule.find_all("td", class_="date")
date_games = schedule.find_all("table", class_="matches_table_inner")

#print(dates[1])

# for all dates, use len(dates)
for dates_index in range(0, len(dates)):
#dates_index = 1
    # Format date
    date_split = dates[dates_index].h4.text.split(".")
    year = int(date_split[2]) + 2000
    month = int(date_split[1])
    day = int(date_split[0])
    date = str(datetime.date(year, month, day))
    
    games = date_games[dates_index].find_all('tr')
    #games_index = 1
    for games_index in range(0, len(games)):
        game_info = games[games_index].find_all('td')

        # Find game id
        game_id_link = game_info[2].a.get('href').split("=")
        game_id = game_id_link[1]

        # Find teams
        team_names = game_info[1].text.replace('\n','').split(" - ")
        away_team = team_names[0].strip()
        home_team = team_names[1].strip()

        # Find score and home/away goals
        game_score = game_info[2].text.split(" ")[0].strip().split(":")
        away_goals = int(game_score[0])
        home_goals = int(game_score[1])

        # Format winning team and losing teams
        if away_goals > home_goals:
            winning_team = away_team
            losing_team = home_team
        elif home_goals > away_goals:
            winning_team = home_team
            losing_team = away_team

        # Add game id to game_id_array
        game_id_array.append(game_id)

        print(date, game_id, away_team, home_team, away_goals, home_goals)

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
    away_name_dict.clear()
    home_name_dict.clear()

    game_url = game_baseurl.format(season_id, game_id)
    game_request = requests.get(game_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    game_page = BeautifulSoup(game_request.text, 'html.parser')
    

    # Format date, teams from schedule array
    date = schedule_array[game_index][4]
    away_team = schedule_array[game_index][5]
    home_team = schedule_array[game_index][6]
    # Reset score counters to zero
    home_score = 0
    away_score = 0

    try:
        ##---------##
        ## ROSTERS ##
        ##---------##

        player_rosters = game_page.find("div", class_="matches_player_statistic")
        roster_tables = player_rosters.find_all('table')
        #print(len(roster_tables))

        for roster_index in range(0,6):
            roster_players = roster_tables[roster_index].find_all('tr')

            for players_index in range(1, len(roster_players)):
                player_data = roster_players[players_index].find_all('td')

                player_num = player_data[0].text
                player_name = player_data[1].text.replace('\n','').replace('  ','').replace('  ',' ').strip()
                #" ".join(player_name.split())
                if "(" in player_name:
                    player_name = player_name.split("(")[0]
                player_name = name_swap(player_name)

                

                # Add name and number to Name Dictionary
                #     and players to roster arrays
                if roster_index is 0 or roster_index is 1 or roster_index is 2:
                    away_name_dict[player_num] = player_name
                    away_roster_array.append(player_name)
                    #print(roster_index, "away", player_num, player_name)
                elif roster_index is 3 or roster_index is 4 or roster_index is 5:
                    home_name_dict[player_num] = player_name
                    home_roster_array.append(player_name)
                    #print(roster_index, "home", player_num, player_name)

        away_roster = ','.join(''.join(elems) for elems in away_roster_array)
        home_roster = ','.join(''.join(elems) for elems in home_roster_array)
        away_roster_array.clear()
        home_roster_array.clear()
        schedule_array[game_index][11] = away_roster
        schedule_array[game_index][12] = home_roster    

        ##-------##
        ## GOALS ##
        ##-------##

        goals_table = game_page.find("table", class_="tablesorter matches_goals")
        goals = goals_table.find_all('tr')
        for goal_index in range(1, len(goals)):
            goal_data = goals[goal_index].find_all('td')

            # Find and format period
            period = goal_data[1].text.replace('\n','').strip()

            # Find and format time
            time = goal_data[2].text.strip()
            time = format_time(time)

            # Format score
            score = goal_data[3].text.strip()
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

            # Find and format goal scorer
            scorer = goal_data[5].text.split(".")[1].split("(")[0]
            scorer = name_swap(scorer)

            # Find and format first assist
            if "." in goal_data[6].text:
                assist1 = goal_data[6].text.split(".")[1].split("(")[0]
                assist1 = name_swap(assist1)
            else: assist1 = ''

            # Find and format second assist
            if "." in goal_data[7].text:
                assist2 = goal_data[7].text.split(".")[1].split("(")[0]
                assist2 = name_swap(assist2)
            else: assist2 = ''

            # Find and format on-ice numbers
            away_onice_numbers = goal_data[8].text.split(",")
            home_onice_numbers = goal_data[9].text.split(",")
            for onice_index in range (0, len(away_onice_numbers)):
                player_num = away_onice_numbers[onice_index]
                away_onice_array.append(player_num)
            for onice_index in range (0, len(home_onice_numbers)):
                player_num = home_onice_numbers[onice_index]
                home_onice_array.append(player_num)
            away_onice = numbers_to_names(away_name_dict, away_onice_array)
            home_onice = numbers_to_names(home_name_dict, home_onice_array)

            if goal_side is 'home':
                gf_onice = home_onice
                ga_onice = away_onice
            elif goal_side is 'away':
                gf_onice = away_onice
                ga_onice = home_onice

            # Format Strength
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

            print(game_id, period, time, score, gf_team, ga_team, scorer)
    except: None

# EXPORT ARRAYS TO CSV FILES

helpers.export_array_to_csv(schedule_array, '{0}-{1}-schedule.csv'.format(league, season))
helpers.export_array_to_csv(goal_array, '{0}-{1}-goals.csv'.format(league, season))
#helpers.export_array_to_csv(boxscore_array, '{0}-{1}-playerbox.csv'.format(league, season))

print("Complete")
