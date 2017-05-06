def get_league_start_year(league: str):
    start_years = {
        'nhl': 1927,
        'ahl': 1941,
    }
    return start_years[league.lower()]
