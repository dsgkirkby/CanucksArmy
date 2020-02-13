import requests
import csv
import datetime
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup

#############################################################
#                                                           #
# Czech.py                                                  #
#   This scraper will gather information from all Czech     #
#   Extraliga games.                                        #
#                                                           #
#############################################################

###############
## FUNCTIONS ##
###############

def format_time(time):
    minutes = int(time[:time.index(":")])
    seconds = int(time[time.index(":")+1:])
    if minutes >= 60:
        minutes = minutes - 60
        if minutes == 65:
            period = 'SO'
        else:
            period = 'OT'
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
team_codes_array = []
player_array = []
player_teams_array = []
game_id_array = []
schedule_array = []
teams_array = []
goal_array = []
penalty_array = []
goalie_array = []
gf_onice_array = []
ga_onice_array = []
away_roster_array = []
home_roster_array = []

# Create new dictionaries
player_dict = {}
team_dict = {}

################
## Base URL's ##
################
teams_baseurl = "http://www.hokej.cz/tipsport-extraliga/tymy?teamList-filter-season={0}"
# Where {0} is the season - 1
stats_baseurl = "http://www.hokej.cz/tipsport-extraliga/stats-center?season={0}&competition=6026&yearFrom=&stranger=0&state=&stats-all=1"
# Where {0} is the season - 1
roster_baseurl = "http://www.hokej.cz/klub/{0}/soupiska?t=h9a58cmdbckardjfg9k42eyhqpfxt8hcvyah2f7pav3piqzxb8af8bx&rosterList-filter-season={1}"
# Where {0} is the club code and {1} is the season - 1
schedule_baseurl = "http://www.hokej.cz/tipsport-extraliga/zapasy?matchList-view-displayAll=1&matchList-filter-season={0}&matchList-filter-competition={1}"
# Where {0} is the season -1, {1} is the competition code
game_baseurl = "http://www.hokej.cz/zapas/{0}"
# Where {0} is the game code

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

# Constants
season = 2019
season_type = "Season"
league = "Czech"
compcode = 6238
# 2017-18 = 6026
# 2018-19 = 6238

print("Gathering...")

##-----------##-------------##-------------------------------------------------##
## SECTION 1 ##   PLAYERS   ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...player list")

##--------------##
## Player Stats ##
##--------------##

stats_url = stats_baseurl.format(str(season - 1))
stats_request = requests.get(stats_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )
stats_page = BeautifulSoup(stats_request.text, 'html.parser')
stats_table = stats_page.find("table", class_="table-stats")

stats_rows = stats_table.find_all('tr')
for rows_index in range(1, len(stats_rows)):
    player_data = stats_rows[rows_index].find_all('td')

    player_id = player_data[1].a.get('href').split("/")[2]
    player_gp = int(player_data[4].text)

    player_dict[player_id] = player_gp

##-----------##
## Team List ##
##-----------##

teams_url = teams_baseurl.format(str(season - 1))
teams_request = requests.get(teams_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )
teams_page = BeautifulSoup(teams_request.text, 'html.parser')
teams = teams_page.find_all("div", class_="col-25 box-team")

for team_index in range(0, len(teams)):
    team_link = teams[team_index].a.get('href')
    team_code = team_link.split("/")[2].split("?")[0]
    team_codes_array.append(team_code)

##-----------##
##  Rosters  ##
##-----------##

