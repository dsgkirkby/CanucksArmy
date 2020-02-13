import requests
import csv
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup

#############################################################
#                                                           #
# Sweden.py                                                 #
#   This scraper will gather information from all Swedish   #
#   league games, inlcuding SHL, Allsvenskan, and Superelit #                        #
#                                                           #
#############################################################

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
schedule_array = []
goal_array = []
player_array = []
penalty_array = []
goalie_array = []
away_roster_array = []
home_roster_array = []
sweleagues = []

# Constants
#SHL = 8121, Allsvenskan = 8122, SuperelitNorra = 8124, SuperelitSodra = 8125
season = 2019
season_type = "Season"
league = "SuperelitNorra"

if league is "SHL":
    #season_id = 8121
    season_id = 9171
    event_start = 5
    roster_start = 7
elif league is "Allsvenskan":
    #season_id = 8122
    season_id = 9168
    event_start = 11
    roster_start = 13
elif league is "SuperelitNorra":
    season_id = 9169
    event_start = 5
    roster_start = 7
elif league is "SuperelitSodra":
    season_id = 9170
    event_start = 5
    roster_start = 7
elif league is "SuperelitTop10":
    season_id = 9517
    event_start = 5
    roster_start = 7
elif league is "SuperelitForts":
    season_id = 9516
    event_start = 5
    roster_start = 7

print("Gathering...")

# Initialize array values
game_array.append(['Game ID'])
schedule_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                       'Visiting Team', 'Home Team', 'Visitor GF', 'Home GF',
                       'Winning Team', 'Losing Team', 'Visitor Roster', 'Home Roster'])

player_array.append(['Player', 'Position', 'Season', 'Season Type', 'League', 'Team',
                     'Age', 'Birthdate', 'Birthplace', 'Height', 'Weight', 'Hand', 'GP', 'Shots'])

goal_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                   'GF Team', 'GA Team', 'Period', 'Time',
                   'Scorer', 'Assist1', 'Assist2',
                   'Score State', 'Strength', 'Plus', 'Minus', 'Situation'])

teams_baseurl = "http://stats.swehockey.se/Teams/Info/TeamRoster/{0}"
schedule_baseurl = "http://stats.swehockey.se/ScheduleAndResults/Schedule/{0}"
rosters_baseurl = "http://stats.swehockey.se/Teams/Info/TeamRoster/{0}"

# ----------------- #
#       TEAMS       #
# ----------------- #
print("...teams")
teams_dict = {}

# GET THE TEAM ROSTER PAGE
#   For creating a dictionary of team abbreviations
teams_url = teams_baseurl.format(season_id)
teams_request = requests.get(teams_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )

teams_page = BeautifulSoup(teams_request.text, 'html.parser')
teams_tables = teams_page.find('table')
teams_row = teams_tables.find('tr').find('td').find('div')
teams = teams_tables.find_all('a')

for teams_index in range(0, len(teams)):
    team_abrv = teams[teams_index].get('href')
    if team_abrv != '#top':
        if team_abrv is not None:
            team_abrv = team_abrv[1:].replace('\r','')
            team_name = teams[teams_index].text.replace('\r','')
            teams_dict[team_abrv] = team_name
teams_dict["SAIK"] = "Skellefteå AIK"

# ----------------- #
#     SCHEDULE      #
# ----------------- #
print("...schedule")
# GET THE SCHEDULE
schedule_url = schedule_baseurl.format(season_id)
schedule_request = requests.get(schedule_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )

schedule_page = BeautifulSoup(schedule_request.text, 'html.parser')
schedule = schedule_page.find('table')
games = schedule.find_all('tr')

for gameIndex in range(2,len(games)):
    game_info = games[gameIndex].find_all('td')

    # Filters out unplayed games
    if len(game_info) > 5:
        link = games[gameIndex].a.get('href')
        link_split = link.split("/")
        game_id = link_split[3][:6]

        game_array.append([game_id])

        if "-" in game_info[0].text:
            last_date = game_info[0].text
            date = last_date
        else:
            date = last_date

        away_team = game_info[2].text.replace('\n',' ').replace('       ','')
        teams_split = away_team.split("-")
        away_team = teams_split[0].replace('  ','').replace('\r','')
        away_team = away_team[:len(away_team)-1]
        home_team = teams_split[1].replace('  ','').replace('\r','')
        home_team = home_team[1:]
        away_goals = game_info[3].text
        away_goals = int(away_goals[:away_goals.index("-")-1])
        home_goals = game_info[3].text
        home_goals = int(home_goals[home_goals.index("-")+1:])
        if away_goals > home_goals:
            winning_team = away_team
            losing_team = home_team
        elif home_goals > away_goals:
            winning_team = home_team
            losing_team = away_team
        
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

# ----------------- #
#      ROSTERS      #
# ----------------- #
print("...rosters")
player_dict = {}
player_shots_dict = {}

