import requests
import re
import time
from bs4 import BeautifulSoup

EXTRA_COLUMNS = 0


def get_qmjhl_stats(season):
    season = str(season)
    current_date = time.strftime('%Y-%m-%d')
    qmjhl_url = 'http://cluster.leaguestat.com/feed/index.php?feed=widgetkit2&view=schedule&key=f109cf290fcf50d4&client_code=lhjmq&date={0}&season_id={1}&team_id=&month=&year=0&type=scheduleseason&lang=en'.format(current_date, season)

    request = requests.get(qmjhl_url)
    soup = BeautifulSoup(request.text, 'html.parser')
    games_table = soup.find(class_='ls-statview-table')
    games = games_table.tbody.find_all('tr')

    game_ids = []

    for game in games:
        game_links = game.find(class_='ls-statview-links')
        game_report_link = game_links.find_all('a', recursive=False)[0].attrs['href']
        if game_report_link.find('game_id=') > 0:
            game_id = game_report_link[-4:]
            game_ids.append(game_id)

    goals = [['scorer', 'assist1', 'assist2', 'situation']]

    for game_id in game_ids:
        game_request = requests.get('http://theqmjhl.ca/reports/games/{0}/text'.format(game_id))
        game_report_page = BeautifulSoup(game_request.text, 'html.parser')

        game_report = game_report_page.find(class_='main-content').div.text

        team_score_regex = re.compile('[0-9]+\s[0-9]+\s[0-9]+\s-\s([0-9]+)')
        team_scores = team_score_regex.findall(game_report)
        total_score = 0
        for team_score in team_scores:
            total_score += int(team_score[0])

        if 'Status Final SO' in game_report:
            total_score -= 1

        scorer_regex = re.compile('\s+([^,\)]+)\s[0-9]+\s+(?:\(([^,\)]+)(?:,\s([^,\)]+|))?\),\s+)?[0-9]{1,2}:[0-9]{2}(?:\s\(([A-Z]+)\))?', re.S)
        goals_found = scorer_regex.findall(game_report)

        total_goals_found = len(goals_found)

        if total_goals_found != total_score:
            print('Error in game {0}: expected {1} goals, but scraped {2}'.format(game_id, total_score, goals_found))

        for goal in goals_found:
            goals.append([goal[0], goal[1], goal[2], goal[3]])

        print('{0}/{1}'.format(str(game_ids.index(game_id) + 1), str(len(game_ids))))

    return goals
