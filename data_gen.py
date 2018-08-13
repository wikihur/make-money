import csv

if __name__ == "__main__":
    r_filename = "C:/Users/user/Desktop/Data/000660.csv"
    w_filename = "C:/Users/user/Desktop/Data/000660_edit2.csv"

    fr = open(r_filename, "r", encoding='UTF-8')
    rdr = csv.reader(fr)

    fw = open(w_filename, "w", encoding='UTF-8', newline='')
    wdr = csv.writer(fw)

    #date = "2018-07-26"

    before_date = ""

    start_min_time = 0

    wdr.writerow(["ds", "y"])

    for line in rdr:
        if line[0] == "index":
            continue

        if int(line[1]) < 90000 or int(line[1]) > 153000:
            continue

        date = line[0][:10]
        if(before_date != date) :
            start_min_time = 0

        if date[:10] != "2018-08-09" and date[:10] != "2018-08-08" :
        #if date[:10] != "2018-08-09":
            continue

        #if int(line[1]) < 100000 :
        #    temp = line[1]
        #    h = " " + temp[0]
        #    m = temp[1:3]
        #    s = temp[3:]
        #    data = [ date + h + ":" + m + ":" + s, abs(int(line[2])) ]
        #else :

        temp = line[1]
        h = " " + temp[:2]
        m = temp[2:4]
        s = temp[4:]

        if (int(m) >= start_min_time):

            if (int(m) < (start_min_time + 1)):
                start_min_time += 1

                if(start_min_time == 60):
                    start_min_time = 0

                data = [date + h + ":" + m + ":00", abs(int(line[2]))]
                wdr.writerow(data)

        #data = [ date + h + ":" + m + ":" + s, abs(int(line[2])) ]
        #data = [date + h + ":" + m + ":00", abs(int(line[2]))]

        #if before_data != line[1]:
        #    #print(data)
        #    wdr.writerow(data)

        before_date = date

    fr.close()
    fw.close()
