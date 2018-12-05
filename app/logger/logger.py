import datetime
import pytz
import time
import os

from config import settings

_LAST_FILE_HOUR_ = None
_LOG_FILE_NAME_ = None


def _log(info):
    global _LAST_FILE_HOUR_
    global _LOG_FILE_NAME_
    import pprint
    pprint.pprint(info)
    timestamp = datetime.datetime.now(tz=pytz.timezone(settings.TIMEZONE))
    hour = timestamp.hour
    if _LAST_FILE_HOUR_ != hour:
        _LAST_FILE_HOUR_ = hour
        time_format = '%Y-%m-%dT%H-%M-%S-%Z'
        timestamp.strftime(time_format)
        _LOG_FILE_NAME_ = os.path.join("logs", str(timestamp.year),
                                       str(timestamp.month), str(
                                           timestamp.day),
                                       "{}.log".format(timestamp.strftime(time_format)))
        if not os.path.exists(os.path.dirname(_LOG_FILE_NAME_)):
            os.makedirs(os.path.dirname(_LOG_FILE_NAME_))
    logtext = pprint.pformat(info, indent=4)
    try:
        with open(_LOG_FILE_NAME_, "a") as myfile:
            myfile.write(logtext + '\n')
    finally:
        myfile.close()


def debug(info):
    return _log(info)
