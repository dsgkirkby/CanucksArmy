import argparse

from modules import helpers, stats, roster, teamroster, standings


def main():
    arg_parser = argparse.ArgumentParser(description="Get prospect data from any league on the planet over a range of seasons")
    arg_parser.add_argument('--roster', action='store_true', help="Output roster list for the given league(s) and season(s)")
    arg_parser.add_argument('--team_roster', action='store_true', help="Output roster list for the given team and season(s)")
    arg_parser.add_argument('--stats', action='store_true', help="Output stats list for the given league(s) and season(s)")
    arg_parser.add_argument('--standings', action='store_true', help="All teams in league, with goals for/against")
    arg_parser.add_argument('--multiple_teams', action='store_true', help="Whether to show all teams a player has played for")
    arg_parser.add_argument('leagues', type=helpers.comma_delimited_list, help="Comma-delimited list (no spaces) of leagues")
    arg_parser.add_argument('start_season', type=int, help="Earliest season for which to scrape data. Second year of the season (i.e. passing 2014 refers to the 2013-14 season)")
    arg_parser.add_argument('--range', type=int, help="Choose the latest season to parse to parse many seasons at once. Second year of the season (i.e. passing 2014 refers to the 2013-14 season)", required=False)

    args = arg_parser.parse_args()

    start_season = args.start_season
    end_season = args.range if args.range is not None else args.start_season
    multiple_teams = args.multiple_teams

    if args.roster:
        results_array = []

        for league in args.leagues:
            for season in range(start_season, end_season + 1):
                try:
                    roster.get_player_rosters(league, season, results_array, multiple_teams)
                except Exception as e:
                    print('Error in {0} {1}'.format(league, season))
                    print(e)

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_rosters.csv'.format(start_season, end_season, '-'.join(args.leagues)))

    if args.team_roster:
        results_array = []

        # When running team_rosters, the 'leagues' argument is actually teams

        for league in args.leagues:
            for season in range(start_season, end_season + 1):
                try:
                    teamroster.get_team_roster('team.php?team={0}&year0={1}'.format(league, season), season, results_array=results_array)
                except Exception as e:
                    print('Error in {0} {1}'.format(league, season))
                    print(e)

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_team_rosters.csv'.format(start_season, end_season, '-'.join(args.leagues)))

    if args.stats:
        results_array = []

        for league in args.leagues:
            for season in range(start_season, end_season + 1):
                try:
                    stats.get_player_stats(league, season, results_array, multiple_teams)
                except Exception as e:
                    print('Error in {0} {1}'.format(league, season))
                    print(e)

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_stats.csv'.format(start_season, end_season, '-'.join(args.leagues)))

    if args.standings:
        results_array = []

        for league in args.leagues:
            for season in range(start_season, end_season + 1):
                try:
                    standings.get_league_standings(league, season, results_array)
                except Exception as e:
                    print('Error in {0} {1}'.format(league, season))
                    print(e)

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_standings.csv'.format(start_season, end_season, '-'.join(args.leagues)))

    print("Success!")


main()
