import argparse

from modules import helpers
from modules import trades


def main():
    arg_parser = argparse.ArgumentParser(description="Get all trades for the NHL for the given seasons")
    arg_parser.add_argument('start_season', type=int, help="Earliest season for which to scrape data. Second year of the season (i.e. passing 2014 refers to the 2013-14 season)")
    arg_parser.add_argument('--range', type=int, help="Choose the latest season to parse to parse many seasons at once. Second year of the season (i.e. passing 2014 refers to the 2013-14 season)", required=False)

    args = arg_parser.parse_args()

    start_season = args.start_season
    end_season = args.range if args.range is not None else args.start_season

    results_array = []

    for season in reversed(range(start_season, end_season + 1)):
        trades.get_nhl_trades(season, results_array)

    helpers.export_array_to_csv(results_array, '{0}-{1}_nhl_trades.csv'.format(start_season, end_season))

    print("Success!")


main()
