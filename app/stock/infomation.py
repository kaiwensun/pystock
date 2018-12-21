import datetime
import pytz
import robin_stocks

from app.shared import utils

_NEED_UPDATE = set()
_MONITORED_STOCKS = {}
_ACCOUNT_PROFILE = None


class NoneExtractableError(ValueError):
    pass


class MismatchResultError(ValueError):
    pass


def retry(func):
    def retry_wrapper(lst, *args, **kwargs):
        RETRY_TIME = 3
        for _ in range(RETRY_TIME):
            nee = None
            res = None
            try:
                res = func(lst, *args, **kwargs)
                valid = len(lst) == len(res) and all(res)
            except NoneExtractableError as e:
                valid = False
                nee = e
            if valid:
                return res
        log = {
            'func': func.__code__,
            'lst': lst,
            'args': args,
            'kwargs': kwargs,
            'res': res
        }
        if nee is None:
            raise MismatchResultError(log)
        else:
            nee.args += (log,)
            raise nee
    return retry_wrapper


def mark_need_update(symbol):
    _NEED_UPDATE.add(symbol)


def _extract_obj(lst, keys, rename={}, typs={}):
    """
    Extract from a list of dicts to get only key-value pairs that we are
    interested in.

    :param lst: The list of dicts that we want to extract from.
    :param keys: The list of keys that we are interested in.
    :param renames: a mapping to rename the keys of the output dict.
    :return: a list of extracted dicts.
    """
    extracted_lst = []
    for obj in lst:
        if not obj:
            # This is an exception that happens quite often
            raise NoneExtractableError(lst, keys)
        extracted = {}
        for key in keys:
            if typs.get(key):
                obj[key] = typs.get(key)(obj[key])
            extracted[rename.get(key, key)] = obj[key]
        extracted_lst.append(extracted)
    return extracted_lst


@retry
def get_fundamentals(symbols):
    fundamentals_data = robin_stocks.stocks.get_fundamentals(symbols)
    keys = ['open', 'high', 'low']
    typs = {'open': utils.get_float,
            'high': utils.get_float,
            'low': utils.get_float}
    return _extract_obj(fundamentals_data, keys, typs=typs)


@retry
def get_instruments(symbols):
    instruments_data = robin_stocks.stocks.get_instruments_by_symbols(symbols)
    keys = ['tradability', 'rhs_tradability', "simple_name", "id", "symbol"]
    renames = {"id": "stock_id"}
    return _extract_obj(instruments_data, keys, renames)


@retry
def get_quotes(symbols):
    quotes_data = robin_stocks.stocks.get_quotes(symbols)
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
    extracted_data = _extract_obj(quotes_data, keys, typs=typs)
    for item in extracted_data:
        item['latest_price'] = (
            item['last_extended_hours_trade_price'] or
            item['last_trade_price'])
    return extracted_data


@retry
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


def build_holdings(symbols):
    MAX_LIST_LEN = 3
    holdings = []
    for start in range(0, len(symbols), MAX_LIST_LEN):
        sub_symbols = symbols[start: start + MAX_LIST_LEN]
        sub_holdings = _build_holdings(sub_symbols)
        holdings.extend(sub_holdings)
    return holdings


def _build_holdings(symbols):
    fundamentals = get_fundamentals(symbols)
    instruments = get_instruments(symbols)
    quotes = get_quotes(symbols)
    stock_ids = [instrument['stock_id'] for instrument in instruments]
    positions = get_positions(stock_ids)
    timestamp = utils.get_timestamp()
    holdings = [{'timestamp': timestamp} for _ in symbols]
    for i in range(len(holdings)):
        for data_lst in [fundamentals, instruments, quotes, positions]:
            try:
                holdings[i].update(data_lst[i])
            except IndexError as e:
                # This error has happend a few times. Let's investigate
                e.args = e.args + ('i={}'.format(i),
                                   repr(holdings), repr(data_lst))
                raise
    return holdings
