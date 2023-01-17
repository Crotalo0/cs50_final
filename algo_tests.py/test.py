# """File only for testing algorithms"""
# from cs50 import SQL
# import datetime

# db = SQL("sqlite:///users.sqlite3")
# user_id = 11

# date = db.execute("SELECT timeout_time FROM otp_timeout WHERE user_id=?", user_id)
# temp_now = datetime.datetime.now()
# datetime_now = datetime.datetime(
#     temp_now.year,
#     temp_now.month,
#     temp_now.day,
#     temp_now.hour,
#     temp_now.minute,
#     temp_now.second,
# )
# time1, time2 = date[0]["timeout_time"].split(" ")
# year, month, day = time1.split("-")
# hour, minutes, seconds = time2.split(":")
# year = int(year)
# month = int(month)
# day = int(day)
# hour = int(hour) + 1
# minutes = int(minutes)
# seconds = int(seconds)

# datetime_db = datetime.datetime(year, month, day, hour, minutes, seconds)

# delta = datetime_now - datetime_db

# print(type(delta))
# if delta > datetime.timedelta(minutes=30):
#     print("hello")

ciao = []

if not ciao:
    print("hey")
