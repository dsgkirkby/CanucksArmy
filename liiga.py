import requests
import csv
import datetime
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup

#############################################################
#                                                           #
# Liiga.py                                                  #
#   This scraper will gather information from all Finnish   #
#   Liiga games.                                            #
#                                                           #
#############################################################

def name_swap(fullname):

    name_split = fullname.split(",")
    lastname = name_split[0]
    firstname = name_split[1]
    name = firstname + " " + lastname
    return name

# Large scale arrays to be used in this program
game_array = []
schedule_array = []
goal_array = []
player_array = []
penalty_array = []
goalie_array = []
plus_players_array = []
minus_players_array = []
away_roster_array = []
home_roster_array = []

# Constants
season_id = "2018-2019"
season = 2019
season_type = "Season"
league = "Liiga"

# Season
game_baseurl = "http://liiga.fi/ottelut/{0}/runkosarja/{1}/tilastot/"
schedule_baseurl = "http://liiga.fi/ottelut/{0}/runkosarja/"
# Playoffs
#game_baseurl = "http://liiga.fi/ottelut/{0}/playoffs/{1}/tilastot/"
#schedule_baseurl = "http://liiga.fi/ottelut/{0}/playoffs/"

print("Gathering...")

# Initialize array values
game_array.append(['Game ID'])
schedule_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                       'Visiting Team', 'Home Team', 'Visitor GF', 'Home GF',
                       'Winning Team', 'Losing Team', 'Away Roster', 'Home Roster'])

goal_array.append(['Season', 'Season Type', 'League', 'GameID', 'Date',
                   'GF Team', 'GA Team', 'Period', 'Time',
                   'Scorer', 'Assist1', 'Assist2',
                   'Score State', 'Strength', 'Plus', 'Minus', 'Situation'])

# ----------------- #
#     SCHEDULE      #
# ----------------- #

# GET THE SCHEDULE
print("...schedule")
#schedule_url = "http://liiga.fi/ottelut/2017-2018/runkosarja/"
schedule_url = schedule_baseurl.format(season_id)
schedule_request = requests.get(schedule_url,
                            data=None,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                }
                            )

schedule_page = BeautifulSoup(schedule_request.text, 'html.parser')
schedule = schedule_page.find_all('table')
print("Tables:", len(schedule))

for tableIndex in range(0, len(schedule)):
    games = schedule[tableIndex].find_all('tr')

    for gameIndex in range(1, len(games)):
        game_info = games[gameIndex].find_all('td')

        #print("Schedule is ", round(gameIndex / 450 * 100,0), "% complete")
        
        # Filter out unplayed games
        if len(game_info) > 2 and "-" not in game_info[7].text:
            print(game_info[7].text)
            if "-" not in game_info[7].text:
                print("True")
            else:
                print("False")
            #print(game_info)
            link = games[gameIndex].a.get('href')
            link_split = link.split("runkosarja/")
            game_id = int(link_split[1][:len(link_split[1])-1])
            #game_id = gameIndex

            # Format date
            date = games[gameIndex].get('data-time')
            #print(date)
            year = int(date[:4])
            month = int(date[4:6])
            day = int(date[6:])
            date = str(datetime.date(year, month, day))

            # Format teams
            teams = game_info[3].text.replace('\r','').replace('\n','')
            teams_split = teams.split("-")
            away_team = teams_split[0].replace(' ','')
            home_team = teams_split[1].replace(' ','')

            # Format score
            score = game_info[5].text
            score_split = score.split(' — ')
            away_goals = score_split[0]
            home_goals = score_split[1]

            if away_goals > home_goals:
                winning_team = away_team
                losing_team = home_team
            elif home_goals > away_goals:
                winning_team = home_team
                losing_team = away_team
                
            game_array.append(gameIndex)
            
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
            
            print(game_id, date, away_team, home_team, away_goals, home_goals)
print(game_array)

# ----------------- #
#       GAMES       #
# ----------------- #

