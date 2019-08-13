import smtplib
import ssl
import logging
import time
from typing import List, NamedTuple

LOGGER = logging.getLogger(__name__)


class UndeliveredMessage(NamedTuple):
    to_addrs: str
    msg: str


class GmailClient:
    def __init__(self, email_address, password):
        self._email_address = email_address
        self._password = password

        # store a connection to the server, initialize lazily
        self._server = None

        # store a list of messages that aren't able to be delivered
        self.undelivered_messages: List[UndeliveredMessage] = []

    def _connect_to_server(self):
        # create and secure server connection
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls(context=ssl.create_default_context())

        # log in to your email
        server.login(self._email_address, self._password)
        self._server = server

    def send_mail(self, to_addrs: str, msg: str):
        if self._server is None:
            self._connect_to_server()

        try:
            self._server.sendmail(from_addr=self._email_address, to_addrs=to_addrs, msg=msg)
            LOGGER.info(f"Email sent to {to_addrs}.")

            # sleep so as not to pass the gmail send limit when used iteratively
            # not doing this will result in a 421, 4.7.0 error from the server
            time.sleep(1)

        except smtplib.SMTPException as e:
            LOGGER.error(f"Email to {to_addrs} failed to send due to an error.")
            LOGGER.error(e)
            self.undelivered_messages.append(UndeliveredMessage(to_addrs, msg))

            # pause, then reconnect to server
            time.sleep(30)
            self._connect_to_server()
