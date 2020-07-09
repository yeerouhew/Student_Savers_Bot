import datetime

import pytz as pytz


# data from luminus api
def com1_data(level):
    room_label = [];
    if level == "LevelB1":
        room_label = ["COM1-B102", "COM1-B103", "COM1-B108", "COM1-B109", "COM1-B110", "COM1-B111", "COM1-B112",
                      "COM1-B113"]

    elif level == "Level1":
        room_label = ["COM1-0113", "COM1-0114", "COM1-0120"]

    elif level == "Level2":
        room_label = ["COM1-0201", "COM1-0203", "COM1-0204", "COM1-0206", "COM1-0207", "COM1-0208", "COM1-0209",
                      "COM1-0210", "COM1-0212", "COM1-0216", "COM1-0217"]

    return room_label


def com2_data(level):
    room_label = [];
    if level == "Level1":
        room_label = ["COM2-0108"]
    return room_label


def return_weekNo(dateNo):
    # changing timezone to Singapore's
    local_tz = pytz.timezone('Asia/Singapore')
    currentDate = dateNo.replace(tzinfo=pytz.UTC).astimezone(local_tz)

    startOfweek1 = datetime.datetime(2020, 6, 23).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek1 = datetime.datetime(2020, 6, 30).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek2 = datetime.datetime(2020, 8, 19).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek2 = datetime.datetime(2020, 8, 25).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek3 = datetime.datetime(2020, 8, 26).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek3 = datetime.datetime(2020, 9, 1).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek4 = datetime.datetime(2020, 9, 2).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek4 = datetime.datetime(2020, 9, 8).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek5 = datetime.datetime(2020, 9, 9).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek5 = datetime.datetime(2020, 9, 15).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek6 = datetime.datetime(2020, 9, 16).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek6 = datetime.datetime(2020, 9, 22).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek7 = datetime.datetime(2020, 9, 30).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek7 = datetime.datetime(2020, 10, 6).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek8 = datetime.datetime(2020, 10, 7).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek8 = datetime.datetime(2020, 10, 13).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek9 = datetime.datetime(2020, 10, 14).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek9 = datetime.datetime(2020, 10, 20).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek10 = datetime.datetime(2020, 10, 21).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek10 = datetime.datetime(2020, 10, 27).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek11 = datetime.datetime(2020, 10, 28).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek11 = datetime.datetime(2020, 11, 3).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek12 = datetime.datetime(2020, 11, 4).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek12 = datetime.datetime(2020, 11, 10).replace(tzinfo=pytz.utc).astimezone(local_tz)

    startOfweek13 = datetime.datetime(2020, 11, 11).replace(tzinfo=pytz.utc).astimezone(local_tz)
    endOfweek13 = datetime.datetime(2020, 11, 17).replace(tzinfo=pytz.utc).astimezone(local_tz)

    if startOfweek1 <= currentDate <= endOfweek1:
        return "1"
    elif startOfweek2 <= currentDate <= endOfweek2:
        return "2"
    elif startOfweek3 <= currentDate <= endOfweek3:
        return "3"
    elif startOfweek4 <= currentDate <= endOfweek4:
        return "4"
    elif startOfweek5 <= currentDate <= endOfweek5:
        return "5"
    elif startOfweek6 <= currentDate <= endOfweek6:
        return "6"
    elif startOfweek7 <= currentDate <= endOfweek7:
        return "7"
    elif startOfweek8 <= currentDate <= endOfweek8:
        return "8"
    elif startOfweek9 <= currentDate <= endOfweek9:
        return "9"
    elif startOfweek10 <= currentDate <= endOfweek10:
        return "10"
    elif startOfweek11 <= currentDate <= endOfweek11:
        return "11"
    elif startOfweek12 <= currentDate <= endOfweek12:
        return "12"
    elif startOfweek13 <= currentDate <= endOfweek13:
        return "13"
    else:
        return "0"

# all rooms in coms1 and coms2

def all_rooms_com1(level):
    room_array = [];

    print(level)

    if level == "LevelB1":
        room_array = ["COM1-B06", "COM1-B07", "COM1-B102", "COM1-B103", "COM1-B108", "COM1-B109", "COM1-B110",
                      "COM1-B111", "COM1-B112",
                      "COM1-B113", "COM1-B14A", "COM1-B14B"]

    elif level == "Level1":
        room_array = ["COM1-0112", "COM1-0113", "COM1-0114", "COM1-0118", "COM1-0120", "COM1-0122"]

    elif level == "Level2":
        room_array = ["COM1-0201", "COM1-0203", "COM1-0204", "COM1-0206", "COM1-0207", "COM1-0208", "COM1-0209",
                      "COM1-0210", "COM1-0212", "COM1-0213", "COM1-0216", "COM1-0217"]

    elif level == "Level3":
        room_array = ["COM1-0319", "COM1-0328"]

    return room_array


def all_rooms_com2(level):

    print(level)
    room_label = [];
    if level == "Level1":
        room_label = ["COM2-0108"]
    elif level == "Level2":
        room_label = ["COM2-0212", "COM2-0220", "COM2-0223", "COM2-0224", "COM2-0226"]
    elif level == "Level3":
        room_label = ["COM2-0314", "COM2-0319", "COM2-0328", "COM2-0330"]
    elif level == "Level4":
        room_label = ["COM2-0402", "COM2-0406"]

    return room_label