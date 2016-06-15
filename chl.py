import argparse

from modules import helpers, qmjhl, ohl


def main():
    arg_parser = argparse.ArgumentParser(description="Get all goals from a chosen chl league season")
    arg_parser.add_argument('season', type=int, help="Season ID")
    arg_parser.add_argument('league', type=str, help="League to scrape (qmjhl or ohl)")

    args = arg_parser.parse_args()

    league = args.league.lower()

    if league == 'qmjhl':
        results_array = qmjhl.get_qmjhl_stats(args.season)
    elif league == 'ohl':
        results_array = ohl.get_ohl_stats(args.season)
    else:
        print('Invalid League')
        return

    helpers.export_array_to_csv(results_array, '{0}-{1}.csv'.format(args.league, args.season))

    print("Success!")


main()
