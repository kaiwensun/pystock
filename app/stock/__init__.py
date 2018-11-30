import robin_stocks

from config import settings
from app.stock import infomation

login = robin_stocks.login(settings.USER_EMAIL, settings.UESR_PASSWORD)


def run_service():
    infomation.build_holdings()
