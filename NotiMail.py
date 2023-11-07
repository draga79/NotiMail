#!/usr/bin/env python3
"""
NotiMail
Version: 0.13
Author: Stefano Marinelli <stefano@dragas.it>
License: BSD 3-Clause License

NotiMail is a script designed to monitor one or more email inbox(es) using the IMAP IDLE feature 
and send notifications via HTTP POST requests when a new email arrives. This version includes 
additional features to store processed email UIDs in a SQLite3 database and ensure they are not 
processed repeatedly.

The script uses:
- IMAP to connect to one or more email server(s)
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
- threading: to deal with multiple inboxes
- BytesParser from email.parser: For parsing raw email data.
- apprise: for apprise notifications

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
import logging
import argparse
import threading
import apprise
from email import policy
from email.parser import BytesParser

# Argument parsing to get the config file
parser = argparse.ArgumentParser(description='NotiMail Notification Service.')
parser.add_argument('-c', '--config', type=str, default='config.ini', help='Path to the configuration file.')
parser.add_argument('--print-config', action='store_true', help='Print the configuration options from config.ini')
parser.add_argument('--test-config', action='store_true', help='Test the configuration options to ensure they work properly')
parser.add_argument('--list-folders', action='store_true', help='List all IMAP folders of the configured mailboxes')
args = parser.parse_args()

# Configuration reading
config = configparser.ConfigParser()
config.read(args.config)

# Logging setup using config (or default if not set)
log_file_location = config.get('GENERAL', 'LogFileLocation', fallback='notimail.log')
logging.basicConfig(filename=log_file_location,
                    level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

class DatabaseHandler:
    def __init__(self, db_name=None):
        if db_name is None:
            db_name = config.get('GENERAL', 'DataBaseLocation', fallback="processed_emails.db")
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()
        self.update_schema_if_needed()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            email_account TEXT,
            uid TEXT,
            notified INTEGER,
            processed_date TEXT,
            PRIMARY KEY(email_account, uid)
        )''')
        self.connection.commit()

    def update_schema_if_needed(self):
        # Check if the email_account column exists
        self.cursor.execute("PRAGMA table_info(processed_emails)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'email_account' not in columns:
            # Add the email_account column and set its default value to 'unknown'
            self.cursor.execute("ALTER TABLE processed_emails ADD COLUMN email_account TEXT DEFAULT 'unknown'")
            # Update the primary key to be a composite key of email_account and uid
            self.cursor.execute("CREATE UNIQUE INDEX idx_email_account_uid ON processed_emails(email_account, uid)")
            self.connection.commit()


    def add_email(self, email_account, uid, notified):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT OR REPLACE INTO processed_emails (email_account, uid, notified, processed_date) VALUES (?, ?, ?, ?)",
                            (email_account, uid, notified, date_str))
        self.connection.commit()


    def is_email_notified(self, email_account, uid):
        self.cursor.execute("SELECT * FROM processed_emails WHERE email_account = ? AND uid = ? AND notified = 1", (email_account, uid))
        return bool(self.cursor.fetchone())

    def delete_old_emails(self, days=7):
        date_limit_str = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("DELETE FROM processed_emails WHERE processed_date < ?", (date_limit_str,))
        self.connection.commit()

    def close(self):
        self.connection.close()

class EmailProcessor:
    def __init__(self, mail, email_account):
        self.mail = mail
        self.email_account = email_account
        self.db_handler = DatabaseHandler()  # Create a new db_handler for each instance

    def fetch_unseen_emails(self):
        status, messages = self.mail.uid('search', None, "UNSEEN")
        return messages[0].split()

    def parse_email(self, raw_email):
        return BytesParser(policy=policy.default).parsebytes(raw_email)

    def process(self):
        logging.info("Fetching the latest email...")
        for message in self.fetch_unseen_emails():
            uid = message.decode('utf-8')
            if self.db_handler.is_email_notified(self.email_account, uid):  # Added email_account here
                logging.info(f"Email UID {uid} already processed and notified, skipping...")
                continue

            _, msg = self.mail.uid('fetch', message, '(BODY.PEEK[])')
            for response_part in msg:
                if isinstance(response_part, tuple):
                    email_message = self.parse_email(response_part[1])
                    sender = email_message.get('From')
                    subject = email_message.get('Subject')
                    logging.info(f"Processing Email - UID: {uid}, Sender: {sender}, Subject: {subject}")
                    notifier.send_notification(email_message.get('From'), email_message.get('Subject'))
                    self.db_handler.add_email(self.email_account, uid, 1)

        # Delete entries older than 7 days
        self.db_handler.delete_old_emails()

class NotificationProvider:
    def send_notification(self, mail_from, mail_subject):
        raise NotImplementedError("Subclasses must implement this method")

class AppriseNotificationProvider(NotificationProvider):
    def __init__(self, apprise_config):
        # Initialize the apprise object
        self.apprise = apprise.Apprise()
        # Add all the services by the configuration provided
        for service_url in apprise_config:
            self.apprise.add(service_url)

    def send_notification(self, mail_from, mail_subject):
        # Prepare the notification message
        mail_subject = mail_subject if mail_subject is not None else "No Subject"
        mail_from = mail_from if mail_from is not None else "Unknown Sender"
        message = f"{mail_from}"

        # Send the notification
        if not self.apprise.notify(title=mail_subject, body=message):
            # If notification fails, log the failure
            logging.error(f"Failed to send notification via Apprise.")
            print(f"Failed to send notification via Apprise.")


class NTFYNotificationProvider(NotificationProvider):
    def __init__(self, ntfy_data):
        #self.ntfy_urls = ntfy_urls  # Expecting a list of URLs
        self.ntfy_data = ntfy_data  # Expecting a list of (URL, Token) tuples
    
    def send_notification(self, mail_from, mail_subject):
        mail_subject = mail_subject if mail_subject is not None else "No Subject"
        mail_from = mail_from if mail_from is not None else "Unknown Sender"

        # Encode the strings in UTF-8
        encoded_from = mail_from.encode('utf-8')
        encoded_subject = mail_subject.encode('utf-8')

        for ntfy_url, token in self.ntfy_data:
            headers = {"Title": encoded_subject}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            try:
                response = requests.post(
                    ntfy_url,
                    data=encoded_from,
                    headers=headers
                )
                if response.status_code == 200:
                    print(f"Notification sent successfully to {ntfy_url}!")
                    logging.info(f"Notification sent successfully to {ntfy_url} via ntfy")
                else:
                    print(f"Failed to send notification to {ntfy_url}. Status Code:", response.status_code)
                    logging.error(f"Failed to send notification to {ntfy_url} via NTFY. Status Code: {response.status_code}")
            except requests.RequestException as e:
                print(f"An error occurred while sending notification to {ntfy_url}: {str(e)}")
                logging.error(f"An error occurred while sending notification to {ntfy_url} via NTFY: {str(e)}")
            finally:
                time.sleep(2)  # Ensure a delay between notifications



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
                logging.info(f"Notification sent successfully via Pushover")
            else:
                print(f"Failed to send notification via Pushover. Status Code:", response.status_code)
                logging.error(f"Failed to send notification to via Pushover. Status Code: {response.status_code}")
        except requests.RequestException as e:
            print(f"An error occurred while sending notification via Pushover: {str(e)}")
            logging.error(f"An error occurred while sending notification via Pushover: {str(e)}")

class GotifyNotificationProvider(NotificationProvider):
    def __init__(self, gotify_url, gotify_token):
        self.gotify_url = gotify_url
        self.gotify_token = gotify_token
    
    def send_notification(self, mail_from, mail_subject):
        mail_subject = mail_subject if mail_subject is not None else "No Subject"
        mail_from = mail_from if mail_from is not None else "Unknown Sender"
        
        message = f"From: {mail_from}\nSubject: {mail_subject}"
        
        # Include the token in the URL
        url_with_token = f"{self.gotify_url}?token={self.gotify_token}"
        
        payload = {
            "title": mail_subject,
            "message": message,
            "priority": 5  # Adjust priority as needed
        }
        
        try:
            response = requests.post(url_with_token, json=payload)
            if response.status_code == 200:
                print("Notification sent successfully via Gotify!")
                logging.info(f"Notification sent successfully via Gotify")
            else:
                print(f"Failed to send notification via Gotify. Status Code: {response.status_code}")
                logging.error(f"Failed to send notification via Gotify. Status Code: {response.status_code}")
        except requests.RequestException as e:
            print(f"An error occurred while sending notification via Gotify: {str(e)}")
            logging.error(f"An error occurred while sending notification via Gotify: {str(e)}")


class Notifier:
    def __init__(self, providers):
        self.providers = providers

    def send_notification(self, mail_from, mail_subject):
        for provider in self.providers:
            provider.send_notification(mail_from, mail_subject)


class IMAPHandler:
    def __init__(self, host, email_user, email_pass, folder="inbox"):
        self.host = host
        self.email_user = email_user
        self.email_pass = email_pass
        self.folder = folder
        self.mail = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.host, 993)
            self.mail.login(self.email_user, self.email_pass)
            self.mail.select(self.folder)
        except imaplib.IMAP4.error as e:
            print(f"Cannot connect: {str(e)}")
            notifier.send_notification("Script Error", f"Cannot connect: {str(e)}")
            raise

    def idle(self):
        print("IDLE mode started. Waiting for new email...")
        logging.info(f"[{self.email_user} - {self.folder}] IDLE mode started. Waiting for new email...")
        try:
            tag = self.mail._new_tag().decode()
            self.mail.send(f'{tag} IDLE\r\n'.encode('utf-8'))
            self.mail.readline()
            while True:
                line = self.mail.readline()
                if line:
                    print(line.decode('utf-8'))
                    if b'BYE' in line:
                        raise ConnectionAbortedError("Received BYE from server. Trying to reconnect...")
                    if b'EXISTS' in line:
                        break
            self.mail.send(b'DONE\r\n')
            self.mail.readline()
        except imaplib.IMAP4.abort as e:
            print(f"Connection closed by server: {str(e)}")
            logging.error(f"[{self.email_user}] Connection closed by server: {str(e)}")
            notifier.send_notification("Script Error", f"Connection closed by server: {str(e)}")
            raise ConnectionAbortedError("Connection lost. Trying to reconnect...")
        except socket.timeout:
            print("Socket timeout during IDLE, re-establishing connection...")
            logging.info(f"[{self.email_user}] Socket timeout during IDLE, re-establishing connection...")
            raise ConnectionAbortedError("Socket timeout. Trying to reconnect...")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            logging.info(f"[{self.email_user}] An error occurred: {str(e)}")
            notifier.send_notification("Script Error", f"An error occurred: {str(e)}")
            raise
        finally:
            print("IDLE mode stopped.")
            logging.info(f"[{self.email_user}] IDLE mode stopped.")

    def process_emails(self):
        processor = EmailProcessor(self.mail, self.email_user) # Pass the email_user (account) to the processor
        processor.process()


class MultiIMAPHandler:
    def __init__(self, accounts):
        self.accounts = accounts
        self.handlers = [IMAPHandler(account['Host'], account['EmailUser'], account['EmailPass'], account['Folder']) for account in accounts]

    def run(self):
        threads = []
        for handler in self.handlers:
            #thread = threading.Thread(target=self.monitor_account, args=(handler,))
            thread = threading.Thread(target=self.monitor_account, args=(handler,), name=handler.email_user)
            thread.daemon = True  # Set thread as daemon
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    @staticmethod
    def monitor_account(handler):
        print(f"Monitoring {handler.email_user} - Folder: {handler.folder}")
        logging.info(f"Monitoring {handler.email_user} - Folder: {handler.folder}")
        while True:  # Add a loop to keep retrying on connection loss
            try:
                handler.connect()
                while True:
                    handler.idle()
                    handler.process_emails()
            except ConnectionAbortedError as e:
                print(str(e))
                time.sleep(30)  # Sleep for 30 seconds before retrying
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                logging.error(f"An unexpected error occurred: {str(e)}")
                notifier.send_notification("Script Error", f"An unexpected error occurred: {str(e)}")
                break

def shutdown_handler(signum, frame):
    print("Shutdown signal received. Cleaning up...")
    logging.info(f"Shutdown signal received. Cleaning up...")
    try:
        for handler in MultiIMAPHandler.handlers:
            handler.mail.logout()
    except:
        pass
    print("Cleanup complete. Exiting.")
    logging.info(f"Cleanup complete. Exiting.")
    sys.exit(0)

def multi_account_main():
    accounts = []

    # Check for the old format [EMAIL] section
    if 'EMAIL' in config.sections():
        old_account = {
            'EmailUser': config['EMAIL']['EmailUser'],
            'EmailPass': config['EMAIL']['EmailPass'],
            'Host': config['EMAIL']['Host']
        }
        accounts.append(old_account)

    # Check for new format [EMAIL:accountX]
    for section in config.sections():
        if section.startswith("EMAIL:"):
            folders = config[section].get('Folders', 'inbox').split(', ')
            for folder in folders:
                account = {
                    'EmailUser': config[section]['EmailUser'],
                    'EmailPass': config[section]['EmailPass'],
                    'Host': config[section]['Host'],
                    'Folder': folder
                }
                accounts.append(account)

    providers = []

    if 'APPRISE' in config:
        apprise_urls = config['APPRISE']['urls'].split(',')  # Assuming urls is a comma-separated list in the config
        providers.append(AppriseNotificationProvider(apprise_urls))


    if 'NTFY' in config:
        ntfy_data = []
        for key in config['NTFY']:
            if key.startswith("url"):
                url = config['NTFY'][key]
                token_key = "token" + key[3:]
                token = config['NTFY'].get(token_key, None)  # Retrieve the token if it exists, else default to None
                ntfy_data.append((url, token))
        providers.append(NTFYNotificationProvider(ntfy_data))

    if 'PUSHOVER' in config:
        api_token = config['PUSHOVER']['ApiToken']
        user_key = config['PUSHOVER']['UserKey']
        providers.append(PushoverNotificationProvider(api_token, user_key))

    if 'GOTIFY' in config:
        gotify_url = config['GOTIFY']['Url']
        gotify_token = config['GOTIFY']['Token']
        providers.append(GotifyNotificationProvider(gotify_url, gotify_token))

    global notifier
    notifier = Notifier(providers)

    socket.setdefaulttimeout(480)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    print("Script started. Press Ctrl+C to stop it anytime.")
    logging.info(f"Script started. Press Ctrl+C to stop it anytime.")
    
    multi_handler = MultiIMAPHandler(accounts)
    multi_handler.run()

    print("Logging out and closing the connection...")
    logging.info(f"Logging out and closing the connection...")
    try:
        for handler in MultiIMAPHandler.handlers:
            handler.mail.logout()
    except:
        pass

def print_config():
    """
    Function to print the configuration options from config.ini
    """
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config[section].items():
            print(f"{key} = {value}")
        print()

def test_config():
    """
    Function to test the configuration options
    """
    # Test Email accounts
    for section in config.sections():
        if section.startswith("EMAIL:"):
            print(f"Testing {section}...")
            handler = IMAPHandler(config[section]['Host'], config[section]['EmailUser'], config[section]['EmailPass'])
            try:
                handler.connect()
                print(f"Connection successful for {section}")
                handler.mail.logout()  # Explicitly logging out after testing
            except Exception as e:
                print(f"Connection failed for {section}. Reason: {str(e)}")

    # Testing NTFY Notification Provider
    if 'NTFY' in config:
        print("Testing NTFY Notification Provider...")
        ntfy_data = []
        for key in config['NTFY']:
            if key.startswith("url"):
                url = config['NTFY'][key]
                token_key = "token" + key[3:]
                token = config['NTFY'].get(token_key, None)
                ntfy_data.append((url, token))
        ntfy_provider = NTFYNotificationProvider(ntfy_data)
        try:
            ntfy_provider.send_notification("Test Sender", "Test Notification from NotiMail")
            print("Test notification sent successfully via NTFY!")
        except Exception as e:
            print(f"Failed to send test notification via NTFY. Reason: {str(e)}")

    # Testing Pushover Notification Provider
    if 'PUSHOVER' in config:
        print("Testing Pushover Notification Provider...")
        pushover_provider = PushoverNotificationProvider(config['PUSHOVER']['ApiToken'], config['PUSHOVER']['UserKey'])
        try:
            pushover_provider.send_notification("Test Sender", "Test Notification from NotiMail")
            print("Test notification sent successfully via Pushover!")
        except Exception as e:
            print(f"Failed to send test notification via Pushover. Reason: {str(e)}")

    # Testing Gotify Notification Provider
    if 'GOTIFY' in config:
        print("Testing Gotify Notification Provider...")
        gotify_provider = GotifyNotificationProvider(config['GOTIFY']['Url'], config['GOTIFY']['Token'])
        try:
            gotify_provider.send_notification("Test Sender", "Test Notification from NotiMail")
            print("Test notification sent successfully via Gotify!")
        except Exception as e:
            print(f"Failed to send test notification via Gotify. Reason: {str(e)}")

    print("Testing done!")


def list_imap_folders():
    """
    Function to list all IMAP folders of the configured mailboxes
    """
    for section in config.sections():
        if section.startswith("EMAIL:"):
            print(f"Listing folders for {section}...")
            handler = IMAPHandler(config[section]['Host'], config[section]['EmailUser'], config[section]['EmailPass'])
            try:
                handler.connect()
                typ, folders = handler.mail.list()
                for folder in folders:
                    print(folder.decode())
                handler.mail.logout()  # Explicitly logging out after listing folders
            except Exception as e:
                print(f"Failed to list folders for {section}. Reason: {str(e)}")


if __name__ == "__main__":
    if args.print_config:
        print_config()
    elif args.test_config:
        test_config()
    elif args.list_folders:
        list_imap_folders()
    else:
        multi_account_main()

