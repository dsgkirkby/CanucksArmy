import argparse

from modules import helpers, hockeytech_api


allowed_leagues = ['ohl', 'qmjhl', 'whl', 'ushl', 'bchl', 'sijhl', 'nojhl', 'ahl']


def main():
    arg_parser = argparse.ArgumentParser(
        description="Get all goals from a chosen chl league season.\n"
                    "Allowed Leagues: {0}".format(", ".join(allowed_leagues)),
        formatter_class=argparse.RawTextHelpFormatter
    )
    arg_parser.add_argument('leagues', type=helpers.comma_delimited_list, help="CHL leagues to scrape")
    arg_parser.add_argument('start_season', type=int, help="Starting season (i.e. 2018 for 2017-18)")
    arg_parser.add_argument('--range', type=int, help="Ending season", required=False)

    args = arg_parser.parse_args()

    start_season = args.start_season
    end_season = args.range if args.range is not None else args.start_season

    goals_results = []
    penalties_results = []
    games_results = []
    players_results = []

    for raw_league in args.leagues:

        league = raw_league.lower()

        if league not in allowed_leagues:
            print('Invalid League: {0}'.format(league))
            return

        #if league == 'ahl':
        #    print('AHL support requires further work')
        #    return

        seasons = helpers.get_json('http://cluster.leaguestat.com/feed/?feed=modulekit&view=seasons&key={0}&fmt=json&client_code={1}&lang=en&league_code=&fmt=json'.format(hockeytech_api.get_api_key(league), hockeytech_api.get_league_code(league)))['SiteKit']['Seasons']

        selected_seasons = filter(
            lambda season:
                start_season <= int(season['end_date'][0:4]) <= end_season and
                season['career'] == '1' and
                'pre season' not in season['season_name'].lower() and
                'pre-season' not in season['season_name'].lower() and
                'tie break' not in season['season_name'].lower() and
                'tie-break' not in season['season_name'].lower() and
                'playoffs' not in season['season_name'].lower(),
            seasons
        )

        for season in reversed(list(selected_seasons)):
            print('Collecting ' + league.upper() + ' ' + season['season_name'] + '...', end='', flush=True)
            hockeytech_api.get_season_stats(
                season, league, goals_results, penalties_results, games_results, players_results
            )
            print('done.')

    helpers.export_array_to_csv(
        goals_results,
        '{0}-{1}-{2}-goals.csv'.format('-'.join(args.leagues), start_season, end_season)
    )
    helpers.export_array_to_csv(
        penalties_results,
        '{0}-{1}-{2}-penalties.csv'.format('-'.join(args.leagues), start_season, end_season)
    )
    helpers.export_array_to_csv(
        games_results,
        '{0}-{1}-{2}-games.csv'.format('-'.join(args.leagues), start_season, end_season)
    )
    helpers.export_array_to_csv(
        players_results,
        '{0}-{1}-{2}-players.csv'.format('-'.join(args.leagues), start_season, end_season)
    )
    print("Success!")

if __name__ == '__main__':
    main()
