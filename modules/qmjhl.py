import requests
import re
import time
from modules import chl_gamesheets
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

    return chl_gamesheets.scrape_gamesheets(game_ids, 'http://theqmjhl.ca/reports/games/{0}/text', 'Status Final SO')