for roster_index in range(0, len(team_codes_array)):
    team_code = team_codes_array[roster_index]
    
    roster_url = roster_baseurl.format(str(team_code), str(season - 1))
    roster_request = requests.get(roster_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    roster_page = BeautifulSoup(roster_request.text, 'html.parser')

    team_title = roster_page.find("h2", class_="m-b-30").text
    team = team_title.replace('Soupiska ','').replace(' 2017-2018','')

    roster_tables = roster_page.find_all("table", class_="table-soupiska")

    for table_index in range(0, len(roster_tables)):
        roster_rows = roster_tables[table_index].find_all('tr')
        for row_index in range(1, len(roster_rows)):
            player_data = roster_rows[row_index].find_all('td')

            # Find and format player name
            player_name = player_data[1].text

            # Find and format player id
            id_link = player_data[1].a.get('href')
            player_id = id_link.split("/")[2].split("?")[0]

            # Find and format position
            if table_index == 0:
                position = "G"
            elif table_index == 1:
                position = "D"
            elif table_index == 2:
                position = "F"

            # Find and format birthdate
            birthdate = player_data[2].text
            if "." in birthdate:
                #print(player_name, birthdate)
                year = int(birthdate.split(".")[2])
                month = int(birthdate.split(".")[1])
                day = int(birthdate.split(".")[0])
                birthdate = datetime.date(year, month, day)
            else:
                birthdate = ""
            
            # Find and format height, weight, and handedness
            height = player_data[5].text.split(' ')[0]
            weight = player_data[6].text.split(' ')[0]
            if player_data[4].text == "levá":
                handedness = "Left"
            elif player_data[4].text == "pravá":
                handedness = "Right"

            # Add player gp from player_dict
            try:
                player_gp = player_dict[player_id]
            except:
                player_gp = ''

            player_array.append([
                player_name,
                position,
                season,
                season_type,
                league,
                team,
                '',
                birthdate,
                '',
                height,
                weight,
                handedness,
                player_gp,
                player_id
            ])

##-----------##-------------##-------------------------------------------------##
## SECTION 2 ##  SCHEDULE   ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...schedule")

schedule_url = schedule_baseurl.format(str(season - 1),compcode)
schedule_request = requests.get(schedule_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )
schedule_page = BeautifulSoup(schedule_request.text, 'html.parser')
schedule_rounds = schedule_page.find_all("table", class_="preview m-b-30")

# For all rounds, go to len(schedule_rounds)
for round_index in range(0, len(schedule_rounds)):
    round_games = schedule_rounds[round_index].find_all('tr')

    for game_index in range(0, len(round_games)):
        try:
            # Find and format game id
            game_id_link = round_games[game_index].a.get('href')
            game_id = game_id_link.split("/")[2]
            print(game_id)

            # Find and format date
            date = round_games[game_index].find("span", class_="match-start-time").text
            month = int(date.split(' ')[2].replace('.',''))
            day = int(date.split(' ')[1].replace('.',''))
            if month > 6:
                year = season - 1
            elif month < 6:
                year = season
            date = str(datetime.date(year, month, day))
            #date = str(year) + "-" + str(month) + "-" + str(day)
            
            # Find and format teams
            teams = round_games[game_index].find_all("span", class_="preview__name--long")
            away_team = teams[1].text
            home_team = teams[0].text

            # Find and format score and home/away goals
            score = round_games[game_index].find_all("td", class_="preview__score")
            away_goals = int(score[1].text)
            home_goals = int(score[0].text)

            # Format winning and losing teams
            if away_goals > home_goals:
                winning_team = away_team
                losing_team = home_team
            elif home_goals > away_goals:
                winning_team = home_team
                losing_team = away_team

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

            # Add away team to team_dict
            team_abrv = round_games[game_index].find("span", class_="preview__name--short").text
            team_full = round_games[game_index].find("span", class_="preview__name--long").text
            if team_abrv not in teams_array:
                teams_array.append(team_abrv)
                team_dict[team_abrv] = team_full

    ##        print("Game ID:", game_id)
    ##        print("Date:", date)
    ##        print("Away team:", away_team)
    ##        print("Home team:", home_team)
    ##        print("Away score:", away_goals)
    ##        print("Home score:", home_goals)
    ##        print("Winning team:", winning_team)
    ##        print("Losing team:", losing_team)

        except: None

print(team_dict)

##-----------##-------------##-------------------------------------------------##
## SECTION 3 ##    GAMES    ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...games")

print(len(game_id_array))

# For full list of games, go to len(game_id_array)
for game_index in range(1, len(game_id_array)):

    game_id = schedule_array[game_index][3]
    # Format date, teams from schedule array
    date = schedule_array[game_index][4]
    away_team = schedule_array[game_index][5]
    home_team = schedule_array[game_index][6]
    print(game_id)

    game_url = game_baseurl.format(game_id)
    game_request = requests.get(game_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    game_page = BeautifulSoup(game_request.text, 'html.parser')

    ##---------##
    ## ROSTERS ##
    ##---------##

    home_roster = game_page.find("div", class_="col-100 col-soupisky-home")
    away_roster = game_page.find("div", class_="col-100 col-soupisky-visitor")
    
    home_roster_rows = home_roster.table.find_all('tr')
    for rows_index in range(1, len(home_roster_rows)):
        player = home_roster_rows[rows_index].find_all('td')
        if len(player) > 1:
            player_name = player[2].text.title()
##            print(game_id, player_name)
            home_roster_array.append(player_name)

    away_roster_rows = away_roster.table.find_all('tr')
    for rows_index in range(1, len(away_roster_rows)):
        player = away_roster_rows[rows_index].find_all('td')
        if len(player) > 1:
            player_name = player[2].text.title()
            away_roster_array.append(player_name)

    away_roster = ','.join(''.join(elems) for elems in away_roster_array)
    home_roster = ','.join(''.join(elems) for elems in home_roster_array)
    away_roster_array.clear()
    home_roster_array.clear()
    schedule_array[game_index][11] = away_roster
    schedule_array[game_index][12] = home_roster
    
    ##-------##
    ## GOALS ##
    ##-------##    
    periods = game_page.find_all("table", class_="table-last-right")

    for period_index in range(0, len(periods)):
        goals = periods[period_index].find_all('tr')

        for goal_index in range(1, len(goals)):
            if "row-plus-minus" not in goals[goal_index]:
                goal_data = goals[goal_index].find_all('td')

                if len(goal_data) > 2:
                    # Format period
                    period = period_index + 1
                    if period == 4:
                        period = 'OT'
                    elif period == 5:
                        period = 'SO'

                    # Format time
                    time = goal_data[0].text
                    time = format_time(time)

                    # Format team
                    team_abrv = goal_data[1].text
                    try:
                        team = team_dict[team_abrv]
                    except:
                        team = team_abrv
                    if team == away_team:
                        gf_team = away_team
                        ga_team = home_team
                    elif team == home_team:
                        gf_team = home_team
                        ga_team = away_team
                    else:
                        gf_team = team
                        ga_team = ''

                    # Format goal scorer
                    scorer = goal_data[2].text.replace('\n','')
                    if "(" in scorer:
                        scorer = scorer[:scorer.index("(")-1]
                    scorer = scorer.title()

                    # Format assists
                    assists = goal_data[3].find_all('a')
                    if len(assists) > 0:
                        assist1 = assists[0].text
                        if len(assists) > 1:
                            assist2 = assists[1].text
                        else:
                            assist2 = ''
                    else:
                        assist1 = ''
                    if "(" in assist1:
                        assist1 = assist1[:assist1.index("(")-1]
                    if "(" in assist2:
                        assist2 = assist2[:assist2.index("(")-1]
                    assist1 = assist1.title()
                    assist2 = assist2.title()

                    # Format on-ice players
                    try:
                        gf_onice_raw = goals[goal_index + 1].find_all('a')
                        for onice_index in range(0, len(gf_onice_raw)):
                            gf_onice_array.append(gf_onice_raw[onice_index].text)
                        gf_onice = ','.join(''.join(elems) for elems in gf_onice_array)
                    except: gf_onice = ''

                    try:
                        ga_onice_raw = goals[goal_index + 2].find_all('a')
                        for onice_index in range(0, len(ga_onice_raw)):
                            ga_onice_array.append(ga_onice_raw[onice_index].text)
                        ga_onice = ','.join(''.join(elems) for elems in ga_onice_array)
                    except: ga_onice = ''
                    gf_onice_array.clear()
                    ga_onice_array.clear()

                    # Format strength
                    gf_strength = len(gf_onice_raw) - 1
                    ga_strength = len(ga_onice_raw) - 1
                    strength = str(gf_strength) + "v" + str(ga_strength)

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
                    
##                    print(game_id, "Period:", period)
##                    print(game_id, "Time:", time)
##                    print(game_id, "Team:", team)
##                    print(game_id, "Scorer:", scorer)
##                    print(game_id, "Assist 1:", assist1)
##                    print(game_id, "Assist 2:", assist2)
##                    print(game_id, "GF Onice:", gf_onice)
##                    print(game_id, "GA Onice:", ga_onice)
##                    print(game_id, "Strength:", strength)
##                    print(" ")

                    # Reset variables
                    scorer = ''
                    assist1 = ''
                    assist2 = ''
                    gf_team = ''
                    ga_team = ''
                    strength = ''
                    gf_onice = ''
                    ga_onice = ''
                

# EXPORT ARRAYS TO CSV FILES
helpers.export_array_to_csv(player_array, '{0}-{1}-players.csv'.format(league, season))
helpers.export_array_to_csv(schedule_array, '{0}-{1}-schedule.csv'.format(league, season))
helpers.export_array_to_csv(goal_array, '{0}-{1}-goals.csv'.format(league, season))
#helpers.export_array_to_csv(boxscore_array, '{0}-{1}-playerbox.csv'.format(league, season))

print("Complete")






