import requests
import csv
import datetime
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup

###################################################
#                                                 #
# NCAA.py                                         #
#   This scraper will gather information from all #
#   NCAA games for 2017-18.                       #
#                                                 #
###################################################

###############
## FUNCTIONS ##
###############

def name_swap(fullname):
    name_split = fullname.split(",")
    lastname = name_split[0]
    firstname = name_split[1]
    name = firstname + " " + lastname
    return name

# Function to convert on-ice numbers to on-ice names
##  Inputs:
##      - onice: on-ice numbers, separated by ','
##      - team:  abbreviated team name, for dictionary
def numbers_to_names(name_dict, onice, team):
    names = []
    if ',' in onice:
        numbers = onice.split(",")
        for oniceIndex in range(0, len(numbers)):
            if 'G' not in numbers[oniceIndex]:
                player_code = str(team + numbers[oniceIndex])
                try:
                    names.append([
                        name_dict[str(player_code)]
                    ])
                except KeyError:
                    names.append(player_code)
        onice_new = ','.join(''.join(elems) for elems in names)
    else:
        onice_new = ''
    return onice_new

# Large scale arrays to be used in this program
game_array = []
teams_array = []
player_array = []
schedule_array = []
goal_array = []
boxscore_array = []
penalty_array = []
goalie_array = []
home_roster_array = []
away_roster_array = []

# Create new dictionaries
player_dict = {}
name_dict = {}

################
## Base URL's ##
################

stats_baseurl = "https://www.collegehockeynews.com/stats/team/{0}"
roster_baseurl = "https://www.collegehockeynews.com/reports/roster/{0}"
game_baseurl = "http://www.collegehockeystats.net/{0}/gamesheet/{1}"
text_baseurl = "http://collegehockeyinc.com/stats/tboxes{0}.php?{1}"

# Initialize large scale arrays
game_array.append('Game ID')
player_array.append(['Player', 'Position', 'Season', 'Season Type', 'League', 'Team',
                     'Age', 'Birthdate', 'Birthplace', 'Height', 'Weight', 'Shot', 'GP'])
schedule_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                       'Visiting Team', 'Home Team', 'Visitor GF', 'Home GF',
                       'Winning Team', 'Losing Team', 'Away Roster', 'Home Roster',
                       'Total Time', '5-on-5 Time',
                       'Notes'])
goal_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                    'GF Team', 'GA Team', 'Period', 'Time',
                    'Scorer', 'Assist1', 'Assist2', 'Score State', 'Strength',
                    'Plus', 'Minus', 'Situation'])
boxscore_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                     'Team', 'No.', 'Name', 'Goals', 'Assists', 'Points',
                     'PIMs', 'SOG', '+/-'])

# Constants
season = 2019
season_type = "Season"
league = "NCAA"
season_code = str(season - 2001) + str(season - 2000)

print("Gathering...")

##-----------##-------------##-------------------------------------------------##
## SECTION 1 ##   PLAYERS   ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...player list")

##---------##
##  TEAMS  ##
##---------##

# GET THE TEAM LIST PAGE
teams_request = requests.get('https://www.collegehockeynews.com/reports/team/',
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )

teams_page = BeautifulSoup(teams_request.text, 'html.parser')
teams_tables = teams_page.find_all('div')
for conferenceIndex in range(28, 34):
    teams_group = teams_tables[conferenceIndex].find_all('p')

    for teamIndex in range(0, len(teams_group)):
        team_link = teams_group[teamIndex].a.get('href')
        team_id = team_link[team_link.index("team/")+5:]
        teams_array.append([team_id])
        #print(team_id)

