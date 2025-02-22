#!/usr/bin/env python3
"""
NotiMail
Version: 2.0
Author: Stefano Marinelli <stefano@dragas.it>
License: BSD 3-Clause License

NotiMail is a script designed to monitor one or more email inboxes using the IMAP IDLE feature
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
- threading: To deal with multiple inboxes.
- os, select: Per gestire la socket pair e interrompere le chiamate bloccanti.
- BytesParser from email.parser: For parsing raw email data.
- apprise: For Apprise notifications

Configuration:
The script reads configuration data from a file named config.ini. Ensure it is properly
configured before running the script.
"""

#!/usr/bin/env python3

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
import os
import select
from email import policy
from email.parser import BytesParser
from threading import Lock
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Creiamo una socket pair globale per gestire lo shutdown
shutdown_sock_r, shutdown_sock_w = socket.socketpair()
shutdown_sock_r.setblocking(0)
shutdown_sock_w.setblocking(0)

# Conditional import of Apprise
try:
    import apprise
    apprise_available = True
except ImportError:
    apprise_available = False

# Conditional import of Flask
try:
    from flask import Flask, jsonify, request
    flask_available = True
except ImportError:
    flask_available = False

# Conditional import of Prometheus client
try:
    from prometheus_client import start_http_server, Counter, Histogram
    from prometheus_client import Gauge, Summary
    prometheus_available = True
except ImportError:
    prometheus_available = False

# Argument parsing to get the config file path
parser = argparse.ArgumentParser(description='NotiMail Notification Service.')
parser.add_argument('-c', '--config', type=str, default='config.ini', help='Path to the configuration file.')
parser.add_argument('--print-config', action='store_true', help='Print the configuration options from config.ini')
parser.add_argument('--test-config', action='store_true', help='Test the configuration options to ensure they work properly')
parser.add_argument('--list-folders', action='store_true', help='List all IMAP folders of the configured mailboxes')
args = parser.parse_args()

# Read configuration
config = configparser.ConfigParser()
config.read(args.config)

def validate_config(config):
    required_sections = ['GENERAL']
    if not any(section.startswith('EMAIL') for section in config.sections()):
        raise ValueError("At least one EMAIL section is required.")
    # Add more validation as needed

validate_config(config)

# Logging setup using configuration (or default if not set)
log_file_location = config.get('GENERAL', 'LogFileLocation', fallback='notimail.log')
log_rotation_type = config.get('GENERAL', 'LogRotationType', fallback='size')
log_rotation_size = config.getint('GENERAL', 'LogRotationSize', fallback=10485760)  # 10MB
log_rotation_interval = config.getint('GENERAL', 'LogRotationInterval', fallback=1)  # 1 day
log_backup_count = config.getint('GENERAL', 'LogBackupCount', fallback=5)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if log_rotation_type == 'size':
    handler = RotatingFileHandler(log_file_location, maxBytes=log_rotation_size, backupCount=log_backup_count)
elif log_rotation_type == 'time':
    handler = TimedRotatingFileHandler(log_file_location, when='midnight', interval=log_rotation_interval, backupCount=log_backup_count)
else:
    raise ValueError(f"Invalid LogRotationType: {log_rotation_type}")

formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logging.info("Module availability:")
logging.info(f" - Apprise available: {apprise_available}")
logging.info(f" - Flask available: {flask_available}")
logging.info(f" - Prometheus client available: {prometheus_available}")

# Start Prometheus metrics server if available and configured
prometheus_host = config.get('GENERAL', 'PrometheusHost', fallback=None)
prometheus_port = config.getint('GENERAL', 'PrometheusPort', fallback=None)

if prometheus_available and prometheus_host and prometheus_port:
    try:
        start_http_server(prometheus_port, addr=prometheus_host)
        logging.info(f"Prometheus metrics server started on {prometheus_host}:{prometheus_port}")
        EMAILS_PROCESSED = Counter('emails_processed_total', 'Total number of emails processed')
        NOTIFICATIONS_SENT = Counter('notifications_sent_total', 'Total number of notifications sent')
        PROCESSING_TIME = Histogram('email_processing_seconds', 'Time spent processing emails')
        ERRORS = Counter('errors_total', 'Total number of errors encountered')
    except Exception as e:
        logging.error(f"Failed to start Prometheus metrics server: {str(e)}")
        prometheus_available = False
