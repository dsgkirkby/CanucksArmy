import csv

ID = 0
NAME = 1


def export_array_to_csv(array, name):
    with open(name, 'w', newline='') as csvFile:
        csv_writer = csv.writer(csvFile)
        for resultRow in array:
            for index, item in enumerate(resultRow):
                resultRow[index] = str(item)\
                    .replace(u'\u0148', 'n')\
                    .replace(u'\u2010', '-')\
                    .replace(u'\u0107', 'c')\
                    .replace(u'\x9E', u'\u017E')\
                    .replace(u'\u010d', 'c')\
                    .replace(u'\u0441', 'c')\
                    .replace(u'\u013d', 'L')\
                    .replace(u'\u013e', 'l')\
                    .replace(u'\u0159', 'r')\
                    .replace(u'\x9a', 's')
            try:
                csv_writer.writerow(resultRow)
            except UnicodeEncodeError as e:
                print(e)


def comma_delimited_list(string):
    return string.split(',')
