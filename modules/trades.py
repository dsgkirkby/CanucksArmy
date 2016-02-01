import requests
import time
from bs4 import BeautifulSoup


def get_nhl_trades(season_end, results_array=None):

    if results_array is None or len(results_array) == 0:
        results_array.append(['Date', 'Team1', 'Team1 Acquired', 'Team2', 'Team2 Acquired'])

    season_start = str(int(season_end) - 1)
    season_end = str(int(season_end) % 100)

    page_index = 1

    while True:
        url = "http://nhltradetracker.com/user/trade_list_by_season/{0}-{1}/{2}".format(season_start, season_end, page_index)

        page_request = requests.get(url)
        page = BeautifulSoup(page_request.text, "html.parser")

        def empty_list_error(tag):
            return tag.text.strip() == 'No trades exist for this selection'

        if page.find(empty_list_error) is not None:
            break

        page_index += 1

        def container_div(tag):
            return tag.name == 'div' and tag.has_attr('id') and tag.attrs['id'] == 'container'

        container_div = page.find(container_div)

        trades = container_div.find_all('table', recursive=False)

        for trade in trades:
            rows = trade.find_all('tr', recursive=False)

            titles = rows[0].find_all('td')

            def get_team_name(tag):
                return tag.text.strip()[:-8]

            team_1 = get_team_name(titles[0])
            team_2 = get_team_name(titles[2])

            data = rows[1].find_all('td', recursive=False)

            def get_trade_assets(tag):
                return tag.text.strip().replace('\n', ', ').replace('  ', ' ')

            date = time.strptime(data[1].text, '%B %d, %Y')
            date = time.strftime('%Y-%m-%d', date)
            team_1_acquired = get_trade_assets(data[0])
            team_2_acquired = get_trade_assets(data[2])

            results_array.append([date, team_1, team_1_acquired, team_2, team_2_acquired])

    return results_array
