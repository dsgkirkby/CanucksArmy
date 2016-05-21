import argparse

from modules import helpers, draft


def main():
    arg_parser = argparse.ArgumentParser(description="Get draft picks from the specified NHL draft")
    arg_parser.add_argument('start_season', type=int, help="Earliest draft to scrape")
    arg_parser.add_argument('--range', type=int, help="Latest draft to scrape", required=False)
    arg_parser.add_argument('--extra', action='store_true', help="Whether to show extra information about each player (significantly slower)")

    args = arg_parser.parse_args()

    start_season = args.start_season
    end_season = args.range if args.range is not None else args.start_season

    results_array = []

    for season in range(start_season, end_season + 1):
        print('Scraping NHL Draft {0}'.format(season))
        results_array = draft.get_draft_picks(season, results_array, args.extra)

    helpers.export_array_to_csv(results_array, 'nhl_draft_{0}-{1}.csv'.format(start_season, end_season))

    print("Success!")


main()
