"""
NotiMail
Version: 0.8
Author: Stefano Marinelli
License: BSD 3-Clause License

NotiMail is a script designed to monitor an email inbox using the IMAP IDLE feature,
and send notifications via HTTP POST requests when a new email arrives.

The script uses IMAP to connect to an email server, enters IDLE mode to wait for new emails,
and sends a notification containing the sender and subject of the new email upon receipt.

Python Dependencies:
- imaplib: For handling IMAP connections.
- email: For parsing received emails.
- requests: For sending HTTP POST notifications.
- configparser: For reading the configuration from a file.
- time, socket: For handling timeouts and delays.

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
from email import policy
from email.parser import BytesParser


class EmailProcessor:
    def __init__(self, mail):
        self.mail = mail
        self.processed_emails = set()

    def fetch_unseen_emails(self):
        status, messages = self.mail.uid('search', None, "UNSEEN")
        return messages[0].split()

    def parse_email(self, raw_email):
        return BytesParser(policy=policy.default).parsebytes(raw_email)

    def process(self):
        print("Fetching the latest email...")
        for message in self.fetch_unseen_emails():
            if message in self.processed_emails:
                print(f"Email UID {message} already processed, skipping...")
                continue

            _, msg = self.mail.uid('fetch', message, '(BODY.PEEK[])')
            for response_part in msg:
                if isinstance(response_part, tuple):
                    email_message = self.parse_email(response_part[1])
                    print('From:', email_message.get('From'))
                    print('Subject:', email_message.get('Subject'))
                    print('Body:', email_message.get_payload())
                    print('------')
                    Notifier.send_notification(email_message.get('From'), email_message.get('Subject'))
                    self.processed_emails.add(message)


class Notifier:
    @staticmethod
    def send_notification(mail_from, mail_subject):
        try:
            ntfy_url = config['NTFY']['NtfyURL']
            response = requests.post(
                ntfy_url,
                data=mail_from.encode(encoding='utf-8'),
                headers={"Title": mail_subject}
            )
            if response.status_code == 200:
                print("Notification sent successfully!")
                time.sleep(5)  # Ensure a delay between notifications
            else:
                print("Failed to send notification. Status Code:", response.status_code)
        except requests.RequestException as e:
            print(f"An error occurred: {str(e)}")


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
            Notifier.send_notification("Script Error", f"Cannot connect: {str(e)}")
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
            Notifier.send_notification("Script Error", f"Connection closed by server: {str(e)}")
            raise ConnectionAbortedError("Connection lost. Trying to reconnect...")
        except socket.timeout:
            print("Socket timeout during IDLE, re-establishing connection...")
            raise ConnectionAbortedError("Socket timeout. Trying to reconnect...")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            Notifier.send_notification("Script Error", f"An error occurred: {str(e)}")
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

# Set a global timeout for all socket operations
socket.setdefaulttimeout(600)  # e.g., 600 seconds or 10 minutes

print("Script started. Press Ctrl+C to stop it anytime.")
try:
    handler = IMAPHandler(host, email_user, email_pass)
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
            Notifier.send_notification("Script Error", f"An unexpected error occurred: {str(e)}")
except KeyboardInterrupt:
    print("User pressed Ctrl+C, exiting...")
finally:
    print("Logging out and closing the connection...")
    try:
        handler.mail.logout()
    except:
        pass