else:
    if not prometheus_available:
        logging.info("Prometheus client library is not available. Metrics will not be exposed.")
    else:
        logging.info("PrometheusHost or PrometheusPort not specified. Metrics will not be exposed.")
    class DummyMetric:
        def inc(self, amount=1):
            pass
        def time(self):
            class DummyTimer:
                def __enter__(self):
                    pass
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            return DummyTimer()
    EMAILS_PROCESSED = NOTIFICATIONS_SENT = ERRORS = DummyMetric()
    PROCESSING_TIME = DummyMetric()

# Flask web interface setup
flask_host = config.get('GENERAL', 'FlaskHost', fallback=None)
flask_port = config.getint('GENERAL', 'FlaskPort', fallback=None)

if flask_available and flask_host and flask_port:
    app = Flask(__name__)

    @app.route('/status')
    def status():
        api_key = request.args.get('api_key')
        configured_api_key = config.get('GENERAL', 'APIKey', fallback=None)
        if api_key == configured_api_key and api_key is not None:
            status_info = {'accounts': []}
            for handler in multi_handler.handlers:
                account_status = {
                    'email_user': handler.email_user,
                    'folder': handler.folder,
                    'connected': handler.mail is not None,
                    'last_check': handler.last_check.strftime("%Y-%m-%d %H:%M:%S") if handler.last_check else None
                }
                status_info['accounts'].append(account_status)
            return jsonify(status_info)
        else:
            all_connected = all(handler.mail is not None for handler in multi_handler.handlers)
            if all_connected:
                return jsonify({'status': 'OK'}), 200
            else:
                return jsonify({'status': 'ERROR'}), 500

    @app.route('/logs')
    def logs():
        api_key = request.args.get('api_key')
        configured_api_key = config.get('GENERAL', 'APIKey', fallback=None)
        if api_key == configured_api_key and api_key is not None:
            try:
                with open(log_file_location, 'r') as f:
                    logs = f.readlines()
                    last_n_lines = logs[-100:]
                return ''.join(last_n_lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}
            except Exception as e:
                return f"Failed to read log file: {str(e)}", 500
        else:
            return "Unauthorized", 401

    @app.route('/config', methods=['GET'])
    def get_config():
        api_key = request.args.get('api_key')
        configured_api_key = config.get('GENERAL', 'APIKey', fallback=None)
        if api_key == configured_api_key and api_key is not None:
            config_dict = {}
            # Sensitive keys that should be redacted (emailpass remains hidden)
            sensitive_keys = ['emailpass', 'apitoken', 'userkey', 'token', 'urls']
            for section in config.sections():
                config_dict[section] = {}
                for key, value in config[section].items():
                    if key.lower() in sensitive_keys:
                        config_dict[section][key] = 'REDACTED'
                    else:
                        config_dict[section][key] = value
            return jsonify(config_dict)
        else:
            return "Unauthorized", 401
else:
    if not flask_available:
        logging.info("Flask is not available. Web interface is disabled.")
    else:
        logging.info("FlaskHost or FlaskPort not specified. Web interface will not be started.")
    app = None

