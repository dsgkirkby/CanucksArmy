import csv

ID = 0
NAME = 1


def export_array_to_csv(array, name):
    with open(name, 'w', newline='') as csvFile:
        csv_writer = csv.writer(csvFile)
        for resultRow in array:
            csv_writer.writerow(resultRow)


def comma_delimited_list(string):
    return string.split(',')