rosters_baseurl = "http://stats.swehockey.se/Teams/Info/TeamRoster/{0}"
stats_baseurl = "http://stats.swehockey.se/Teams/Info/PlayersByTeam/{0}"

# GET THE STATS PAGES
stats_url = stats_baseurl.format(season_id)
stats_request = requests.get(stats_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )

stats_page = BeautifulSoup(stats_request.text, 'html.parser')
all_stats = stats_page.find_all('table')

stats = all_stats[0].find_all('tr')
for playerIndex in range(1, len(stats)):
    player_info = stats[playerIndex].find_all('td')

    # Filters out unplayed games
    if len(player_info) > 5:
        if "," in player_info[2].text:
            name = player_info[2].text.replace(' ','')
            player_gp = player_info[4].text
            try:
                player_shots = player_info[15].text
            except:
                player_shots = ''

            # Find team
            team = player_info[0].parent.parent.th.text
            
            name = name_swap(name)
            player_with_team = str(name + "-" + team)
            # add name to dictionary to match with name in rosters
            player_dict[player_with_team] = player_gp
            player_shots_dict[player_with_team] = player_shots
    

# GET THE ROSTERS
rosters_url = rosters_baseurl.format(season_id)
rosters_request = requests.get(rosters_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )

rosters_page = BeautifulSoup(rosters_request.text, 'html.parser')
rosters = rosters_page.find_all('table')

roster = rosters[0].find_all('tr')
for playerIndex in range(1, len(roster)):
    player_info = roster[playerIndex].find_all('td')

    # Filters out unplayed games
    if len(player_info) > 5:
        if "," in player_info[1].text:        
            number = player_info[0].text
            name = player_info[1].text.replace(' ','')
            birthdate = player_info[2].text
            position = player_info[3].text
            shot = player_info[4].text
            height = player_info[5].text
            weight = player_info[6].text
            nationality = player_info[7].text

            # Format name
            name = name_swap(name)

            # Find team
            team = player_info[0].parent.parent.th.text

            # Format player_with_team and find GP from dictionary
            player_with_team = str(name + "-" + team)
            try:
                games = player_dict[player_with_team]
                player_shots = player_shots_dict[player_with_team]
            except KeyError:
                games = ''
                player_shots = ''
            
            player_array.append([
                name,
                position,
                season,
                season_type,
                league,
                team,
                '',
                birthdate,
                nationality,
                height,
                weight,
                shot,
                games,
                player_shots
        ])

# ----------------- # *********************************************************************************************************************************
#       GAMES       # 
# ----------------- # *********************************************************************************************************************************
print("...games (", len(game_array),")")
events_baseurl = "http://stats.swehockey.se/Game/Events/{0}"
lineups_baseurl = "http://stats.swehockey.se/Game/LineUps/{0}"

lineups_dict = {}

# For loop through all games in game_array - len(game_array)
for gameIndex in range(1, len(game_array)):

    game_id = str(*game_array[gameIndex])
    lineups_dict.clear()
    # Pull date, teams from schedule array
    date = schedule_array[gameIndex][4]
    away_team = schedule_array[gameIndex][5]
    home_team = schedule_array[gameIndex][6]

    #------------------------------------------
    #   Lineup
    #------------------------------------------
    # Get dictionary of players

    url = lineups_baseurl.format(*game_array[gameIndex])

    # REQUEST THE INDIVIDUAL GAME'S BOXSCORE
    lineups_request = requests.get(url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )

    lineups_page = BeautifulSoup(lineups_request.text, 'html.parser')

    lineups_tables = lineups_page.find_all('table')

    for tableIndex in range(10, 15):
        try:
            if 'Line Up' in lineups_tables[tableIndex].tr.th.text:
                roster_start = tableIndex + 3
                print(lineups_tables[tableIndex].tr.th.text)
                break
        except:
            None

    lineups_rows = lineups_tables[roster_start].find_all('tr')

    for rowsIndex in range(0, len(lineups_rows)):
        try:
            if "(" in lineups_rows[rowsIndex].th.h3.text \
               or "(White)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Red)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Blue)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Green)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Yellow)" in lineups_rows[rowsIndex].th.h3.text:
                away_row = rowsIndex
                break
        except:
            None

    for rowsIndex in range(away_row + 1, len(lineups_rows)):
        try:
            if "(" in lineups_rows[rowsIndex].th.h3.text \
               or "(White)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Reed)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Blue)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Green)" in lineups_rows[rowsIndex].th.h3.text \
               or "(Yellow)" in lineups_rows[rowsIndex].th.h3.text:
                home_row = rowsIndex
                break
        except:
            None
