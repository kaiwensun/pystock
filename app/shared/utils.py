def get_int(num):
    if num is None:
        return None
    return int(float(num))


def get_float(num):
    if num is None:
        return None
    return float(num)


def round_price(price):
    if price > 1:
        return "{:.2f}".format(price)
    else:
        return "{:.4f}".format(price)
