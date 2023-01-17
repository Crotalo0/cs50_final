"""Useful functions"""
import string
from functools import wraps
import random
import datetime

from flask import redirect, session


def login_required(f):
    """Decorate routes to require login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def secure_password(password: str) -> bool:
    """Check if password is secure enough"""
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    symbol = string.punctuation
    number = string.digits

    if len(password) < 8:
        return False

    for letter in password:
        if (
            letter not in lower
            or letter not in upper
            or letter not in symbol
            or letter not in number
        ):
            condition = False
    condition = True
    return condition


def otp_generator():
    """Generate OTP for password reset route"""
    otp = []
    numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    for _ in range(0, 6):
        otp.append(random.choice(numbers))
    return "".join(otp)


def otp_expired(otp_date, expiration_time, db_key):
    """Check age of OTP"""
    return one_day_old_timeout(otp_date, expiration_time, db_key)


def one_day_old_timeout(timeout_date, timeout_time, db_key):
    """Check date of last timeout (for failed OTP)"""
    # Get current time with custom format
    temp_now = datetime.datetime.now()
    datetime_now = datetime.datetime(
        temp_now.year,
        temp_now.month,
        temp_now.day,
        temp_now.hour,
        temp_now.minute,
        temp_now.second,
    )

    # Split db time
    time1, time2 = timeout_date[0][db_key].split(" ")
    year, month, day = time1.split("-")
    hour, minutes, seconds = time2.split(":")
    year = int(year)
    month = int(month)
    day = int(day)
    hour = int(hour) + 1
    minutes = int(minutes)
    seconds = int(seconds)

    # create datetime object with db time
    datetime_db = datetime.datetime(year, month, day, hour, minutes, seconds)

    # Get time-delta
    time_delta = datetime_now - datetime_db
    if time_delta > timeout_time:
        return True
    return False


def random_url_gen():
    """Generate a random url endpoint for email confirmation"""
    lower = string.ascii_lowercase
    number = string.digits
    ascii_array = [lower, number]
    final_url = []
    for i in range(15):
        lower_or_number = random.randint(0, 1)
        final_url.append(random.choice(ascii_array[lower_or_number]))
    return "".join(final_url)


if __name__ == "__main__":
    x = random_url_gen()
    print(x)
