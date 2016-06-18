import requests
import html5lib
import xml.etree.ElementTree as etree

html_prefix = '{http://www.w3.org/1999/xhtml}'


def find_from_xpath(root, xpath):
    xpath_modified = '/{0}'.format(html_prefix).join(xpath.split('/'))
    return root.find(xpath_modified)


def get_player_name(root, number, is_away):
    roster_table = find_from_xpath(root, './body/table[1]/tbody/tr[3]/td[{0}]/table/tbody'.format('1' if is_away else '3'))
    for player in roster_table[2:]:
        if len(player[1].text.strip()) < 1:
            continue
        if int(player[1].text) == int(number):
            bold = find_from_xpath(player[2], './b')
            if find_from_xpath(player[2], './b') is not None:
                name = bold.text
            else:
                name = player[2].text
            return name.split(',')[1].strip() + ' ' + name.split(',')[0].strip() + '-' + number
    print('failed to find player name for number\'' + str(number) + '\'')
    return number


def scrape_gamesheets(game_ids, url):
    goals = [['GameID', 'date', 'visiting team', 'home team', 'GF team', 'GA team', 'period', 'time', 'scorer', 'assist1', 'assist2', 'situation', 'plus', 'minus']]

    for game_id in game_ids:
        game_request = requests.get(url.format(game_id))
        if 'This game is not available.' in game_request.text:
            print('Game {0} not available'.format(game_id))
            continue
        game_report = html5lib.parse(game_request.text)

        date = find_from_xpath(game_report, './body/table[1]/tbody/tr[2]/td/table/tbody/tr/td[1]')[2].tail.strip()
        visiting_team = find_from_xpath(game_report, './body/table[1]/tbody/tr[2]/td/table/tbody/tr/td[2]')[0].tail.strip()
        home_team = find_from_xpath(game_report, './body/table[1]/tbody/tr[2]/td/table/tbody/tr/td[3]')[0].tail.strip()

        away_goals_table = find_from_xpath(game_report, './body/table[2]/tbody/tr/td[1]/table/tbody')
        home_goals_table = find_from_xpath(game_report, './body/table[2]/tbody/tr/td[2]/table/tbody')

        for row in away_goals_table[2:] + home_goals_table[2:]:
            if (len(row[0].text.strip())) < 1:
                continue

            is_away = row in away_goals_table[2:]

            time = row[1].text.strip()
            if time[0] == ':':
                time = '0' + time

            period = row[0].text.strip()
            if period[0].isdigit():
                period = period[0]

            def parse_plus_minus(player_number_list, is_away_local):
                non_empty_list = filter(lambda x: len(x.strip()) > 0, map(lambda x: x.text, player_number_list))
                return list(map(lambda x: get_player_name(game_report, x, is_away_local), non_empty_list))

            plusses = parse_plus_minus(row[4:10], is_away)
            minuses = parse_plus_minus(row[10:16], not is_away)

            if len(plusses) > 0 and len(minuses) > 0:
                strength = str(len(plusses)) + 'v' + str(len(minuses))
            else:
                strength = row[2].text.strip()

            goals.append([
                game_id,
                date,
                visiting_team,
                home_team,
                visiting_team if is_away else home_team,
                home_team if is_away else visiting_team,
                period,
                time,
                get_player_name(game_report, row[3].text.strip().split('-')[0], is_away),
                get_player_name(game_report, row[3].text.strip().split('-')[1], is_away) if len(row[3].text.split('-')) > 1 else '',
                get_player_name(game_report, row[3].text.strip().split('-')[2], is_away) if len(row[3].text.split('-')) > 2 else '',
                strength,
                ','.join(plusses),
                ','.join(minuses),
            ])

        print('{0}/{1}'.format(str(game_ids.index(game_id) + 1), str(len(game_ids))))

    return goals
