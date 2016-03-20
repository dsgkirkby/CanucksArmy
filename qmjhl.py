import argparse

from modules import helpers, qmjhl


def main():
    arg_parser = argparse.ArgumentParser(description="Get all goals from a chosen qmjhl season")
    arg_parser.add_argument('season', type=int, help="Season ID")

    args = arg_parser.parse_args()

    results_array = qmjhl.get_qmjhl_stats(args.season)

    helpers.export_array_to_csv(results_array, 'qmjhl-{0}.csv'.format(args.season))

    print("Success!")


main()
