from sendgrid import SendGridAPIClient
from config import settings
from sendgrid.helpers.mail import Email, Content, Mail
from app.logger import logger
from app.shared import utils

__all__ = ['send', 'send_stock_order_email']


def send(from_email, to_email, subject, content, content_type="text/plain"):
    sg = SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
    from_email = Email(from_email)
    to_email = Email(to_email)
    subject = "[pystock] {}".format(subject)
    content = Content(content_type, content)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    if response.status_code != 202:
        logger.debug("Failed to send message: {}. Status code {}".format(
            content, response.status_code))


def send_stock_order_email(symbol, order_type, quantity, price, details):
    subject = "executing {} shares of {} as a {} order at ${}.".format(
        quantity, symbol, order_type, utils.round_price(price))
    send(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_TO_EMAIL,
         subject, details)


def send_debug_alert(content):
    subject = "debug alert"
    send(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_TO_EMAIL,
         subject, content)


def send_on_start():
    subject = "service starts"
    content = """
    <dl>
        <dt style="font-weight: 600;">{}</dt><dd>{}</dd>
        <dt style="font-weight: 600;">{}</dt><dd>{}</dd>
        <dt style="font-weight: 600;">{}</dt><dd>{}</dd>
        <dt style="font-weight: 600;">{}</dt><dd>{}</dd>
    </dl>
    """.format(
        'start time', utils.get_timestamp(),
        'allowed symbols', ', '.join(settings.ALLOWED_SYMBOLS),
        'max money per symbol', settings.MAX_MONEY_PER_SYMBOL,
        'action diff percentage', settings.ACTION_DIFF_PERCENTAGE)
    send(
        settings.SENDGRID_FROM_EMAIL,
        settings.SENDGRID_TO_EMAIL,
        subject,
        content,
        content_type='text/html')
