from app.stock.trade import TradeType


def analyze(holding):
    available_quantity = holding['quantity'] - holding['shares_held_for_sells']
    if holding['high'] and holding['latest_price']:
        if holding['high'] * 0.97 > holding['latest_price']:
            if available_quantity > 1:
                # sell all shares to stop loss
                return (holding, TradeType.sell, 1)
    elif holding['low'] and holding['latest_price']:
        if holding['low'] * 1.03 > holding['latest_price']:
            if holding['quantity'] < 2 and holding['latest_price'] > 500:
                return (holding, TradeType.buy, 1)
            elif holding['quantity'] < 5 and holding['latest_price'] <= 500:
                return (holding, TradeType.buy, 1)