class DatabaseHandler:
    def __init__(self, db_name=None):
        if db_name is None:
            db_name = config.get('GENERAL', 'DataBaseLocation', fallback="processed_emails.db")
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()
        self.update_schema_if_needed()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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
        self.cursor.execute("PRAGMA table_info(processed_emails)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'email_account' not in columns:
            self.cursor.execute("ALTER TABLE processed_emails ADD COLUMN email_account TEXT DEFAULT 'unknown'")
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
    def __init__(self, mail, email_account, notifier):
        self.mail = mail
        self.email_account = email_account
        self.notifier = notifier

    def fetch_unseen_emails(self):
        status, messages = self.mail.uid('search', None, "UNSEEN")
        return messages[0].split()

    def parse_email(self, raw_email):
        return BytesParser(policy=policy.default).parsebytes(raw_email)

    def process(self):
        logging.info("Fetching the latest email...")
        with DatabaseHandler() as db_handler:
            for message in self.fetch_unseen_emails():
                uid = message.decode('utf-8')
                if db_handler.is_email_notified(self.email_account, uid):
                    logging.info(f"Email UID {uid} already processed and notified, skipping...")
                    continue

                _, msg = self.mail.uid('fetch', message, '(BODY.PEEK[])')
                for response_part in msg:
                    if isinstance(response_part, tuple):
                        with PROCESSING_TIME.time():
                            email_message = self.parse_email(response_part[1])
                            sender = email_message.get('From')
                            subject = email_message.get('Subject')
                            logging.info(f"Processing Email - UID: {uid}, Sender: {sender}, Subject: {subject}")
                            try:
                                self.notifier.send_notification(sender, subject)
                                NOTIFICATIONS_SENT.inc()
                            except Exception as e:
                                logging.error(f"Failed to send notification: {str(e)}")
                                ERRORS.inc()
                            db_handler.add_email(self.email_account, uid, 1)
                            EMAILS_PROCESSED.inc()

            db_handler.delete_old_emails()

class NotificationProvider:
    def send_notification(self, mail_from, mail_subject):
        raise NotImplementedError("Subclasses must implement this method")

if apprise_available:
    class AppriseNotificationProvider(NotificationProvider):
        def __init__(self, apprise_config):
            self.apprise = apprise.Apprise()
            for service_url in apprise_config:
                self.apprise.add(service_url.strip())

        def send_notification(self, mail_from, mail_subject):
            mail_subject = mail_subject if mail_subject is not None else "No Subject"
            mail_from = mail_from if mail_from is not None else "Unknown Sender"
            message = f"{mail_from}"
            if not self.apprise.notify(title=mail_subject, body=message):
                logging.error("Failed to send notification via Apprise.")
else:
    pass  # Apprise is not available; skip defining the provider

class NTFYNotificationProvider(NotificationProvider):
    def __init__(self, ntfy_data):
        self.ntfy_data = ntfy_data

    def send_notification(self, mail_from, mail_subject):
        mail_subject = mail_subject if mail_subject is not None else "No Subject"
        mail_from = mail_from if mail_from is not None else "Unknown Sender"
        encoded_from = mail_from.encode('utf-8')
        encoded_subject = mail_subject.encode('utf-8')

        for ntfy_url, token in self.ntfy_data:
            headers = {"Title": encoded_subject}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            try:
                response = requests.post(ntfy_url, data=encoded_from, headers=headers)
                if response.status_code == 200:
                    logging.info(f"Notification sent successfully to {ntfy_url} via ntfy")
                else:
                    logging.error(f"Failed to send notification to {ntfy_url} via NTFY. Status Code: {response.status_code}")
                    ERRORS.inc()
            except requests.RequestException as e:
                logging.error(f"An error occurred while sending notification to {ntfy_url} via NTFY: {str(e)}")
                ERRORS.inc()
            finally:
                time.sleep(2)

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
                logging.info("Notification sent successfully via Pushover")
            else:
                logging.error(f"Failed to send notification via Pushover. Status Code: {response.status_code}")
                ERRORS.inc()
        except requests.RequestException as e:
            logging.error(f"An error occurred while sending notification via Pushover: {str(e)}")
            ERRORS.inc()

class GotifyNotificationProvider(NotificationProvider):
    def __init__(self, gotify_url, gotify_token):
        self.gotify_url = gotify_url
        self.gotify_token = gotify_token

    def send_notification(self, mail_from, mail_subject):
        mail_subject = mail_subject if mail_subject is not None else "No Subject"
        mail_from = mail_from if mail_from is not None else "Unknown Sender"
        message = f"From: {mail_from}\nSubject: {mail_subject}"
        url_with_token = f"{self.gotify_url}?token={self.gotify_token}"
        payload = {
            "title": mail_subject,
            "message": message,
            "priority": 5
        }
        try:
            response = requests.post(url_with_token, json=payload)
            if response.status_code == 200:
                logging.info("Notification sent successfully via Gotify")
            else:
                logging.error(f"Failed to send notification via Gotify. Status Code: {response.status_code}")
                ERRORS.inc()
        except requests.RequestException as e:
            logging.error(f"An error occurred while sending notification via Gotify: {str(e)}")
            ERRORS.inc()

class Notifier:
    def __init__(self, providers):
        self.providers = providers

    def send_notification(self, mail_from, mail_subject):
        for provider in self.providers:
            provider.send_notification(mail_from, mail_subject)

class IMAPHandler:
    def __init__(self, host, email_user, email_pass, folder="inbox", notifier=None):
        self.host = host
        self.email_user = email_user
        self.email_pass = email_pass
        self.folder = folder
        self.notifier = notifier
        self.mail = None
        self.last_check = None

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.host, 993)
            self.mail.login(self.email_user, self.email_pass)
            self.mail.select(self.folder)
        except imaplib.IMAP4.error as e:
            logging.error(f"Cannot connect: {str(e)}")
            if self.notifier:
                self.notifier.send_notification("Script Error", f"Cannot connect: {str(e)}")
            raise

    def idle(self):
        logging.info(f"[{self.email_user} - {self.folder}] IDLE mode started. Waiting for new email...")
        try:
            tag = self.mail._new_tag().decode()
            self.mail.send(f'{tag} IDLE\r\n'.encode('utf-8'))
            while True:
                # Attendiamo sul socket IMAP e sulla socket pair per shutdown
                rlist, _, _ = select.select([self.mail.sock, shutdown_sock_r], [], [])
                if shutdown_sock_r in rlist:
                    # Riceviamo il dato di "wake-up" e usciamo dal loop
                    shutdown_sock_r.recv(1024)
                    break
                if self.mail.sock in rlist:
                    line = self.mail.readline()
                    if line:
                        if b'BYE' in line:
                            raise ConnectionAbortedError("Received BYE from server. Trying to reconnect...")
                        if b'EXISTS' in line:
                            break
            self.mail.send(b'DONE\r\n')
            self.mail.readline()
        except Exception as e:
            logging.error(f"[{self.email_user}] Error in idle: {str(e)}")
        finally:
            logging.info(f"[{self.email_user}] IDLE mode stopped.")
            self.last_check = datetime.datetime.now()

    def process_emails(self):
        processor = EmailProcessor(self.mail, self.email_user, self.notifier)
        processor.process()

