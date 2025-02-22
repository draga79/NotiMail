# NotiMail 📧

**Version 2.0 is here!**

Stay connected without constantly draining your battery. Introducing **NotiMail** – the future of server-side email notifications that supports multiple push providers, multiple email accounts, a web interface for monitoring, Prometheus metrics, dynamic configuration reload, and robust startup checks!

## What's New in 2.0 🚀
- **Web Interface (Flask)**: Securely monitor your email accounts, view real-time status, logs, and configuration via a browser.
- **Prometheus Metrics**: Export detailed email processing metrics (emails processed, notifications sent, processing time, errors) for monitoring and alerting.
- **Dynamic Configuration Reload**: Reload your configuration on the fly (via SIGHUP) without needing to restart the script.
- **Enhanced Logging**: Efficient log management with rotation and an integrated web interface to view recent logs.
- **Robust Startup Checks**: Immediate tests on log file writing, database operations, and test notifications with errors printed to both stdout and log.
- **Backward Compatibility**: All features from previous versions are still supported.

## Features 🌟
- **Multi-Account Monitoring**: Monitor multiple email accounts and folders seamlessly.
- **Email Processing & Notification**: Automatically process new emails and send notifications containing the sender and subject.
- **Multiple Push Providers**: Support for NTFY, Gotify, Pushover, and Apprise (if installed) notifications.
- **Database Integration**: Uses SQLite3 to track processed emails and avoid duplicate notifications.
- **Metrics & Monitoring**: Export valuable metrics to Prometheus for detailed insights.
- **Thread-Safe Processing**: Handles multiple accounts and folders concurrently using threading.
- **Web Interface**: Provides secure endpoints to check account status, view logs, and inspect configuration.
- **Dynamic Config Reload**: Change settings on the fly without stopping the service.
- **CLI Options**: Options like `--print-config`, `--test-config`, and `--list-folders` help verify and troubleshoot your setup.
- **Startup Error Reporting**: Startup errors are logged and also printed to stdout for immediate feedback.

## Benefits 🚀
- **Extended Battery Life**: Offload persistent IMAP connections to a server.
- **Real-Time Notifications**: Get instant push notifications when new emails arrive.
- **Reduced Data Consumption**: Process emails server-side, saving bandwidth on client devices.
- **Resilient & Secure**: Built with robust error handling, secure IMAP SSL connections, and immediate startup tests.

## Installation Guide 🔧

### Prerequisites
- **Python 3.6 or higher** is required.
- For full feature support, install optional libraries such as **Flask**, **Prometheus Client**, and **Apprise**.

### Step-by-Step Installation

1. **Clone or Download the Repository**:
    ```bash
    git clone https://github.com/draga79/NotiMail.git
    cd NotiMail
    ```

2. **Install Required Libraries**:  
   Install the core dependencies. For example, on FreeBSD you might run:
    ```bash
    pkg install python311 py311-sqlite3 py311-requests py311-configparser py311-datetime py311-argparse
    ```
   For additional features, install these optional libraries:
    - **Flask** (for the web interface):
      ```bash
      pkg install py311-flask
      ```
    - **Prometheus Client** (for metrics):
      ```bash
      pkg install py311-prometheus-client
      ```
    - **Apprise** (for extra notification services):
      ```bash
      pip install py311-apprise
      ```

3. **Configure NotiMail**:  
   Edit the `config.ini` file to add your email accounts, folders, and notification provider settings. The configuration also allows you to set up the web interface (Flask), Prometheus metrics, and logging options.

4. **Run NotiMail**:
    ```bash
    python3.11 NotiMail.py
    ```

## Usage

- **Web Interface**:  
  If Flask is installed and configured in your `config.ini` (with `FlaskHost` and `FlaskPort`), the web interface will be available at:
  - `/status` – Get a detailed status of monitored email accounts (requires API key). Without an API key, the /status endpoint returns a simple status (OK or ERROR) indicating if all email accounts are connected and functioning properly.
  - `/logs` – View the last 100 lines of logs (requires API key).
  - `/config` – Display the current configuration with sensitive keys redacted (requires API key).

- **Prometheus Metrics**:  
  If the Prometheus client is installed and configured (set `PrometheusHost` and `PrometheusPort` in `config.ini`), NotiMail will export metrics such as:
  - Total emails processed
  - Total notifications sent
  - Email processing time
  - Total errors encountered

- **Dynamic Configuration Reload**:  
  Send a SIGHUP signal to the running process to reload the configuration without restarting:
    ```bash
    kill -SIGHUP <process_id>
    ```

- **CLI Options**:  
  - `--print-config`: Print the current configuration.
  - `--test-config`: Run tests for connectivity and notification providers.
  - `--list-folders`: List all available IMAP folders for each email account.

## Troubleshooting

- **Missing Dependencies**:  
  Ensure that all required and optional libraries are installed.
  
- **Flask/Prometheus Unavailable**:  
  Verify that Flask and Prometheus client libraries are installed and properly configured in `config.ini`.

- **Configuration Errors**:  
  Double-check the syntax of `config.ini` or use the `--test-config` option to validate your setup.

- **Startup Errors**:  
  Errors during startup (log file, database, or test notification) will be printed to both stdout and the log. Address these immediately as the program will exit if they occur.

## Changelog
For a detailed list of changes, please refer to the [CHANGELOG.md](CHANGELOG.md).

---

Enjoy smarter, more efficient email notifications with **NotiMail 2.0**!
