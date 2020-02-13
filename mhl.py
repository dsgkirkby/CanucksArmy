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

stats_baseurl = "https://engmhl.khl.ru/stat/players/{0}/all/"
# Where {0} is the season code
players_baseurl = "https://engmhl.khl.ru/players/tournament/{0}/"
# Where {0} is the first letter
schedule_baseurl = "https://engmhl.khl.ru/calendar/{0}/0/0/"
# Where {0} is the season code
game_box_baseurl = "https://engmhl.khl.ru/game/{0}/{1}/summary/"
# Where {0} is the season code and {1} is the game code
game_team_baseurl = "https://engmhl.khl.ru/game/{0}/{1}/teams/"
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
season_id = 677
# For 2018-19
season = 2019
season_type = "Season"
league = "MHL"

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
stats_div = stats_page.find("div", class_="stat_players")
stats_tables = stats_div.find_all("table", class_="site_table site_table-denser")
for table_index in range(0, len(stats_tables)):
    table_rows = stats_tables[table_index].find_all('tr')
    for row_index in range(1, len(table_rows)):
        player_data = table_rows[row_index].find_all('td')

        # Find and format player id
        player_id = player_data[1].a.get('href').split("/")[2]

        # Find and format player name
        player_name = player_data[1].text
        player_name = name_swap(player_name)

        # Find and format team
        team_name = player_data[3].text.replace('\n','').strip()

        # Find and format player gp
        player_gp = player_data[4].text

        # Find and format player shots
        player_shots = player_data[15].text
        player_shots_dict[player_id] = player_shots

        # Find and format TOI (if available to skaters)
        try:
            player_toi = player_data[21].text.strip()
        except:
            player_toi = ''
        player_toi_dict[player_id] = player_toi

        # Add to player and team dictionaries
        player_dict[player_id] = player_gp
        player_team_dict[player_id] = team_name

##print(player_dict)
##print('')
##print(player_team_dict)

##-------------##
## PLAYER BIOS ##
##-------------##

players_url = players_baseurl.format(season_id)
players_request = requests.get(players_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )
players_page = BeautifulSoup(players_request.text, 'html.parser')
players_scripts = players_page.find_all('script')

for script_index in range(0, len(players_scripts)):
    if "var _Data" in players_scripts[script_index].text:
        stats_table_script = script_index

stats_rows = players_scripts[stats_table_script].text.split("var _Data  = [")[1].split("[")
print(stats_rows[1])

for row_index in range(1, len(stats_rows)-2):
    if "players_list_thumb" in stats_rows[row_index]:
        # Find and format player id
        player_id = stats_rows[row_index].split("/players/")[1].split("/")[0]

        # Find and format player name
        player_name = stats_rows[row_index].split(">")[4].split("<")[0]
        #print(player_name)
        player_name = name_swap(player_name)

        player_data = stats_rows[row_index].split(",")

        # Find and format player position
        player_pos = player_data[2].replace("'","")[0]

        # Find and format player birthday
        player_birthdate = player_data[3].replace("'","")

        # Find and format player nationality
        player_nationality = player_data[5].replace("'","")
        if (">") in player_nationality:
            player_nationality = player_nationality.split(">")[1].strip()

        # Find and format player handedness
        player_shot = player_data[6].replace("'","")

        # Find and format player weight
        player_weight = player_data[7].replace("'","")

        # Find and format player height
        player_height = player_data[8].replace("'","")

        # Get team and games played from dictionaries
        try:
            player_team = player_team_dict[player_id]
            player_gp = player_dict[player_id]
            player_shots = player_shots_dict[player_id]
            player_toi = player_toi_dict[player_id]
        except:
            player_team = ""
            player_gp = 0

        player_array.append([
                player_name,
                player_pos,
                season,
                season_type,
                league,
                player_team,
                '',
                player_birthdate,
                player_nationality,
                player_height,
                player_weight,
                player_shot,
                player_gp,
                player_shots,
                player_toi,
                player_id
            ])

        print(player_id, player_name, player_pos, player_birthdate, player_team, player_shot, player_height, player_gp, player_toi, player_shots)

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
schedule_days = schedule_page.find_all("div", class_="calendar_dayitems")

#print(len(schedule_days))

