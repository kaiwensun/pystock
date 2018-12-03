import sys
_NOT_SET_ = "_NOT_SET_"

# These settings can be overridden by local_settings.py

ALLOWED_SYMBOLS = []
USER_EMAIL = "USER_EMAIL"
USER_PASSWORD = "USER_PASSWORD"

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
