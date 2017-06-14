import argparse

from modules import helpers, chl


def main():
    arg_parser = argparse.ArgumentParser(
        description="Get all goals from a chosen chl league season.\n\n"
                    "Earliest possible seasons:\n"
                    "OHL: 1997-98\n"
                    "WHL: 1996-97\n"
                    "QMJHL: 1969-70\n"
                    "USHL: 2002-03\n",
        formatter_class=argparse.RawTextHelpFormatter
    )
    arg_parser.add_argument('leagues', type=helpers.comma_delimited_list, help="CHL leagues to scrape")
    arg_parser.add_argument('start_season', type=int, help="Starting season (i.e. 2018 for 2017-18)")
    arg_parser.add_argument('--range', type=int, help="Ending season", required=False)

    args = arg_parser.parse_args()

    start_season = args.start_season
    end_season = args.range if args.range is not None else args.start_season

    results_array = []

    for raw_league in args.leagues:

        league = raw_league.lower()

        if league not in ['ohl', 'qmjhl', 'whl', 'ushl']:
            print('Invalid League: {0}'.format(league))
            return

        seasons = helpers.get_json('http://cluster.leaguestat.com/feed/?feed=modulekit&view=seasons&key={0}&fmt=json&client_code={1}&lang=en&league_code=&fmt=json'.format(chl.api_key, chl.league_codes[league]))['SiteKit']['Seasons']

        selected_seasons = filter(
            lambda season: start_season <= int(season['end_date'][0:4]) <= end_season and season['career'] == '1',
            seasons
        )

        for season in reversed(list(selected_seasons)):
            print('Collecting ' + league.upper() + ' ' + season['season_name'] + '...', end='', flush=True)
            chl.get_season_stats(season, league, results_array)
            print(' done.')

    helpers.export_array_to_csv(results_array, '{0}-{1}-{2}.csv'.format('-'.join(args.leagues), start_season, end_season))
    print("Success! {0} results found.".format(len(results_array)))

if __name__ == '__main__':
    main()