# For loop through all rosters in teams_array len(teams_array)
for rosterIndex in range(0, len(teams_array)):

    # ---------
    #   STATS
    # ---------
    
    stats_url = stats_baseurl.format(*teams_array[rosterIndex])
    # REQUEST THE TEAM STATS PAGE
    stats_request = requests.get(stats_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    stats_page = BeautifulSoup(stats_request.text, 'html.parser')
    #print(stats_page)
    stats_table = stats_page.find('tbody')

    stats_players = stats_table.find_all('tr')

    for playerIndex in range(0, len(stats_players)):
        player_stats = stats_players[playerIndex].find_all('td')
        player_link = player_stats[0].a.get('href')
        player_id = player_link[len(player_link)-5:]
        player_gp = player_stats[1].text

        # Add player_id to Player Dictionary
        player_dict[player_id] = player_gp
        print(player_id, player_dict[player_id])

    # -----------
    #   ROSTERS
    # -----------

    roster_url = roster_baseurl.format(*teams_array[rosterIndex])
    # REQUEST THE TEAM ROSTER
    roster_request = requests.get(roster_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    roster_page = BeautifulSoup(roster_request.text, 'html.parser')
    title = roster_page.title.string
    #team_name = title[title.index("18")+3:title.index("Roster")-1]
    team_name = title[:title.index("18")-3]
    print(team_name)
    roster_table = roster_page.find_all('tbody')
    
    for positionIndex in range(0, len(roster_table)):
        
        roster_players = roster_table[positionIndex].find_all('tr')
        #print(roster_players)

        for playerIndex in range(0,len(roster_players)):
            player_info = roster_players[playerIndex].find_all('td')
            if len(player_info) > 8:
                try:
                    roster_name = player_info[2].text.replace(' ','')
                    print("  ",roster_name)
                    name = name_swap(roster_name)
                    position = player_info[4].text
                    birthdate = player_info[7].text.replace(' ','')
                    birthplace = player_info[8].text
                    height = player_info[5].text
                    weight = player_info[6].text
                    
                    player_link = player_info[0].a.get('href')
                    player_id = player_link[len(player_link)-5:]
                    try:
                        games = player_dict[player_id]
                    except KeyError:
                        games = ''

                    #Format birthdate
                    try:
                        birthday_split = birthdate.split("/")
                        birthdate = str(birthday_split[2] + "-" + birthday_split[0] + "-" + birthday_split[1])
                    except:
                        None
                        
                    #print(player_id, games)

                    player_array.append([
                        name,
                        position,
                        season,
                        season_type,
                        league,
                        team_name,
                        '',
                        birthdate,
                        birthplace,
                        height,
                        weight,
                        '',
                        games
                    ])
                except:
                    None
                
##-----------##-------------##-------------------------------------------------##
## SECTION 2 ##  SCHEDULE   ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...schedule")

# GET THE SCHEDULE
schedule_request = requests.get('http://collegehockeyinc.com/stats/compnatfull19.php',
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )

schedule_page = BeautifulSoup(schedule_request.text, 'html.parser')
schedule = schedule_page.find('table')
games = schedule.find_all("tr", bgcolor="#EEEEEE")

print(len(games), "games found.")

# len(games)
for gameIndex in range(0, len(games)):
    game = games[gameIndex]
    game_info = game.find_all('td')

    # Filters out monthly headers
    if len(game_info) > 1:

        # Filters out unplayed games
        if u'\xa0' not in game_info[3]:

            # Filter out exhibition games
##            if 'Exhibition' not in game_info[9].text:
            
            try:
                # Pull Game ID from link
                link = games[gameIndex].a.get('href')
                game_id = link[link.index("?")+1:]
                print("Adding",game_id,"to schedule.")
                # Add to game array for use in boxscores
                game_array.append([game_id])

                # Format date
                date = game_info[1].text.split("/")
                month = int(date[0])
                day = int(date[1])
                year = int(date[2]) + 2000
                date = str(datetime.date(year, month, day))

                # Format teams
                away_team = game_info[2].text
                home_team = game_info[4].text[3:]

                # Format goals
                away_goals = game_info[3].text
                home_goals = game_info[5].text
                if " " in away_goals:
                    away_goals = away_goals[:away_goals.index(" ")]
                if " " in home_goals:
                    home_goals = home_goals[:home_goals.index(" ")]
                notes = game_info[9].text

                # Format winning and losing teams
                if int(away_goals) > int(home_goals):
                    winning_team = away_team
                    losing_team = home_team
                elif int(home_goals) > int(away_goals):
                    winning_team = home_team
                    losing_team = away_team

                # Add Schedule information to schedule array
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
                    losing_team,'','',
                    '','',
                    notes
                ])
            except:
                None

