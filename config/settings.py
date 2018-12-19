import sys
_NOT_SET_ = "_NOT_SET_"

# These settings can be overridden by local_settings.py

# Stock settings
MANAGED_STOCKS = {
    "ORCL": {
        "symbol": "ORCL",
        "strategy": "chase",
        "max_money": 1000,
        "buy_price_trigger": 1.008,
        "sell_price_trigger": 1/1.01,
        "buy_quantity_ratio": 0.5,
        "sell_quantity_ratio": 0.75,
        "trade_price_margin": 0.001,
        "extended_hours": True
    }
}
USER_EMAIL = _NOT_SET_
USER_PASSWORD = _NOT_SET_
MAKE_TRADE = False
OPEN_HOUR_SLEEP = 10
TIMEZONE = "US/Pacific"
MARKETS = ["XNAS"]

# Notification settings
SENDGRID_API_KEY = _NOT_SET_  # APPLY_ONE_FROM_SENDGRID_WEBSITE
SENDGRID_FROM_EMAIL = _NOT_SET_
SENDGRID_TO_EMAIL = _NOT_SET_

# Control settings
PROPAGATE_EXCEPTION = False

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
