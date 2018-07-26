# -*- coding: utf-8 -*-

import csv


if __name__ == "__main__":

    code = "000660"
    filename = "c:/data/" + code + ".csv"
    #filename = "./data/" + code + ".csv"
    # filename = code + ".csv"
    f = open(filename, "r",  encoding='UTF8')
    # f = open(filename, "r")
    rdr = csv.reader(f)

    csv_f = open(code + "_edit.csv", 'w', encoding='utf-8', newline='')
    wr = csv.writer(csv_f)
    # code = filename[30:36]

    for line in rdr:
        if(line[0][:10] =="2018-07-26"):
            wr.writerow(line)

    f.close()
    csv_f.close()