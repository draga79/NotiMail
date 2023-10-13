"""
NotiMail
Version: 0.8 - Alpha
Author: Stefano Marinelli <stefano@dragas.it>
License: BSD 3-Clause License

NotiMail is a script designed to monitor an email inbox using the IMAP IDLE feature 
and send notifications via HTTP POST requests when a new email arrives. This version includes 
additional features to store processed email UIDs in a SQLite3 database and ensure they are not 
processed repeatedly.

The script uses:
- IMAP to connect to an email server
- IDLE mode to wait for new emails
- Sends a notification containing the sender and subject of the new email upon receipt
- Maintains a SQLite database to keep track of processed emails

Python Dependencies:
- imaplib: For handling IMAP connections.
- email: For parsing received emails.
- requests: For sending HTTP POST notifications.
- configparser: For reading the configuration from a file.
- time, socket: For handling timeouts and delays.
- sqlite3: For database operations.
- datetime: For date and time operations.
- signal, sys: For handling script shutdown and signals.
- BytesParser from email.parser: For parsing raw email data.

Configuration:
The script reads configuration data from a file named config.ini. Ensure it is properly 
configured before running the script.

BSD 3-Clause License:

Copyright (c) 2023, Stefano Marinelli
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""

import imaplib
import email
import requests
import configparser
import time
import socket
import sqlite3
import datetime
import signal
import sys
from email import policy
from email.parser import BytesParser

class DatabaseHandler:
    def __init__(self, db_name="processed_emails.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            uid TEXT PRIMARY KEY,
            notified INTEGER,
            processed_date TEXT
        )''')
        self.connection.commit()

    def add_email(self, uid, notified):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO processed_emails (uid, notified, processed_date) VALUES (?, ?, ?)",
                            (uid, notified, date_str))
        self.connection.commit()

    def is_email_notified(self, uid):
        self.cursor.execute("SELECT * FROM processed_emails WHERE uid = ? AND notified = 1", (uid,))
        return bool(self.cursor.fetchone())

    def delete_old_emails(self, days=7):
        date_limit_str = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("DELETE FROM processed_emails WHERE processed_date < ?", (date_limit_str,))
        self.connection.commit()

    def close(self):
        self.connection.close()


class EmailProcessor:
    def __init__(self, mail):
        self.mail = mail
        self.db_handler = DatabaseHandler()

    def fetch_unseen_emails(self):
        status, messages = self.mail.uid('search', None, "UNSEEN")
        return messages[0].split()

    def parse_email(self, raw_email):
        return BytesParser(policy=policy.default).parsebytes(raw_email)

    def process(self):
        print("Fetching the latest email...")
        for message in self.fetch_unseen_emails():
            uid = message.decode('utf-8')
            if self.db_handler.is_email_notified(uid):
                print(f"Email UID {uid} already processed and notified, skipping...")
                continue

            _, msg = self.mail.uid('fetch', message, '(BODY.PEEK[])')
            for response_part in msg:
                if isinstance(response_part, tuple):
                    email_message = self.parse_email(response_part[1])
                    print('From:', email_message.get('From'))
                    print('Subject:', email_message.get('Subject'))
                    print('Body:', email_message.get_payload())
                    print('------')
                    notifier.send_notification(email_message.get('From'), email_message.get('Subject'))
                    # Add UID to database to ensure it is not processed in future runs
                    self.db_handler.add_email(uid, 1)

        # Delete entries older than 7 days
        self.db_handler.delete_old_emails()

class NotificationProvider:
    def send_notification(self, mail_from, mail_subject):
        raise NotImplementedError("Subclasses must implement this method")

class NTFYNotificationProvider(NotificationProvider):
    def __init__(self, ntfy_urls):
        self.ntfy_urls = ntfy_urls  # Expecting a list of URLs
    
    def send_notification(self, mail_from, mail_subject):
        mail_subject = mail_subject if mail_subject is not None else "No Subject"
        mail_from = mail_from if mail_from is not None else "Unknown Sender"
        sanitized_subject = mail_subject.encode('latin-1', errors='replace').decode('latin-1')
        sanitized_from = mail_from.encode('latin-1', errors='replace').decode('latin-1')

        for ntfy_url in self.ntfy_urls:
            try:
                response = requests.post(
                    ntfy_url,
                    data=sanitized_from.encode(encoding='utf-8'),
                    headers={"Title": sanitized_subject}
                )
                if response.status_code == 200:
                    print(f"Notification sent successfully to {ntfy_url}!")
                else:
                    print(f"Failed to send notification to {ntfy_url}. Status Code:", response.status_code)
            except requests.RequestException as e:
                print(f"An error occurred while sending notification to {ntfy_url}: {str(e)}")
            finally:
                time.sleep(5)  # Ensure a delay between notifications

class PushoverNotificationProvider(NotificationProvider):
    def __init__(self, api_token, user_key):
        self.api_token = api_token
        self.user_key = user_key
        self.pushover_url = "https://api.pushover.net/1/messages.json"
    
    def send_notification(self, mail_from, mail_subject):
        mail_subject = mail_subject if mail_subject is not None else "No Subject"
        mail_from = mail_from if mail_from is not None else "Unknown Sender"

        message = f"From: {mail_from}\nSubject: {mail_subject}"

        data = {
            "token": self.api_token,
            "user": self.user_key,
            "message": message
        }

        try:
            response = requests.post(self.pushover_url, data=data)
            if response.status_code == 200:
                print("Notification sent successfully via Pushover!")
            else:
                print(f"Failed to send notification via Pushover. Status Code:", response.status_code)
        except requests.RequestException as e:
            print(f"An error occurred while sending notification via Pushover: {str(e)}")

class Notifier:
    def __init__(self, providers):
        self.providers = providers

    def send_notification(self, mail_from, mail_subject):
        for provider in self.providers:
            provider.send_notification(mail_from, mail_subject)


class IMAPHandler:
    def __init__(self, host, email_user, email_pass):
        self.host = host
        self.email_user = email_user
        self.email_pass = email_pass
        self.mail = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.host, 993)
            self.mail.login(self.email_user, self.email_pass)
            self.mail.select('inbox')
        except imaplib.IMAP4.error as e:
            print(f"Cannot connect: {str(e)}")
            notifier.send_notification("Script Error", f"Cannot connect: {str(e)}")
            raise

    def idle(self):
        print("IDLE mode started. Waiting for new email...")
        try:
            tag = self.mail._new_tag().decode()
            self.mail.send(f'{tag} IDLE\r\n'.encode('utf-8'))
            self.mail.readline()
            while True:
                line = self.mail.readline()
                if line:
                    print(line.decode('utf-8'))
                    if b'EXISTS' in line:
                        break
            self.mail.send(b'DONE\r\n')
            self.mail.readline()
        except imaplib.IMAP4.abort as e:
            print(f"Connection closed by server: {str(e)}")
            notifier.send_notification("Script Error", f"Connection closed by server: {str(e)}")
            raise ConnectionAbortedError("Connection lost. Trying to reconnect...")
        except socket.timeout:
            print("Socket timeout during IDLE, re-establishing connection...")
            raise ConnectionAbortedError("Socket timeout. Trying to reconnect...")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            notifier.send_notification("Script Error", f"An error occurred: {str(e)}")
            raise
        finally:
            print("IDLE mode stopped.")

    def process_emails(self):
        processor = EmailProcessor(self.mail)
        processor.process()


# Load configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

email_user = config['EMAIL']['EmailUser']
email_pass = config['EMAIL']['EmailPass']
host = config['EMAIL']['Host']

# Example: Creating notification providers based on configuration
providers = []

if 'NTFY' in config:
    ntfy_urls = [config['NTFY'][url_key] for url_key in config['NTFY']]
    providers.append(NTFYNotificationProvider(ntfy_urls))

if 'PUSHOVER' in config:
    api_token = config['PUSHOVER']['ApiToken']
    user_key = config['PUSHOVER']['UserKey']
    providers.append(PushoverNotificationProvider(api_token, user_key))

# Initialize Notifier with providers
notifier = Notifier(providers)


# Set a global timeout for all socket operations
socket.setdefaulttimeout(600)  # e.g., 600 seconds or 10 minutes

def shutdown_handler(signum, frame):
    print("Shutdown signal received. Cleaning up...")
    try:
        handler.mail.logout()
    except:
        pass
    processor.db_handler.close()
    print("Cleanup complete. Exiting.")
    sys.exit(0)

# Register the signal handlers
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

print("Script started. Press Ctrl+C to stop it anytime.")
handler = IMAPHandler(host, email_user, email_pass)
processor = EmailProcessor(None)  # Creating an instance for graceful shutdown handling

try:
    while True:
        try:
            handler.connect()
            while True:
                handler.idle()
                handler.process_emails()
        except ConnectionAbortedError as e:
            print(str(e))
            time.sleep(30)  # wait for 30 seconds before trying to reconnect
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            notifier.send_notification("Script Error", f"An unexpected error occurred: {str(e)}")
finally:
    print("Logging out and closing the connection...")
    try:
        handler.mail.logout()
    except:
        pass
    processor.db_handler.close()

