from app.stock import trade
from copy import deepcopy
from config import settings

_MEMORY_STORAGE = {}


def clear_daily_storage():
    global _MEMORY_STORAGE
    _MEMORY_STORAGE = {}


def expires_daily_extremes(holding, trade_type):
    """
    Call this function when you make a trade based on the daily extreme price.
    If a buy was made, extreme_type = high
    If a sell was made, extreme_type = low
    _MEMORY_STORAGE = {
        "AMZN": {
            "high": {
                "price": 2000.23,
                "after_trade": False
            },
            "low": {
                "price": 1800.3,
                "after_trade": True  # this is True if a trade was made today
            }
        },
        ...
    }
    """
    if trade_type is trade.TradeType.buy:
        extreme_type = 'high'
    elif trade_type is trade.TradeType.sell:
        extreme_type = 'low'
    symbol = holding['symbol']
    _MEMORY_STORAGE.get(symbol, {}) \
        .get(extreme_type, {}) \
        .update({
            'price': holding['latest_price'],
            'after_trade': True})


def _intend_to_trade(holding, suggestion):
    """
    trade_type: can be TradeType.buy, TradeType.sell, or None.
    return: True - you should fullfill the intention
            False - hold off the intention
    the intention counts are reset to 0 once a fullfill is suggested
    """
    if suggestion is None:
        trade_type = None
    else:
        trade_type = suggestion[0]
    TRADE_INTENTION_THRESHOLD = 2
    symbol = holding['symbol']
    stock_storage = _MEMORY_STORAGE.setdefault(symbol, {})
    shold_fullfill = False
    if trade_type is None:
        stock_storage['intend_buy'] = 0
        stock_storage['intend_sell'] = 0
        return False
    elif trade_type is trade.TradeType.buy:
        stock_storage['intend_buy'] = \
            (stock_storage.get('intend_buy') or 0) + 1
        stock_storage['intend_sell'] = 0
        shold_fullfill = \
            stock_storage['intend_buy'] >= TRADE_INTENTION_THRESHOLD
    elif trade_type is trade.TradeType.sell:
        stock_storage['intend_buy'] = 0
        stock_storage['intend_sell'] = \
            (stock_storage.get('intend_sell') or 0) + 1
        shold_fullfill = \
            stock_storage['intend_sell'] >= TRADE_INTENTION_THRESHOLD
    if shold_fullfill:
        stock_storage['intend_buy'] = 0
        stock_storage['intend_sell'] = 0
    return shold_fullfill


def _update_daily_extremes_after_trade(holding):
    symbol = holding['symbol']
    latest_price = holding['latest_price']
    stock_storage = _MEMORY_STORAGE.setdefault(symbol, {})
    if latest_price is not None:
        # calc highest
        for extreme_type in ['high', 'low']:
            extreme = None
            if stock_storage.get(extreme_type, {}).get('after_trade'):
                after_trade = True
                stored_extreme = stock_storage \
                    .get(extreme_type, {}) \
                    .get('price')
                if stored_extreme is None:
                    extreme = latest_price
                else:
                    if extreme_type == 'high':
                        extreme = max(stored_extreme, latest_price)
                    else:
                        extreme = min(stored_extreme, latest_price)
            else:
                after_trade = False
                extreme = holding[extreme_type]
                if extreme is None:
                    extreme = latest_price
            stock_storage \
                .setdefault(extreme_type, {}) \
                .update({'price': extreme, 'after_trade': after_trade})
    return deepcopy(_MEMORY_STORAGE[symbol])


def analyze(holding):
    daily_extremes = _update_daily_extremes_after_trade(holding)
    available_quantity = holding['quantity'] - holding['shares_held_for_sells']
    daily_high = daily_extremes.get('high', {}).get('price')
    daily_low = daily_extremes.get('low', {}).get('price')
    latest_price = holding['latest_price']
    suggestion = None
    if daily_high is not None and latest_price is not None:
        if daily_high / settings.ACTION_DIFF_PERCENTAGE > latest_price:
            if available_quantity > 1:
                # sell all shares to stop loss
                suggestion = (trade.TradeType.sell, 1)
    if not suggestion and daily_low is not None and latest_price is not None:
        # TODO: check available buying power before suggesting to buy
        if daily_low * settings.ACTION_DIFF_PERCENTAGE < latest_price:
            max_shares = settings.MAX_MONEY_PER_SYMBOL // latest_price
            if holding['quantity'] + \
                    holding['shares_held_for_sells'] + 1 <= max_shares:
                suggestion = (trade.TradeType.buy, 1)
    if _intend_to_trade(holding, suggestion):
        return suggestion
    return None
