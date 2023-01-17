"""Everything mail related"""
import datetime
import smtplib


class Mail:
    """Handler for mail services"""

    def __init__(self, server, email, password):
        self.server = server
        self.email = email
        self.password = password
        self.otp_total_time = datetime.timedelta(minutes=10)

    def send_email(self, msg, receiver):
        with smtplib.SMTP(self.server) as connection:
            connection.starttls()
            connection.login(user=self.email, password=self.password)
            connection.sendmail(
                from_addr=self.email,
                to_addrs=receiver,
                msg=msg,
            )
