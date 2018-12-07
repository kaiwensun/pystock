import enum
import robin_stocks
import pprint

from app.stock import infomation, analysis
from app.notification import email
from app.shared import utils


class OrderType(enum.Enum):
    limit = 'limit'
    market = 'market'


class TriggerType(enum.Enum):
    immediate = 'immediate'
    stop = 'stop'


class TradeType(enum.Enum):
    buy = 'buy'
    sell = 'sell'


def trade(holding, action, quantity, price=None, order_type=OrderType.market,
          trigger_type=TriggerType.immediate, stop_price=None,
          extended_hours=False):
    account = infomation.get_account_info(key='url')
    _stock_id = holding['stock_id']
    _instrument_url = robin_stocks.urls.instruments()
    instrument = "{}{}/".format(_instrument_url, _stock_id)
    symbol = holding['symbol']
    typ = isinstance(order_type, OrderType) and order_type.value
    time_in_force = 'gfd'
    trigger = isinstance(trigger_type, TriggerType) and trigger_type.value
    price = price if price is not None else holding['latest_price']
    stop_price = None if trigger_type == TriggerType.stop else stop_price
    if action == TradeType.buy:
        # buying_power may change due to buying using mobile app.
        # so update=True
        margin_balances = infomation.get_account_info(
            key='margin_balances', update=True)
        buying_power = utils.get_float(
            margin_balances['day_trade_buying_power'])
        if buying_power is None:
            # This is unexpected
            email.send_debug_alert(
                "buying_pwoer is None" +
                str(margin_balances))
            quantity = 0
        if quantity * price > buying_power:
            quantity = buying_power // price
    elif action == TradeType.sell:
        available_quantity = \
            holding['quantity'] - holding['shares_held_for_sells']
        quantity = min(available_quantity, quantity)
    if quantity == 0:
        return None
    side = isinstance(action, TradeType) and action.value
    params = {
        'account': account,
        'instrument': instrument,
        'symbol': symbol,
        'type': typ,
        'time_in_force': time_in_force,
        'trigger': trigger,
        'price': price,
        'quantity': quantity,
        'side': side
    }
    if stop_price is not None:
        params['stop_price'] = stop_price
    if extended_hours:
        params['extended_hours'] = 'true'

    order_url = robin_stocks.urls.orders()
    # This is temporarily used to let mobile app pause pystock trading this
    # stock. Make 10 limit buy orders with $0.01 each, then you'll have a
    # share_held_for_buys > 9 almost forever.
    if holding['shares_held_for_buys'] > 9:
        response = "stop trading due to shares_held_for_buys = {}".format(
            holding['shares_held_for_buys'])
    else:
        response = robin_stocks.helper.request_post(order_url, params)
        # Force update cached account info (eg. available buying power)
        infomation.get_account_info(update=True)
    details = {
        'request': params,
        'response': response
    }
    analysis.expires_daily_extremes(holding, action)
    details_str = pprint.pformat(details, indent=4)
    # This is temporarily used to let mobile app pause pystock sending emails
    if holding['shares_held_for_buys'] > 15:
        email.send_stock_order_email(
            symbol, order_type, quantity, price, details_str)
    return details
