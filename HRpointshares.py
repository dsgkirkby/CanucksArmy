import requests
import csv
from modules import helpers
from unidecode import unidecode
from bs4 import BeautifulSoup

###################################################
#                                                 #
# HRpointshares.py                                #
#   This scraper will gather seasonal point share #
#   information from Hockey Reference             #
#                                                 #
###################################################

# Large scale arrays to be used in this program
roster_array = []
stats_array = []
corsi_array = []
teams_array = []

roster_array.append(['PlayerSeasonCode','PlayerCode','EP PlayerSeasonCode','EP PlayerCode','Player','Season','Team','Pos','Ht','Wt','DoB','Note'])
stats_array.append(['PlayerSeasonCode','PlayerCode','Player','Season','Team','GP','G','A','P','+/-','PIM','EVG','EVA','EVP','SOG','Sh%','TOI','ATOI','OPS','DPS','PS','BLK','HIT'])
corsi_array.append(['PlayerSeasonCode','PlayerCode','Player','Season','Team','GP','CF','CA','CF%','CF%rel','FF','FA','FF%','FF%rel','TOI60','TOI(EV)','TK','GV','E+/-','iCF','Thru%'])

season_baseurl = "https://www.hockey-reference.com/leagues/NHL_{0}.html"
team_baseurl = "https://www.hockey-reference.com/teams/{0}.html"

firstSeason = 2019
lastSeason = 2019

# Create code to pull team names from individual season pages
# -----------------------------------------------------------

for seasonIndex in range(firstSeason, lastSeason + 1):
    try:
        print("Compiling teams from ", seasonIndex, "...")
        url = season_baseurl.format(seasonIndex)
        season_request = requests.get(url,
                                    data=None,
                                    headers={
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                        }
                                    )
        season_page = BeautifulSoup(season_request.text, 'html.parser')
        season_tables = season_page.find_all('table')

        if seasonIndex < 1975:
            num_tables = 1
        elif seasonIndex > 1974:
            num_tables = 2
        for tableIndex in range(0, num_tables):
            tableRows = season_tables[tableIndex].find_all('tr')

            for rowIndex in range(2, len(tableRows)):
                if "Division" not in tableRows[rowIndex].text:
                    team_link = tableRows[rowIndex].a.get('href')
                    team_season_code = team_link[7:team_link.index('.')]

                    teams_array.append(team_season_code)
    except:
        None

# Cycle through each team page
# -----------------------------------------------------------

print("Gathering team information...")
for teamIndex in range(0, len(teams_array)):
    team_season_code = teams_array[teamIndex]
    team_abrv = team_season_code.split('/')[0]
    season = team_season_code.split('/')[1]
    
    print(team_season_code, round((float(teamIndex)/float(len(teams_array)))*100,2), "%")
    url = team_baseurl.format(team_season_code)
    team_request = requests.get(url,
                                data=None,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
                                    }
                                )
    team_page = BeautifulSoup(team_request.text, 'html.parser')
    team_tables = team_page.find_all('table')
    roster_table = team_tables[2]
    stats_table = team_tables[3]
    ##corsi_table = team_tables[7]

    # TEAM ROSTER
    # ======================================
    table_rows = roster_table.find_all('tr')
    for rowIndex in range(1, len(table_rows)):
        player = table_rows[rowIndex].find_all('td')
        #print(player)

        playercode = player[0].get('data-append-csv')
        playerseasoncode = playercode + '_' + str(season)
        name = player[0].text
        pos = player[2].text
        height = player[4].text
        weight = player[5].text
        dob = player[8].text

        if '(' in name:
            note = "Captain"
            name = name[:name.index('(')-1]
        else:
            note = ""

        year = dob[len(dob)-2:len(dob)]
        first_name = name[:name.index(' ')].lower()
        last_name = name[name.index(' '):].replace(' ','').lower()
        ep_playercode = last_name + '.' + first_name + '-' + str(year)
        ep_playerseasoncode = ep_playercode + '_NHL' + str(season)

        roster_array.append([
            playerseasoncode,
            playercode,
            ep_playerseasoncode,
            ep_playercode,
            name,
            season,
            team_abrv,
            pos,
            height,
            weight,
            dob,
            note
        ])

    # TEAM STATISTICS
    # ======================================
    table_rows = stats_table.find_all('tr')

    # to search all table rows, use len(table_rows)
    for rowIndex in range(2, len(table_rows)-1):
        player = table_rows[rowIndex].find_all('td')

        playercode = player[0].get('data-append-csv')
        playerseasoncode = playercode + '_' + str(season)
        name = player[0].text
        gp = player[3].text
        goals = player[4].text
        assists = player[5].text
        points = player[6].text
        plus_minus = player[7].text
        pims = player[8].text
        evgoals = player[9].text
        evassists = player[13].text
        try:
            evpoints = int(evgoals) + int(evassists)
        except:
            evpoints = 0
        shots = player[16].text
        sh_pct = player[17].text
        toi = player[18].text
        atoi = player[19].text
        ops = player[20].text
        dps = player[21].text
        ps = player[22].text
        blks = player[23].text
        hits = player[24].text

        stats_array.append([
            playerseasoncode,
            playercode,
            name,
            season,
            team_abrv,
            gp,
            goals,
            assists,
            points,
            plus_minus,
            pims,
            evgoals,
            evassists,
            evpoints,
            shots,
            sh_pct,
            toi,
            atoi,
            ops,
            dps,
            ps,
            blks,
            hits
        ])
        
        #print(playerseasoncode, playercode, name, team_abrv, season, gp, goals, assists, points)

    ### TEAM ADVANCED STATISTICS (CORSI)
    ##table_rows = corsi_table.find_all('tr')

    ### to search all table rows, use len(table_rows)
    ##for rowIndex in range(2, len(table_rows)-1):
    ##    player = table_rows[rowIndex].find_all('td')
    ##
    ##    playercode = player[0].get('data-append-csv')
    ##    playerseasoncode = playercode + '.' + str(season)
    ##    name = player[0].text
    ##    gp = player[3].text
    ##    cf = player[4].text
    ##    ca = player[5].text
    ##    cf_pct = player[6].text
    ##    cf_rel = player[7].text
    ##    ff = player[8].text
    ##    fa = player[9].text
    ##    ff_pct = player[10].text
    ##    ff_rel = player[11].text
    ##    toi60 = player[17].text
    ##    toiEV = player[18].text
    ##    tk = player[19].text
    ##    gv = player[20].text
    ##    e_pm = player[21].text
    ##    icf = player[22].text
    ##    thru_pct = player[23].text
    ##
    ##    print(playerseasoncode, name, gp, cf_pct)

print("Complete")
# EXPORT ARRAYS TO CSV FILES
helpers.export_array_to_csv(roster_array, 'hockeyreference-rosters-{0}-{1}.csv'.format(firstSeason, lastSeason))
helpers.export_array_to_csv(stats_array, 'hockeyreference-stats-{0}-{1}.csv'.format(firstSeason, lastSeason))
#helpers.export_array_to_csv(corsi_array, 'hockeyreference-corsi-{0}-{1}.csv'.format(firstSeason, lastSeason))


