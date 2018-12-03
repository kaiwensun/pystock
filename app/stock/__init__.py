import robin_stocks
import datetime
import pytz
import time
import os

from config import settings
from app.stock import infomation

login = robin_stocks.login(settings.USER_EMAIL, settings.USER_PASSWORD)

_LAST_FILE_HOUR_ = None
_LOG_FILE_NAME_ = None


def run_service():
    while True:
        holdings = None
        market_info = infomation.market_open_time(settings.MARKETS[0])
        if not market_info['is_open_today']:
            logger("sleep during holiday")
            time.sleep(60 * 60)
        elif market_info['is_open_now']:
            logger("work during open hours")
            holdings = infomation.build_holdings()
        elif market_info['end - utcnow'] <= 0:
            logger("sleep after market closed")
            time.sleep(60 * 60)
        elif market_info['utcnow - start'] > -60 * 5:
            logger("work when market is about to open")
            holdings = infomation.build_holdings()
        else:
            logger("sleep when market has not opened yet")
            time.sleep(- market_info['utcnow - start'] - 60 * 3)
        if holdings is not None:
            logger(holdings)
        time.sleep(settings.OPEN_HOUR_SLEEP)


def logger(info):
    global _LAST_FILE_HOUR_
    global _LOG_FILE_NAME_
    import pprint
    pprint.pprint(info)
    timestamp = datetime.datetime.now(tz=pytz.timezone(settings.TIMEZONE))
    hour = timestamp.hour
    if _LAST_FILE_HOUR_ != hour:
        _LAST_FILE_HOUR_ = hour
        time_format = '%Y-%m-%dT%H%M%Sz%Z'
        timestamp.strftime(time_format)
        _LOG_FILE_NAME_ = os.path.join(
            "logs", "{}.log".format(
                timestamp.strftime(time_format)))
        if not os.path.exists(os.path.dirname(_LOG_FILE_NAME_)):
            os.makedirs(os.path.dirname(_LOG_FILE_NAME_))
    logtext = pprint.pformat(info, indent=4)
    try:
        with open(_LOG_FILE_NAME_, "a") as myfile:
            myfile.write(logtext + '\n')
    finally:
        myfile.close()
