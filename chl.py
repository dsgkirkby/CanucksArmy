import argparse

from modules import helpers, chl


def main():
    arg_parser = argparse.ArgumentParser(description="Get all goals from a chosen chl league season")
    arg_parser.add_argument('season', type=int, help="Season ID")
    arg_parser.add_argument('league', type=str, help="League to scrape (qmjhl or ohl)")

    args = arg_parser.parse_args()

    league = args.league.lower()

    if league == 'ohl' or league == 'qmjhl' or league == 'whl':
        results_array = chl.get_season_stats(args.season, league)
    else:
        print('Invalid League')
        return

    helpers.export_array_to_csv(results_array, '{0}-{1}.csv'.format(args.league, args.season))

    print("Success!")

if __name__ == '__main__':
    main()