class MultiIMAPHandler:
    def __init__(self, accounts):
        self.accounts = accounts
        self.handlers = [IMAPHandler(account['Host'], account['EmailUser'], account['EmailPass'], account['Folder'], account['Notifier']) for account in accounts]
        self.lock = Lock()

    def run(self):
        threads = []
        for handler in self.handlers:
            thread = threading.Thread(target=self.monitor_account, args=(handler,), name=handler.email_user)
            thread.daemon = True
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def monitor_account(self, handler):
        logging.info(f"Monitoring {handler.email_user} - Folder: {handler.folder}")
        while True:
            try:
                handler.connect()
                while True:
                    handler.idle()
                    with self.lock:
                        handler.process_emails()
            except ConnectionAbortedError as e:
                logging.error(str(e))
                time.sleep(30)
            except Exception as e:
                logging.error(f"An unexpected error occurred: {str(e)}")
                ERRORS.inc()
                if handler.notifier:
                    handler.notifier.send_notification("Script Error", f"An unexpected error occurred: {str(e)}")
                break

def shutdown_handler(signum, frame):
    logging.info("Shutdown signal received. Cleaning up...")
    try:
        # Inviamo un byte attraverso la socket pair per sbloccare la select
        shutdown_sock_w.send(b'\x00')
        for handler in multi_handler.handlers:
            if handler.mail is not None:
                # Forziamo la chiusura del socket IMAP per interrompere eventuali operazioni bloccanti
                try:
                    handler.mail.sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                handler.mail.logout()
    except Exception as e:
        logging.error(f"Error during logout: {str(e)}")
    logging.info("Cleanup complete. Exiting.")
    sys.exit(0)

