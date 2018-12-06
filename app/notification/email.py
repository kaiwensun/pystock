from sendgrid import SendGridAPIClient
from config import settings
from sendgrid.helpers.mail import Email, Content, Mail
from app.logger import logger

__all__ = ['send', 'send_stock_order_email']


def send(from_email, to_email, subject, content, content_type="text/html"):
    sg = SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
    from_email = Email(from_email)
    to_email = Email(to_email)
    content = Content(content_type, content)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    if response.status_code != 202:
        logger.debug("Failed to send message: {}. Status code {}".format(
            content, response.status_code))


def send_stock_order_email(symbol, order_type, quantity, price, details):
    subject = "executing {} shares of {} as a {} order at {}.".format(
        order_type, symbol, quantity, price)
    send(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_TO_EMAIL,
         subject, details)
