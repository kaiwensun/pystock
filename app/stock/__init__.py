import robin_stocks
import time

from config import settings
from app.stock import infomation, analysis, trade
from app.logger import logger


def run_service():
    robin_stocks.login(settings.USER_EMAIL, settings.USER_PASSWORD)
    while True:
        holdings = None
        sleep_time = settings.OPEN_HOUR_SLEEP
        market_info = infomation.market_open_time(settings.MARKETS[0])
        if not market_info['is_open_today']:
            logger.debug("sleep during holiday")
            analysis.clear_daily_storage()
            sleep_time = 60 * 60
        elif market_info['is_open_now']:
            logger.debug("work during open hours")
            holdings = infomation.build_holdings()
        elif market_info['end - utcnow'] <= 0:
            logger.debug("sleep after market closed")
            analysis.clear_daily_storage()
            sleep_time = 60 * 60
        elif market_info['utcnow - start'] > -60 * 5:
            logger.debug("work when market is about to open")
            holdings = infomation.build_holdings()
        else:
            logger.debug("sleep when market has not opened yet")
            analysis.clear_daily_storage()
            sleep_time = - int(market_info['utcnow - start']) - 60 * 3

        if holdings is not None:
            logger.debug("holding")
            logger.debug(holdings)
            for holding in holdings:
                strategy = analysis.analyze(holding)
                if strategy:
                    logger.debug("suggestion/strategy")
                    logger.debug(strategy)
                    details = trade.trade(
                        holding, strategy['trade_type'], strategy['shares'])
                    if details is not None:
                        logger.debug("trade_details")
                        logger.debug(details)
        time.sleep(sleep_time)