def reload_config_handler(signum, frame):
    logging.info("Received SIGHUP signal. Reloading configuration...")
    reload_configuration()

def reload_configuration():
    global config
    config.read(args.config)
    logging.info("Configuration reloaded.")
    # Implement logic to update handlers and notifiers if necessary

def parse_notification_providers(account_name=None):
    providers = []
    # Determine which sections to read based on account_name
    if account_name:
        # Only include sections specific to this account
        sections_to_check = [section for section in config.sections() if section.endswith(f":{account_name}")]
    else:
        # Exclude account-specific sections
        sections_to_check = [section for section in config.sections() if ':' not in section]

    # NTFY providers
    ntfy_sections = [s for s in sections_to_check if s.startswith('NTFY')]
    ntfy_data = []
    for section in ntfy_sections:
        for key in config[section]:
            if key.lower().startswith("url"):
                url = config[section][key]
                index = key[3:]  # e.g., '1'
                token_key = f"Token{index}"
                token = config[section].get(token_key, None)
                ntfy_data.append((url, token))
    if ntfy_data:
        providers.append(NTFYNotificationProvider(ntfy_data))

    # Pushover provider
    pushover_sections = [s for s in sections_to_check if s.startswith('PUSHOVER')]
    for section in pushover_sections:
        if 'ApiToken' in config[section] and 'UserKey' in config[section]:
            api_token = config[section]['ApiToken']
            user_key = config[section]['UserKey']
            providers.append(PushoverNotificationProvider(api_token, user_key))
            break

    # Gotify provider
    gotify_sections = [s for s in sections_to_check if s.startswith('GOTIFY')]
    for section in gotify_sections:
        if 'Url' in config[section] and 'Token' in config[section]:
            gotify_url = config[section]['Url']
            gotify_token = config[section]['Token']
            providers.append(GotifyNotificationProvider(gotify_url, gotify_token))
            break

    # Apprise providers (only if apprise is available)
    if apprise_available:
        apprise_sections = [s for s in sections_to_check if s.startswith('APPRISE')]
        for section in apprise_sections:
            if 'urls' in config[section]:
                apprise_urls = config[section]['urls'].split(',')
                providers.append(AppriseNotificationProvider(apprise_urls))
                break

    return providers

def multi_account_main():
    accounts = []
    # Parse global notification providers
    global_providers = parse_notification_providers()
    if global_providers:
        global_notifier = Notifier(global_providers)
    else:
        global_notifier = None

    for section in config.sections():
        if section.startswith("EMAIL:"):
            account_name = section.split(":", 1)[1]
            folders = config[section].get('Folders', 'inbox').split(', ')
            for folder in folders:
                account = {
                    'EmailUser': config[section]['EmailUser'],
                    'EmailPass': config[section]['EmailPass'],
                    'Host': config[section]['Host'],
                    'Folder': folder,
                    'Notifier': None
                }
                # Parse account-specific notification providers
                account_providers = parse_notification_providers(account_name)
                if account_providers:
                    account['Notifier'] = Notifier(account_providers)
                else:
                    # Use global notifier if available
                    if global_notifier:
                        account['Notifier'] = global_notifier
                    else:
                        logging.error(f"No notification providers specified for account {section} and no global notification providers are available.")
                        print(f"Error: No notification providers specified for account {section} and no global notification providers are available.")
                        sys.exit(1)
                accounts.append(account)

    # Set socket timeout
    socket.setdefaulttimeout(480)

    # Signal handlers for graceful shutdown and config reload
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGHUP, reload_config_handler)  # For dynamic config reload

    logging.info("Script started. Press Ctrl+C to stop it at any time.")

    # Start Flask app in a separate thread if available and configured
    if flask_available and app:
        flask_thread = threading.Thread(target=run_flask_app)
        flask_thread.daemon = True
        flask_thread.start()
    else:
        if not flask_available:
            logging.info("Flask is not available. Skipping web interface.")
        else:
            logging.info("FlaskHost or FlaskPort not specified. Web interface will not be started.")

    global multi_handler
    multi_handler = MultiIMAPHandler(accounts)
    multi_handler.run()

    logging.info("Logging out and closing connections...")
    try:
        for handler in multi_handler.handlers:
            handler.mail.logout()
    except:
        pass

