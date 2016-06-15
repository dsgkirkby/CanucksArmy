import requests
import re
from bs4 import BeautifulSoup


def scrape_gamesheets(game_ids, url, shootOutText):
    goals = [['scorer', 'assist1', 'assist2', 'situation']]

    for game_id in game_ids:
        game_request = requests.get(url.format(game_id))
        game_report_page = BeautifulSoup(game_request.text, 'html.parser')

        game_report = game_report_page.body.text

        team_score_regex = re.compile('[0-9]+\s[0-9]+\s[0-9]+\s-\s([0-9]+)')
        team_scores = team_score_regex.findall(game_report)
        total_score = 0
        for team_score in team_scores:
            total_score += int(team_score[0])

        if shootOutText in game_report:
            total_score -= 1

        scorer_regex = re.compile('\s+([^,\)]+)\s[0-9]+\s+(?:\(([^,\)]+)(?:,\s([^,\)]+|))?\),\s+)?[0-9]{1,2}:[0-9]{2}(?:\s\(([A-Z]+)\))?', re.S)
        goals_found = scorer_regex.findall(game_report)

        total_goals_found = len(goals_found)

        if total_goals_found != total_score:
            print('Error in game {0}: expected {1} goals, but scraped {2}'.format(game_id, total_score, len(goals_found)))

        for goal in goals_found:
            goals.append([goal[0], goal[1], goal[2], goal[3]])

        print('{0}/{1}'.format(str(game_ids.index(game_id) + 1), str(len(game_ids))))

    return goals