import requests
import html5lib
import xml.etree.ElementTree as etree

html_prefix = '{http://www.w3.org/1999/xhtml}'


def find_from_xpath(root, xpath):
    xpath_modified = '/{0}'.format(html_prefix).join(xpath.split('/'))
    return root.find(xpath_modified)


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

            if row in away_goals_table[2:]:
                gf_team = visiting_team
                ga_team = home_team
            else:
                gf_team = home_team
                ga_team = visiting_team

            goals.append([
                game_id,
                date,
                visiting_team,
                home_team,
                gf_team,
                ga_team,
                row[0].text.strip(),
                row[1].text.strip(),
                row[3].text.strip().split('-')[0],
                row[3].text.strip().split('-')[1] if len(row[3].text.split('-')) > 1 else '',
                row[3].text.strip().split('-')[2] if len(row[3].text.split('-')) > 2 else '',
                '' if row[2].text is None else row[2].text.strip(),
                ','.join(list(filter(lambda x: len(x.strip()) > 0, map(lambda x: x.text, row[4:9])))),
                ','.join(list(filter(lambda x: len(x.strip()) > 0, map(lambda x: x.text, row[10:15])))),
            ])

        print('{0}/{1}'.format(str(game_ids.index(game_id) + 1), str(len(game_ids))))

    return goals
