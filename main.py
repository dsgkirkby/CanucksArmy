import argparse

from modules import helpers, stats, roster, teamroster, standings, icetime, team_stats


def main():
    arg_parser = argparse.ArgumentParser(
        description="Get prospect data from any league on the planet over a range of seasons")
    arg_parser.add_argument('--roster', action='store_true',
                            help="Output roster list for the given league(s) and season(s)")
    arg_parser.add_argument('--team_roster', type=str,
                            help="Output roster list for the given team and season(s)")
    arg_parser.add_argument('--stats', action='store_true',
                            help="Output stats list for the given league(s) and season(s)")
    arg_parser.add_argument('--team_stats', type=str,
                            help="Output stats list for the given team and season(s)")
    arg_parser.add_argument('--playoffs', action='store_true',
                            help="Use playoff instead of regular season stats")
    arg_parser.add_argument('--standings', action='store_true',
                            help="All teams in league, with goals for/against")
    arg_parser.add_argument(
        '--icetime', action='store_true', help="NHL icetime for season")
    arg_parser.add_argument('--multiple_teams', action='store_true',
                            help="Whether to show all teams a player has played for")
    arg_parser.add_argument('leagues', type=helpers.comma_delimited_list,
                            help="Comma-delimited list (no spaces) of leagues")
    arg_parser.add_argument('start_season', type=int,
                            help="Earliest season for which to scrape data. Second year of the season (i.e. passing 2014 refers to the 2013-14 season)")
    arg_parser.add_argument(
        '--range', type=int, help="Choose the latest season to parse to parse many seasons at once. Second year of the season (i.e. passing 2014 refers to the 2013-14 season)", required=False)

    args = arg_parser.parse_args()

    start_season = args.start_season
    end_season = args.range if args.range is not None else args.start_season
    multiple_teams = args.multiple_teams
    playoffs = args.playoffs

    if args.icetime:
        if len(args.leagues) is not 1 or args.leagues[0].lower() != "nhl":
            print("Error: Icetime is currently only supported for the NHL")
            return

        results_array = []

        for season in range(start_season, end_season + 1):
            icetime.get_nhl_season_icetime(season, results_array)

        helpers.export_array_to_csv(
            results_array, '{0}-{1}_{2}_icetime.csv'.format(start_season, end_season, 'nhl'))

    if args.roster:
        results_array = []

        for league in args.leagues:
            for season in range(start_season, end_season + 1):
                roster.get_player_rosters(league, season, results_array, multiple_teams)

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_rosters.csv'.format(
            start_season, end_season, '-'.join(args.leagues)))

    if args.team_roster is not None:
        results_array = []

        if len(args.leagues) != 1:
            print(
                'Error: must supply a single league for the team you wish to fetch the roster of')
        else:
            league = args.leagues[0]
            for season in range(start_season, end_season + 1):
                teamroster.get_team_roster('https://eliteprospects.com/team.php?team={0}&year0={1}'.format(
                    args.team_roster, season), season, league, results_array=results_array)

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_team_rosters.csv'.format(
            start_season, end_season, '-'.join(args.leagues)))

    if args.team_stats is not None:
        results_array = []
        goalie_results_array = []

        if len(args.leagues) != 1:
            print(
                'Error: must supply a single league for the team you wish to fetch stats for')
        else:
            league = args.leagues[0]
            for season in range(start_season, end_season + 1):
                team_stats.get_player_stats(
                    'https://www.eliteprospects.com/team/{}/{}-{}?tab=stats#players'.format(
                        args.team_stats,
                        int(season) - 1,
                        season
                    ),
                    season,
                    league,
                    results_array=results_array,
                    goalie_results_array=goalie_results_array
                )

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_team_stats.csv'.format(
            start_season, end_season, '-'.join(args.leagues)))
        helpers.export_array_to_csv(goalie_results_array, '{0}-{1}_{2}_team_goalie_stats.csv'.format(
            start_season, end_season, '-'.join(args.leagues)))

    if args.stats:
        results_array = []
        goalie_results_array = []

        for league in args.leagues:
            for season in range(start_season, end_season + 1):
                stats.get_player_stats(
                    league, season, results_array, goalie_results_array)

        helpers.export_array_to_csv(
            results_array,
            '{0}-{1}_{2}{3}_stats.csv'.format(start_season, end_season, '-'.join(
                args.leagues), '_playoff' if playoffs else '')
        )
        helpers.export_array_to_csv(
            goalie_results_array,
            '{0}-{1}_{2}{3}_goalie_stats.csv'.format(start_season, end_season, '-'.join(
                args.leagues), '_playoff' if playoffs else '')
        )

    if args.standings:
        results_array = []

        for league in args.leagues:
            for season in range(start_season, end_season + 1):
                standings.get_league_standings(
                    league, season, results_array)

        helpers.export_array_to_csv(results_array, '{0}-{1}_{2}_standings.csv'.format(
            start_season, end_season, '-'.join(args.leagues)))

    print("Success!")


if __name__ == '__main__':
    main()