##-----------##-------------##-------------------------------------------------##
## SECTION 3 ##    GAMES    ##                                                 ##
##-----------##-------------##-------------------------------------------------##
print("...games")

# For loop through all games in game_array len(game_array)
for gameIndex in range(1, len(game_array)):

    # Pull date, teams from schedule array
    game_id = str(*game_array[gameIndex])
    date = schedule_array[gameIndex][4]
    notes = schedule_array[gameIndex][15]
    total_time = 60

    print(game_id)

    ##---------------##
    ## TEXT BOXSCORE ##
    ##---------------##
    
    # REQUEST THE INDIVIDUAL GAME'S TEXT BOXSCORE
    text_request = requests.get(text_baseurl.format(str(season - 2000), *game_array[gameIndex]),
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    text_page = BeautifulSoup(text_request.text, 'html.parser')

    game_text = text_page.find('div', class_="offset-top-10 offset-md-top-10 text-left").text.replace('\n','')
    teams_text = game_text[:game_text.index("Date")]
    #print(teams_text)

    if " at " in teams_text:
        teams_split = teams_text.split(" at ")

        away_team = teams_split[0][:teams_split[0].index("(")-1]
        away_team_abrv = teams_split[0][teams_split[0].index("(")+1:teams_split[0].index(")")]
        home_team = teams_split[1][:teams_split[1].index("(")-1]
        home_team_abrv = teams_split[1][teams_split[1].index("(")+1:teams_split[1].index(")")]

    elif " vs " in teams_text:
        teams_split = teams_text.split(" vs ")

        away_team = teams_split[0][:teams_split[0].index("(")-1]
        away_team_abrv = teams_split[0][teams_split[0].index("(")+1:teams_split[0].index(")")]
        home_team = teams_split[1][:teams_split[1].index("(")-1]
        home_team_abrv = teams_split[1][teams_split[1].index("(")+1:teams_split[1].index(")")]

    ##----------##
    ## BOXSCORE ##
    ##----------##

    # Clear Name Dictionary for a new game
    name_dict.clear()
        
    # REQUEST THE INDIVIDUAL GAME'S BOXSCORE
    game_request = requests.get(game_baseurl.format(season_code, *game_array[gameIndex]),
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    game_page = BeautifulSoup(game_request.text, 'html.parser')

    game_tables = game_page.find_all('table')

    ##---------##
    ## ROSTERS ##
    ##---------##

    # Gather data from tables 10 (away team) and 11 (home team)
    for teamIndex in range(10, 12):
        players_table = game_tables[teamIndex]
        players = players_table.find_all('tr')[1:]

        for playerIndex in range(0, len(players)):
            player = players[playerIndex].find_all('td')

            if len(player) > 7:   
                box_number = player[0].text
                box_name = player[1].text.title()
                box_g = player[2].text
                box_a = player[3].text
                box_p = player[4].text
                box_pim = player[5].text
                box_sog = player[6].text
                box_pm = player[7].text

                if teamIndex is 10:
                    team = away_team
                    team_abrv = away_team_abrv
                elif teamIndex is 11:
                    team = home_team
                    team_abrv = home_team_abrv
                
                # Add player to Name Dictionary
                name_dict[str(team_abrv + box_number)] = box_name

                #print(name_dict)
                        
                boxscore_array.append([
                    season,
                    season_type,
                    league,
                    team,
                    game_id,
                    date,
                    box_number,
                    box_name,
                    box_g,
                    box_a,
                    box_p,
                    box_pim,
                    box_sog,
                    box_pm,
                    str(team_abrv + box_number),
                    name_dict[str(team_abrv + box_number)]
                ])

                if team == home_team:
                    home_roster_array.append(box_name)
                elif team == away_team:
                    away_roster_array.append(box_name)
                    
    away_roster = ','.join(''.join(elems) for elems in away_roster_array)
    home_roster = ','.join(''.join(elems) for elems in home_roster_array)
    away_roster_array.clear()
    home_roster_array.clear()
    schedule_array[gameIndex][11] = away_roster
    schedule_array[gameIndex][12] = home_roster

    ##-------------##
    ## GOALS TABLE ##
    ##-------------##
    goals_table = game_tables[8]
    goals = goals_table.find_all('tr')[1:]

    for goalIndex in range(0, len(goals)):
        goal_info = goals[goalIndex].find_all('td')

        period = goal_info[1].text[:1]
        time = goal_info[2].text
        team = goal_info[3].text
        score = goal_info[4].text
        situation = goal_info[5].text
        scorer = goal_info[6].text
        assists = goal_info[7].text
        gf_onice_numbers = goal_info[8].text
        ga_onice_numbers = goal_info[9].text

        # Format teams
        if team == away_team_abrv:
            gf_team = away_team
            ga_team = home_team
            gf_team_abrv = away_team_abrv
            ga_team_abrv = home_team_abrv
        elif team == home_team_abrv:
            gf_team = home_team
            ga_team = away_team
            gf_team_abrv = home_team_abrv
            ga_team_abrv = away_team_abrv
        else:
            gf_team = ''
            ga_team = ''

##        print("Away Team: " + away_team_abrv)
##        print("Home Team: " + home_team_abrv)
##        print("Goal by: " + team)
##        print("GF Team: " + gf_team_abrv)
##        print("GA Team: " + ga_team_abrv)
##        print(" ")
##        print(name_dict)
##        print(" ")
        
        # Format assists (split primary and secondary)
        if "-" in assists:
            assist1 = ''
            assist2 = ''
        elif "," in assists:
            assist1 = assists.split(", ")[0]
            assist2 = assists.split(", ")[1]
        else:
            assist1 = assists
            assist2 = ''

        # Strip (#) from goals
        if "(" in scorer:
            scorer = scorer[:scorer.index("(")-1]

        # Strip /# from assists
        if "/" in assist1:
            assist1 = assist1[:assist1.index("/")]
        if "/" in assist2:
            assist2 = assist2[:assist2.index("/")]

        # Format strength (#v#)
        for_strength = gf_onice_numbers.count(',')
        against_strength = ga_onice_numbers.count(',')
        strength = str(for_strength) + 'v' + str(against_strength)

        # Format on-ice players
        gf_onice = numbers_to_names(name_dict, gf_onice_numbers, gf_team_abrv)
        ga_onice = numbers_to_names(name_dict, ga_onice_numbers, ga_team_abrv)

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
            assist2,'',
            strength,
            gf_onice,
            ga_onice,
            situation,
            notes
        ])

        # Add to total time in beyond 60 minutes
        if period == 'O':
            extra_minutes = int(time[:time.index(":")])
            extra_seconds = float(time[time.index(":")+1:])/60

            total_time = float(total_time) + float(extra_minutes) + extra_seconds


    schedule_array[gameIndex][13] = total_time

    # Penalty table
    # -------------
    penalty_table = game_tables[14]
    penalties = penalty_table.find_all('tr')[1:]

# EXPORT ARRAYS TO CSV FILES
helpers.export_array_to_csv(schedule_array, '{0}-{1}-schedule.csv'.format(league, season))
helpers.export_array_to_csv(goal_array, '{0}-{1}-goals.csv'.format(league, season))
helpers.export_array_to_csv(boxscore_array, '{0}-{1}-playerbox.csv'.format(league, season))
helpers.export_array_to_csv(player_array, '{0}-{1}-players.csv'.format(league, season))

print("Complete")
