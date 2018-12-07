import sys
_NOT_SET_ = "_NOT_SET_"

# These settings can be overridden by local_settings.py

# Stock settings
ALLOWED_SYMBOLS = []
USER_EMAIL = _NOT_SET_
USER_PASSWORD = _NOT_SET_
MAKE_TRADE = False
OPEN_HOUR_SLEEP = 10
TIMEZONE = "US/Pacific"
MARKETS = ["XNAS"]

# Trading policy settings
MAX_MONEY_PER_SYMBOL = 1000
ACTION_DIFF_PERCENTAGE = 1.005

# Notification settings
SENDGRID_API_KEY = _NOT_SET_  # APPLY_ONE_FROM_SENDGRID_WEBSITE
SENDGRID_FROM_EMAIL = _NOT_SET_
SENDGRID_TO_EMAIL = _NOT_SET_

thismodule = sys.modules[__name__]
try:
    import local_settings
    for key in dir(local_settings):
        setattr(thismodule, key, getattr(local_settings, key))
except ModuleNotFoundError:
    pass

for key in dir(thismodule):
    if key is not "_NOT_SET_" and getattr(thismodule, key) is _NOT_SET_:
        raise AttributeError("%s should be set in local_settings." % key)