def print_config():
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config[section].items():
            print(f"{key} = {value}")
        print()

def test_config():
    logging.info("Testing global notification providers...")
    global_providers = parse_notification_providers()
    if global_providers:
        global_notifier = Notifier(global_providers)
        try:
            global_notifier.send_notification("Test Sender", "Test Notification from NotiMail")
            logging.info("Test notification sent successfully via global notification providers!")
        except Exception as e:
            logging.error(f"Failed to send test notification via global providers. Reason: {str(e)}")
    else:
        logging.info("No global notification providers configured.")

    for section in config.sections():
        if section.startswith("EMAIL:"):
            account_name = section.split(":", 1)[1]
            logging.info(f"Testing {section}...")
            handler = IMAPHandler(config[section]['Host'], config[section]['EmailUser'], config[section]['EmailPass'])
            try:
                handler.connect()
                logging.info(f"Connection successful for {section}")
                handler.mail.logout()
            except Exception as e:
                logging.error(f"Connection failed for {section}. Reason: {str(e)}")
            account_providers = parse_notification_providers(account_name)
            if account_providers:
                account_notifier = Notifier(account_providers)
                try:
                    account_notifier.send_notification("Test Sender", f"Test Notification from NotiMail - {section}")
                    logging.info(f"Test notification sent successfully via account-specific providers for {section}!")
                except Exception as e:
                    logging.error(f"Failed to send test notification via account-specific providers for {section}. Reason: {str(e)}")
            else:
                logging.info(f"No account-specific notification providers configured for {section}.")
    logging.info("Testing completed!")

def list_imap_folders():
    for section in config.sections():
        if section.startswith("EMAIL:"):
            logging.info(f"Listing folders for {section}...")
            handler = IMAPHandler(config[section]['Host'], config[section]['EmailUser'], config[section]['EmailPass'])
            try:
                handler.connect()
                typ, folders = handler.mail.list()
                for folder in folders:
                    print(folder.decode())
                handler.mail.logout()
            except Exception as e:
                logging.error(f"Failed to list folders for {section}. Reason: {str(e)}")

def run_flask_app():
    app.run(host=flask_host, port=flask_port)

def initial_checks():
    logging.info("Performing initial tests...")
    # Test log file write
    try:
        with open(log_file_location, 'a') as f:
            test_message = f"{datetime.datetime.now()} - Test log write from NotiMail startup.\n"
            f.write(test_message)
    except Exception as e:
        print("Error: unable to write to log file:", e)
        logging.error("Error: unable to write to log file: " + str(e))
        sys.exit(1)
    
    # Test database operations
    try:
        with DatabaseHandler() as db:
            db.add_email("test", "test", 0)
            db.cursor.execute("DELETE FROM processed_emails WHERE email_account=? AND uid=?", ("test", "test"))
            db.connection.commit()
    except Exception as e:
        print("Error: unable to write to database:", e)
        logging.error("Error: unable to write to database: " + str(e))
        sys.exit(1)
    
    # Test sending a test notification via global providers
    try:
        global_providers = parse_notification_providers()
        if not global_providers:
            print("Error: no global notification providers configured for the test.")
            logging.error("Error: no global notification providers configured for the test.")
            sys.exit(1)
        test_notifier = Notifier(global_providers)
        test_notifier.send_notification("Test Notification", "Test notification from NotiMail startup")
    except Exception as e:
        print("Error: unable to send test notification:", e)
        logging.error("Error: unable to send test notification: " + str(e))
        sys.exit(1)
    logging.info("Initial tests completed successfully.")

if __name__ == "__main__":
    if args.print_config:
        print_config()
    elif args.test_config:
        test_config()
    elif args.list_folders:
        list_imap_folders()
    else:
        initial_checks()
        multi_account_main()