##        if "()" in lineups_rows[rowsIndex].text:
##            home_row = rowsIndex

    print(gameIndex, game_id)
    #print(away_row, lineups_rows[away_row].text)
    #print(home_row, lineups_rows[home_row].text)

    for rowsIndex in range(1, len(lineups_rows)):
        players_in_row = lineups_rows[rowsIndex].find_all('div')

        #if len(players_in_row) > 0:
        for lineIndex in range(0, len(players_in_row)):
            player = players_in_row[lineIndex].text.replace('\n','').replace('\r','').replace(' ','')
    
            if "(" in player:
                player = player[:player.index("(")-1]

            player_split = player.split(".")
            number = player_split[0]
            player = name_swap(player_split[1])

            # Find team
            if rowsIndex < home_row:
                team = lineups_rows[away_row].text
                team = team[:team.index("(")-1]
                away_roster_array.append(player)
            elif rowsIndex > home_row:
                team = lineups_rows[home_row].text
                team = team[:team.index("(")-1]
                home_roster_array.append(player)

            #print(team, player)

            player_id = str(team + number)

            # Assign player name to player_id in lineup dictionary
            lineups_dict[player_id] = player
            
    away_roster = ','.join(''.join(elems) for elems in away_roster_array)
    home_roster = ','.join(''.join(elems) for elems in home_roster_array)
    away_roster_array.clear()
    home_roster_array.clear()
    schedule_array[gameIndex][11] = away_roster
    schedule_array[gameIndex][12] = home_roster

    #------------------------------------------
    #   Events
    #------------------------------------------
    
    url = events_baseurl.format(*game_array[gameIndex])

    # REQUEST THE INDIVIDUAL GAME'S BOXSCORE
    game_request = requests.get(url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )

    game_page = BeautifulSoup(game_request.text, 'html.parser')

    game_tables = game_page.find_all('table')

    # Events table
    # ------------
    #SHL = 5, Allsvenskan = 5
    events_table = game_tables[event_start]

    events = events_table.find_all('tr')
    for eventIndex in range(1, len(events)):
        event = events[eventIndex].find_all('td')

        if len(event) > 4:
            goal = event[3].find_all('span')

            if len(goal) > 0:

                if "%" not in event[3].text:
                
                    # Format scorer and assists
                    scorer = event[3].text.replace('\n',' ').replace('\r','').replace('     ','')
                    #print(scorer)
                    scorer = scorer[:scorer.index("(")-1]
                    scorer = scorer[scorer.index(".")+1:]
                    scorer = name_swap(scorer)
                    if len(goal) > 1:
                        assist1 = goal[1].text.replace('\n',' ').replace('     ','')
                        assist1 = assist1[assist1.index(".")+1:]
                        assist1 = name_swap(assist1).replace('\r','')
                        if len(goal) > 2:
                            assist2 = goal[2].text.replace('\n',' ').replace('     ','').replace('    ','')
                            assist2 = assist2[assist2.index(".")+1:]
                            assist2 = name_swap(assist2).replace('\r','')
                        else:
                            assist2 = ''
                    else:
                        assist1 = ''
                        assist2 = ''
                    
                    score = event[1].text

                    # Format teams
                    gf_team = event[2].text
                    gf_team = teams_dict[gf_team]
                    if gf_team == away_team:
                        ga_team = home_team
                    elif gf_team == home_team:
                        ga_team = away_team

                    # Format periods and time
                    time = event[0].text
                    if ":" in time:
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
                        time = str(minutes) + ":" + str(seconds)
                    else:
                        time = ''
                        period = "SO"

                    # Format on-ice plus and minus player numbers
                    on_ice = event[4].text.replace('\n',' ').split("Neg")
                    plus = on_ice[0].replace('     Pos. Part.: ','').replace(' ','').replace('\r','')
                    minus = on_ice[1].replace('. Part.: ','').replace(' ','').replace('\r','')

                    gf_onice = numbers_to_names(lineups_dict, plus, gf_team)
                    ga_onice = numbers_to_names(lineups_dict, minus, ga_team)

                    #print(gf_onice, ga_onice)

##                    plus_split = plus.split(",")
##                    for plus_index in range(1, len(plus_split)):
##                        try:
##                            plus_list[plus_index] = lineups_dict[player_id]
##                        except KeyError:
##                            plus_list[plus_index] = plus_split[plus_index]

                    # Format strength (#v#)
                    for_strength = plus.count(',')
                    against_strength = minus.count(',')
                    strength = str(for_strength) + "v" + str(against_strength)

                    # Format strength situation
                    situation = score[score.index("(")+1:]
                    situation = situation[:situation.index(")")]

                    #print(game_id," ",date," ",scorer)

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
                        '',
                        strength,
                        gf_onice,
                        ga_onice,
                        situation,
                        away_team,
                        home_team
                    ])
        
helpers.export_array_to_csv(goal_array, "{0}-{1}-goals.csv".format(league, season))
helpers.export_array_to_csv(schedule_array, "{0}-{1}-schedule.csv".format(league, season))
helpers.export_array_to_csv(player_array, "{0}-{1}-players.csv".format(league, season))
print("Complete")
