import argparse

from modules import helpers
from modules import alltime


def main():
    arg_parser = argparse.ArgumentParser(description="Get all-time games played, goals, assists, and points from any league")
    arg_parser.add_argument('league', help="League of which to get all-time stats")

    args = arg_parser.parse_args()

    results_array = alltime.get_all_time_stats(args.league)

    helpers.export_array_to_csv(results_array, '{0}_all_time_stats.csv'.format(args.league))

    print("Success!")


main()
