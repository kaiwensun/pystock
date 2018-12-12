from app.stock import trade
from copy import deepcopy
from config import settings
from app.logger import logger

import math

_MEMORY_STORAGE = {}


def clear_daily_storage():
    global _MEMORY_STORAGE
    _MEMORY_STORAGE = {}


def get_storage(symbol):
    return _MEMORY_STORAGE.get(symbol)


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
    for extreme_type in ['high', 'low']:
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
        trade_type = suggestion['trade_type']
    symbol = holding['symbol']
    stock_storage = _MEMORY_STORAGE.setdefault(symbol, {})
    should_fullfill = False
    if trade_type is None:
        stock_storage['intend_buy'] = 0
        stock_storage['intend_sell'] = 0
        return False
    elif trade_type is trade.TradeType.buy:
        stock_storage['intend_buy'] = \
            (stock_storage.get('intend_buy') or 0) + 1
        stock_storage['intend_sell'] = 0
        should_fullfill = \
            stock_storage['intend_buy'] >= settings.TRADE_INTENTION_THRESHOLD
    elif trade_type is trade.TradeType.sell:
        stock_storage['intend_buy'] = 0
        stock_storage['intend_sell'] = \
            (stock_storage.get('intend_sell') or 0) + 1
        should_fullfill = \
            stock_storage['intend_sell'] >= settings.TRADE_INTENTION_THRESHOLD
    if should_fullfill:
        stock_storage['intend_buy'] = 0
        stock_storage['intend_sell'] = 0
    return should_fullfill


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
        logger.debug("daily_extremes")
        logger.debug(deepcopy(_MEMORY_STORAGE[symbol]))
    return deepcopy(_MEMORY_STORAGE[symbol])


def analyze(holding):
    symbol = holding['symbol']
    stock_config = get_stock_config(symbol)
    strategies = {
        'chase': strategy_chase
    }
    strategy = strategies[stock_config['strategy']]
    return strategy(holding)


def strategy_chase(holding):
    symbol = holding['symbol']
    stock_config = get_stock_config(symbol)
    daily_extremes = _update_daily_extremes_after_trade(holding)
    logger.debug(daily_extremes)
    available_quantity = holding['quantity'] - holding['shares_held_for_sells']
    daily_high = daily_extremes.get('high', {}).get('price')
    daily_low = daily_extremes.get('low', {}).get('price')
    latest_price = holding['latest_price']
    suggestion = None
    if daily_high is not None and latest_price is not None:
        if daily_high * stock_config['sell_price_trigger'] > latest_price:
            if available_quantity > 0:
                quantity = math.ceil(
                    available_quantity *
                    stock_config['sell_quantity_ratio'])
                quantity = min(quantity, available_quantity)
                suggestion = {
                    'trade_type': trade.TradeType.sell,
                    'quantity': quantity}

    if not suggestion and daily_low is not None and latest_price is not None:
        # TODO: check available buying power before suggesting to buy
        if daily_low * stock_config['buy_price_trigger'] <= latest_price:
            max_shares = stock_config['max_money'] // latest_price
            curr_shares = \
                holding['quantity'] + holding['shares_held_for_sells']
            quantity = max(
                1,
                math.ceil(
                    curr_shares *
                    stock_config['buy_quantity_ratio']))
            if curr_shares + quantity > max_shares:
                quantity = max_shares - curr_shares
            if quantity > 0:
                suggestion = {
                    'trade_type': trade.TradeType.buy,
                    'quantity': quantity}

    if _intend_to_trade(holding, suggestion):
        suggestion['extended_hours'] = stock_config['extended_hours']
        return suggestion
    return None


def get_stock_config(symbol):
    return settings.MANAGED_STOCKS[symbol]