# for full schedule, use len(schedule_days)
for days_index in range (0, len(schedule_days)):
    # Find and format date
    date = schedule_days[days_index].find("div", class_="b_calendar_items_day_date ib").text.split(",")[0]

    day_games = schedule_days[days_index].find_all("div", class_="col-xs-12 col-lg-6 ")
    #print(date, len(day_games))   

    for game_index in range(0, len(day_games)):
        game_id_link = day_games[game_index].find("div", class_="b_calendar_item_popup_row").a.get('href')
        game_id = game_id_link.split("/")[3]

        # Find and format Away Team
        away_team = day_games[game_index].find("div", class_="b_calendar_item_col b_calendar_item_col-right")
        away_team = away_team.find("div", class_="b_calendar_item_team_name").text.strip()

        # Find and format Home Team
        home_team = day_games[game_index].find("div", class_="b_calendar_item_col b_calendar_item_col-left")
        home_team = home_team.find("div", class_="b_calendar_item_team_name").text.strip()

        try:
            # Find and format Score
            score_str = day_games[game_index].find("div", class_="b_calendar_item_col b_calendar_item_col-center")
            score_str = score_str.find("div", class_="b_calendar_item_game_score").find_all('div')
            #print(date, game_id, len(score_str))
            home_goals = int(score_str[0].text)
            if len(score_str) is 3:
                away_goals = int(score_str[2].text)
            elif len(score_str) is 4:
                away_goals = int(score_str[3].text)
            
            # Format winning team and losing teams
            if away_goals > home_goals:
                winning_team = away_team
                losing_team = home_team
            elif home_goals > away_goals:
                winning_team = home_team
                losing_team = away_team
        except:
            home_goals = ''
            away_goals = ''
            winning_team = ''
            losing_team = ''

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
    away_name_dict.clear()
    home_name_dict.clear()

    ##---------##
    ## ROSTERS ##
    ##---------##

    game_team_url = game_team_baseurl.format(season_id, game_id)
    game_team_request = requests.get(game_team_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    game_team_page = BeautifulSoup(game_team_request.text, 'html.parser')
    

    # Format date, teams from schedule array
    date = schedule_array[game_index][4]
    away_team = schedule_array[game_index][5]
    home_team = schedule_array[game_index][6]
    # Reset score counters to zero
    home_score = 0
    away_score = 0

    print(date, game_id)
    
    forward_tables = game_team_page.find_all("table", class_="team_table tablesorter c_for")
    #print(date, game_id, len(forward_tables))

    for table_index in range(0,2):
        table_rows = forward_tables[table_index].find_all('tr')
        for row_index in range(1, len(table_rows)):
            player_data = table_rows[row_index].find_all('td')

            # Find and format player number
            player_num = player_data[0].text

            try:
                # Find and format player id
                player_id = player_data[2].a.get('href').split("/")[2]

                # Find and format player name
                player_name = player_data[2].text.strip()
                player_name = name_swap(player_name)

                # Add name and number to Name Dictionary
                #     and players to roster arrays
                if table_index is 1:
                    away_name_dict[player_num] = player_name
                    away_roster_array.append(player_name)
                    #print(table_index, "away", player_num, player_name)
                elif table_index is 0:
                    home_name_dict[player_num] = player_name
                    home_roster_array.append(player_name)
                    #print(table_index, "home", player_num, player_name)
            except:
                player_id = ''
                player_name = ''

    defence_tables = game_team_page.find_all("table", class_="team_table tablesorter c_def")
    #print(date, game_id, len(defence_tables))

    for table_index in range(0,2):
        table_rows = defence_tables[table_index].find_all('tr')
        for row_index in range(1, len(table_rows)):
            player_data = table_rows[row_index].find_all('td')

            # Find and format player number
            player_num = player_data[0].text

            try:
                # Find and format player id
                player_id = player_data[2].a.get('href').split("/")[2]

                # Find and format player name
                player_name = player_data[2].text.strip()
                player_name = name_swap(player_name)

                # Add name and number to Name Dictionary
                #     and players to roster arrays
                if table_index is 1:
                    away_name_dict[player_num] = player_name
                    away_roster_array.append(player_name)
                    #print(table_index, "away", player_num, player_name)
                elif table_index is 0:
                    home_name_dict[player_num] = player_name
                    home_roster_array.append(player_name)
                    #print(table_index, "home", player_num, player_name)
            except:
                player_id = ''
                player_name = ''

    away_roster = ','.join(''.join(elems) for elems in away_roster_array)
    home_roster = ','.join(''.join(elems) for elems in home_roster_array)
    away_roster_array.clear()
    home_roster_array.clear()
    schedule_array[game_index][11] = away_roster
    schedule_array[game_index][12] = home_roster

    ##-------##
    ## GOALS ##
    ##-------##

    game_box_url = game_box_baseurl.format(season_id, game_id)
    game_box_request = requests.get(game_box_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    game_box_page = BeautifulSoup(game_box_request.text, 'html.parser')

    goal_table = game_box_page.find("table", class_="protocol_table")
    
    table_rows = goal_table.find_all('tr')
    for rows_index in range(1, len(table_rows)):
        goal_data = table_rows[rows_index].find_all('td')

        # Find and format period
        period = goal_data[1].text.replace('\n','').strip()

        # Find and format time
        time = goal_data[2].text.strip()
        time = format_time(time)

        # Format score
        score = goal_data[3].text.strip()
        score_split = score.split(":")
        if int(score_split[1]) > away_score:
            away_score = int(score_split[1])
            goal_side = 'away'
        elif int(score_split[0]) > home_score:
            home_score = int(score_split[0])
            goal_side = 'home'
        if goal_side is 'away':
            gf_team = away_team
            ga_team = home_team
        elif goal_side is 'home':
            gf_team = home_team
            ga_team = away_team

        # Find and format goal scorer
        scorer = goal_data[5].text
        if "(" in scorer:
            scorer = scorer[scorer.index(".")+1:scorer.index("(")]
        else:
            scorer = scorer[scorer.index(".")+1:].strip()
        scorer = name_swap(scorer)

        # Find and format first assist
        if "." in goal_data[6].text:
            assist1 = goal_data[6].text
            assist1 = assist1[assist1.index(".")+1:assist1.index("(")]
            assist1 = name_swap(assist1)
        else: assist1 = ''

        # Find and format second assist
        if "." in goal_data[7].text:
            assist2 = goal_data[7].text
            assist2 = assist2[assist2.index(".")+1:assist2.index("(")]
            assist2 = name_swap(assist2)
        else: assist2 = ''

        # Find and format on-ice numbers
        away_onice_numbers = goal_data[9].text.split(",")
        home_onice_numbers = goal_data[8].text.split(",")
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

        #print(game_id, rows_index, period, gf_team, ga_team, scorer, assist1, assist2)

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
helpers.export_array_to_csv(schedule_array, '{0}-{1}-schedule.csv'.format(league, season))
helpers.export_array_to_csv(goal_array, '{0}-{1}-goals.csv'.format(league, season))

print("Complete")
