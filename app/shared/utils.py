import datetime
import pytz

from config import settings


def get_int(num):
    if num is None:
        return None
    return int(float(num))


def get_float(num):
    if num is None:
        return None
    return float(num)


def round_price(price):
    if price > 1:
        return "{:.2f}".format(price)
    else:
        return "{:.4f}".format(price)


def get_timestamp():
    time_format = '%m/%d/%Y %H:%M:%S %Z'
    timestamp = datetime.datetime.now(tz=pytz.timezone(settings.TIMEZONE))
    return timestamp.strftime(time_format)
