import requests
import json
from modules import chl_gamesheets

EXTRA_COLUMNS = 0


def get_ohl_stats(season):
    season = str(season)
    ohl_url = 'http://cluster.leaguestat.com/feed/?feed=modulekit&view=schedule&key=c680916776709578&fmt=json&client_code=ohl&lang=en&season_id={0}&team_id=undefined&league_code=&fmt=json'.format(season)

    request = requests.get(ohl_url)
    decoder = json.JSONDecoder()
    result = decoder.decode(request.text)
    game_ids = list(map(lambda game: game['game_id'], result['SiteKit']['Schedule']))

    return chl_gamesheets.scrape_gamesheets(game_ids, 'http://media.ontariohockeyleague.com/stats/official-game-report.php?game_id={0}')
