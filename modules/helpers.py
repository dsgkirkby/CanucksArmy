import csv
import re
from unidecode import unidecode


def export_array_to_csv(array, name):
    with open(name, 'w', newline='') as csvFile:
        csv_writer = csv.writer(csvFile)
        for resultRow in array:
            for index, item in enumerate(resultRow):
                resultRow[index] = unidecode(str(item))
            try:
                csv_writer.writerow(resultRow)
            except UnicodeEncodeError as e:
                print(e)


def comma_delimited_list(string):
    return string.split(',')


def flatten(thing):
    return [item for sublist in thing for item in sublist]


def listmap(iteratee, func):
    return list(map(func, iteratee))

def strip_extra_spaces(text):
    return re.sub(' +', ' ', text)
