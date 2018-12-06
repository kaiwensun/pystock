import datetime
import pytz
import robin_stocks

from config import settings

_NEED_UPDATE = set()
_MONITORED_STOCKS = {}
_ACCOUNT_PROFILE = None
_MEMORY_STORAGE = {}


def mark_need_update(symbol):
    _NEED_UPDATE.add(symbol)


def _extract_obj(obj_or_lst, keys, rename={}):
    """
    Extract from dict(s) to get only key-value pairs that we are interested in.

    :param obj_or_lst: The dict that we want to extract from, or a list of \
    dicts.
    :param keys: The list of keys that we are interested in.
    :param renames: a mapping to rename the keys of the output dict.
    :return: the extracted dict, or a list of extracted dicts.

    """
    if isinstance(obj_or_lst, dict):
        is_dict = True
        lst = [obj_or_lst]
    else:
        is_dict = False
        lst = obj_or_lst
    extracted_lst = []
    for obj in lst:
        extracted = {}
        for key in keys:
            extracted[rename.get(key, key)] = obj[key]
        extracted_lst.append(extracted)
    return extracted_lst[0] if is_dict else extracted_lst


def get_fundamentals(symbols):
    fundamental_data = robin_stocks.stocks.get_fundamentals(symbols)
    keys = ['open', 'high', 'low']
    return _extract_obj(fundamental_data, keys)


def get_instruments(symbols):
    instrument_data = robin_stocks.stocks.get_instruments_by_symbols(symbols)
    keys = ['tradability', 'rhs_tradability', "simple_name", "id", "symbol"]
    renames = {"id": "stock_id"}
    return _extract_obj(instrument_data, keys, renames)


def get_quotes(symbols):
    quote_data = robin_stocks.stocks.get_quotes(symbols)
    keys = ["ask_price", "ask_size", "bid_price", "bid_size",
            "last_trade_price", "last_extended_hours_trade_price"]
    extracted_data = _extract_obj(quote_data, keys)
    for item in extracted_data:
        item['latest_price'] = (
            item['last_extended_hours_trade_price'] or
            item['last_trade_price'])
    return extracted_data


def get_positions(stock_ids):
    account_number = get_account_info(key='account_number')
    url = "https://api.robinhood.com/accounts/{account_number}/positions/{{stock_id}}/".format(  # noqa
        account_number=account_number)
    positions = []
    for stock_id in stock_ids:
        position = robin_stocks.helper.request_get(
            url.format(stock_id=stock_id))
        positions.append(position)
    keys = ["shares_held_for_buys", "average_buy_price",
            "shares_held_for_sells", "quantity"]
    return _extract_obj(positions, keys)


def get_account_info(key=None, update=False):
    global _ACCOUNT_PROFILE
    if _ACCOUNT_PROFILE is None or update:
        _ACCOUNT_PROFILE = robin_stocks.profiles.load_account_profile()
    if key is None:
        return _ACCOUNT_PROFILE.copy()
    else:
        return _ACCOUNT_PROFILE.get(key)


def get_timestamp():
    time_format = '%m/%d/%Y %H:%M:%S %Z'
    timestamp = datetime.datetime.now(tz=pytz.timezone(settings.TIMEZONE))
    return timestamp.strftime(time_format)


def market_open_time(mic):
    utcnow = datetime.datetime.now(tz=pytz.utc)
    res = {
        'is_open_today': False,
        'is_open_now': False,
        'extended_opens_at': None,
        'extended_closes_at': None,
        'utcnow': utcnow,
        'utcnow - start': None,
        'end - utcnow': None
    }
    url = "https://api.robinhood.com/markets/{mic}/".format(mic=mic)
    market = robin_stocks.helper.request_get(url)
    today_url = market['todays_hours']
    today_market = robin_stocks.helper.request_get(today_url)
    is_open = today_market['is_open']
    if not is_open:
        return res
    res['is_open_today'] = is_open
    start = _parse_market_time(today_market['extended_opens_at'])
    end = _parse_market_time(today_market['extended_closes_at'])
    res['extended_opens_at'] = start
    res['extended_closes_at'] = end
    res['utcnow - start'] = (utcnow - start).total_seconds()
    res['end - utcnow'] = (end - utcnow).total_seconds()
    if res['utcnow - start'] > 0 and res['end - utcnow'] > 0:
        res['is_open_now'] = True
    return res


def _parse_market_time(str):
    # example: "2018-12-03T14:00:00Z"
    return datetime.datetime.strptime(
        str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)


def build_holdings():
    symbols = settings.ALLOWED_SYMBOLS.copy()
    fundamentals = get_fundamentals(symbols)
    instruments = get_instruments(symbols)
    quotes = get_quotes(symbols)
    stock_ids = [instrument['stock_id'] for instrument in instruments]
    positions = get_positions(stock_ids)
    timestamp = get_timestamp()
    holdings = [{'timestamp': timestamp} for _ in symbols]
    for i in range(len(holdings)):
        for data_lst in [fundamentals, instruments, quotes, positions]:
            holdings[i].update(data_lst[i])
    return holdings
