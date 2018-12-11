import datetime
import pytz
import robin_stocks

from config import settings
from app.shared import utils

_NEED_UPDATE = set()
_MONITORED_STOCKS = {}
_ACCOUNT_PROFILE = None


def mark_need_update(symbol):
    _NEED_UPDATE.add(symbol)


def _extract_obj(obj_or_lst, keys, rename={}, typs={}):
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
            if typs.get(key):
                obj[key] = typs.get(key)(obj[key])
            extracted[rename.get(key, key)] = obj[key]
        extracted_lst.append(extracted)
    return extracted_lst[0] if is_dict else extracted_lst


def get_fundamentals(symbols):
    fundamental_data = robin_stocks.stocks.get_fundamentals(symbols)
    keys = ['open', 'high', 'low']
    typs = {'open': utils.get_float,
            'high': utils.get_float,
            'low': utils.get_float}
    return _extract_obj(fundamental_data, keys, typs=typs)


def get_instruments(symbols):
    instrument_data = robin_stocks.stocks.get_instruments_by_symbols(symbols)
    keys = ['tradability', 'rhs_tradability', "simple_name", "id", "symbol"]
    renames = {"id": "stock_id"}
    return _extract_obj(instrument_data, keys, renames)


def get_quotes(symbols):
    quote_data = robin_stocks.stocks.get_quotes(symbols)
    keys = ["ask_price", "ask_size", "bid_price", "bid_size",
            "last_trade_price", "last_extended_hours_trade_price"]
    typs = {
        "ask_price": utils.get_float,
        "ask_size": utils.get_float,
        "bid_price": utils.get_float,
        "bid_size": utils.get_float,
        "last_trade_price": utils.get_float,
        "last_extended_hours_trade_price": utils.get_float
    }
    extracted_data = _extract_obj(quote_data, keys, typs=typs)
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
    typs = {
        "shares_held_for_buys": utils.get_int,
        "average_buy_price": utils.get_int,
        "shares_held_for_sells": utils.get_int,
        "quantity": utils.get_int
    }
    return _extract_obj(positions, keys, typs=typs)


def get_account_info(key=None, update=False):
    global _ACCOUNT_PROFILE
    if _ACCOUNT_PROFILE is None or update:
        _ACCOUNT_PROFILE = robin_stocks.profiles.load_account_profile()
    if key is None:
        return _ACCOUNT_PROFILE.copy()
    else:
        return _ACCOUNT_PROFILE.get(key)


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
    timestamp = utils.get_timestamp()
    holdings = [{'timestamp': timestamp} for _ in symbols]
    for i in range(len(holdings)):
        for data_lst in [fundamentals, instruments, quotes, positions]:
            holdings[i].update(data_lst[i])
    return holdings
