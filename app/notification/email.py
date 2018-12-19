from sendgrid import SendGridAPIClient
from config import settings
from sendgrid.helpers.mail import Email, Content, Mail
from app.logger import logger
from app.shared import utils

__all__ = ['send', 'send_stock_order_email']


def send(subject, content, from_email=settings.SENDGRID_FROM_EMAIL,
         to_email=settings.SENDGRID_TO_EMAIL, content_type="text/plain"):
    sg = SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
    from_email = Email(from_email)
    to_email = Email(to_email)
    subject = "[pystock] {}".format(subject)
    content = Content(content_type, content)
    mail = Mail(from_email, subject, to_email, content)
    try:
        response = sg.client.mail.send.post(request_body=mail.get())
    except Exception:
        response = False
    if response and response.status_code != 202:
        logger.debug("Failed to send message: {}. Status code {}".format(
            content, response.status_code))
    elif not response:
        logger.debug("Failed to send message: {}. response is {}".format(
            content, response))


def send_stock_order_email(symbol, trade_type_value, quantity, price, details):
    subject = "{}ing {} share{} of {} at ${}.".format(
        trade_type_value, quantity, '' if quantity == 1 else 's', symbol,
        price)
    send(subject, details)


def send_debug_alert(content):
    subject = "debug alert"
    send(subject, content)


def send_on_start():
    subject = "service starts"
    managed_stocks = "".join([
        "<li>{}</li>".format({key: value})
        for key, value in settings.MANAGED_STOCKS.items()])
    mamaged_stocks = "<ul>{}</ul>".format(managed_stocks)
    content = """
    <dl>
        <dt style="font-weight: 600;">{}</dt><dd>{}</dd>
        <dt style="font-weight: 600;">{}</dt><dd>{}</dd>
    </dl>
    """.format(
        'start time', utils.get_timestamp(),
        'managed stocks', mamaged_stocks)
    send(subject, content, content_type='text/html')


def send_exception(subject, content):
    subject = '[exception]{}'.format(subject)
    send(subject, content, content_type="text/plain")
