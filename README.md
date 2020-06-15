# tradeserver

from TraderServer folder, run:

1. pip install -r requirements.txt
2. python src/server.py
3. python src/client/client.py

EMAIL

Email functionality will not work when you run, as you must authorize your GMAIL account to send emails via API.
This service only works for Justen at this point in time. For this reason, the GMAIL_USER and GMAIL_PASSWORD variables in src.client.utils/email_util.py are blanked out.

TIME OUT
Client will timeout with the server after 60 seconds of no response after sending a message
