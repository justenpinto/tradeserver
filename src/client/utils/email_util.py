import smtplib
import traceback

from email.mime.text import MIMEText

GMAIL_USER = ''
GMAIL_PASSWORD = ''


def send_email(subject, body=None, to=None):
    recipients = []
    if to:
        if isinstance(to, list):
            recipients.extend(to)
        elif isinstance(to, str):
            recipients.append(to)
        else:
            raise Exception("Unknown object type for recipients: %s" % type(to))
    else:
        recipients = ['justen.pinto@gmail.com']
    msg = MIMEText(body, 'plain')
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = ', '.join(recipients)
    try:
        email_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        email_server.ehlo()
        email_server.login(GMAIL_USER, GMAIL_PASSWORD)
        email_server.sendmail(GMAIL_USER, recipients, msg.as_string())
    except:
        error_message = traceback.format_exc()
        print(error_message)