print("...games")
# For loop through all games in game_array - len(game_array)
for gameIndex in range(1, len(game_array)):

    game_id = schedule_array[gameIndex][3]

    game_url = game_baseurl.format(season_id, game_id)
    game_request = requests.get(game_url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )

    print("Game ID:", game_id, "  Games are", round(gameIndex / len(game_array) * 100,0), "% complete")
    
    # Format date, teams from schedule array
    date = schedule_array[gameIndex][4]
    away_team = schedule_array[gameIndex][5]
    home_team = schedule_array[gameIndex][6]
    # Reset score counters to zero
    home_score = 0
    away_score = 0

    game_page = BeautifulSoup(game_request.text, 'html.parser')
    game_tables = game_page.find_all('table')
    goals = game_tables[0].find_all('tr')

    for goalIndex in range(0, len(goals)):
        
        goal_info = goals[goalIndex].find_all('td')

        # Format score
        score = goal_info[0].find_all('span')[0].text
        score_split = score.split(" – ")
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

        # Format time
        time = goal_info[0].find_all('span')[1].text
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
            time = str(minutes) + ":0" + str(seconds)
        else:
            time = str(minutes) + ":" + str(seconds)
        
        # Format scorers
        scoring_play = goal_info[1].find_all('a')
        scorer = goal_info[1].a.text
        if "(" in goal_info[1].text:
            assist1 = scoring_play[1].text
            if "," in goal_info[1].text[:goal_info[1].text.index(")")]:
                assist2 = scoring_play[2].text
            else:
                assist2 = ''
        else:
            assist1 = ''
            assist2 = ''

        # Special teams goals
        if "YV2" in goal_info[1].text:
            strength = "5v3"
            situation = "PP"
        elif "YV" in goal_info[1].text:
            strength = "5v4"
            situation = "PP"
        elif "AV2" in goal_info[1].text:
            strength = "3v5"
            situation = "PP"
        elif "AV" in goal_info[1].text:
            strength = "4v5"
            situation = "PP"
        else:
            situation = ""
        
        # on-ice players not reported
        if "+" not in goal_info[1].text:
            plus = ''
            minus = ''
        # on-ice players reported
        elif "+" in goal_info[1].text:
            # Format on-ice players
            plus_minus = goal_info[1].find_all('td')
            plus_players = plus_minus[0].find_all('a')
            minus_players = plus_minus[1].find_all('a')
            for playerIndex in range(0, len(plus_players)):
                plus_players_array.append(plus_players[playerIndex].text)
            for playerIndex in range(0, len(minus_players)):
                minus_players_array.append(minus_players[playerIndex].text)
            plus = ','.join(''.join(elems) for elems in plus_players_array)
            minus = ','.join(''.join(elems) for elems in minus_players_array)
            plus_players_array.clear()
            minus_players_array.clear()
            #print(plus_players)
            #print(minus_players)
            # Format strength (#v#)
            for_strength = plus.count(',')+1
            against_strength = minus.count(',')+1
            strength = str(for_strength) + "v" + str(against_strength)

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
            plus,minus,
            situation
        ])

    for tableIndex in range(1, len(game_tables)):
        try:
            if 'Nimi' in game_tables[tableIndex].a.text:
                away_roster = game_tables[tableIndex]
                away_players = away_roster.find_all('tr')
                for playerIndex in range(1, len(away_players)):
                    away_roster_array.append(name_swap(away_players[playerIndex].a.text.replace(' ','')))
                home_roster = game_tables[tableIndex + 2]
                home_players = home_roster.find_all('tr')
                for playerIndex in range(1, len(home_players)):
                    home_roster_array.append(name_swap(home_players[playerIndex].a.text.replace(' ','')))
                break
        except:
            None


    away_roster = ','.join(''.join(elems) for elems in away_roster_array)
    home_roster = ','.join(''.join(elems) for elems in home_roster_array)
    away_roster_array.clear()
    home_roster_array.clear()
    schedule_array[gameIndex][11] = away_roster
    schedule_array[gameIndex][12] = home_roster

# EXPORT ARRAYS TO CSV FILES
helpers.export_array_to_csv(schedule_array, '{0}-{1}-schedule.csv'.format(league, season))
helpers.export_array_to_csv(goal_array, '{0}-{1}-goals.csv'.format(league, season))
#helpers.export_array_to_csv(boxscore_array, '{0}-{1}-playerbox.csv'.format(league, season))
#helpers.export_array_to_csv(player_array, "AHL-players.csv")

print("Complete")



