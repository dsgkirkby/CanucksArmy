import csv
import re
import requests
import json
from unidecode import unidecode

html_prefix = '{http://www.w3.org/1999/xhtml}'


def export_array_to_csv(array, name):
    with open(name, 'w', newline='') as csvFile:
        csv_writer = csv.writer(csvFile)
        for resultRow in array:
            for index, item in enumerate(resultRow):
                resultRow[index] = unidecode(str(item)).replace('"', '\\"')
            try:
                csv_writer.writerow(resultRow)
            except UnicodeEncodeError as e:
                print(e)


def export_dict_array_to_csv(array, name):
    with open(name, 'w', newline='') as csvFile:
        writer = csv.DictWriter(csvFile, array[0].keys())
        writer.writeheader()
        writer.writerows(array)


def comma_delimited_list(string):
    return string.split(',')


def flatten(thing):
    return [item for sublist in thing for item in sublist]


def listmap(iteratee, func):
    return list(map(func, iteratee))


def strip_extra_spaces(text):
    return re.sub(' +', ' ', text)


def get_json(url):
    request = requests.get(url)
    decoder = json.JSONDecoder()
    return decoder.decode(request.text)


def get_player_id_from_url(url):
    slashes = [i for i, ltr in enumerate(url) if ltr == '/']
    return url[slashes[-2] + 1:slashes[-1]]


def get_ep_table_rows(table):
    rows_by_section = []
    sections = table.findall('.//{}tbody'.format(html_prefix))

    if len(sections) == 1:  # this is the case when there's no category to group by, for example a league without conferences
        section_rows = sections[0].findall(
            './/{}tr'.format(html_prefix))

        rows_by_section.append(section_rows)
    else:
        # first tbody is usually just the header
        for section_number in range(0, len(sections)):
            # Last row is the title row for the next round (unless it's the last round)
            section_rows = sections[section_number].findall(
                './/{}tr'.format(html_prefix))

            if len(section_rows) > 1:
                num_rows = len(section_rows) if section_number == len(
                    sections) - 1 else len(section_rows) - 1

                rows_by_section.append(section_rows[:num_rows])

    return rows_by_section


def get_info_from_player_name(name: str):
    name_raw = name.strip()
    name_parts = name_raw.split('(')

    # Some players have no position or other data listed for some reason
    if len(name_parts) < 2:
        return name_raw, None

    name = name_parts[0].strip()
    position = name_parts[1][:-1].strip()

    return name, position
