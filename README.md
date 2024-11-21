# NotiMail 📧

**Version 2.0 is here!**

Stay connected without the constant drain on your battery. Introducing **NotiMail** - the future of server-side email notifications supporting multiple push providers, multiple email accounts, a web interface, Prometheus metrics, and dynamic configuration reload!

## What's New in 2.0 🚀
- **Web Interface (Flask)**: Monitor your email accounts and view logs via a web interface.
- **Prometheus Metrics**: Export detailed email processing metrics for monitoring.
- **Dynamic Configuration Reload**: Reload the configuration without restarting the script.
- **Enhanced Logging**: View logs via the web interface and manage them efficiently with rotation.
- **Backward Compatibility**: Retains all features from version 1.0 and earlier.

## Features 🌟
- **Monitors Multiple Emails on the Server**: Monitor multiple email accounts and folders with ease.
- **Processes and Notifies**: Processes new emails and sends notifications containing sender and subject.
- **Supports Multiple Push Providers**: NTFY, Gotify, Pushover, and Apprise notifications are supported.
- **Database Integration**: Uses SQLite3 to track processed emails and avoid duplicates.
- **Metrics and Monitoring**: Export metrics to Prometheus for detailed insights.
- **Thread-Safe Email Processing**: Handles multiple accounts and folders simultaneously.
- **Web Interface for Status and Logs**: Securely view account statuses, logs, and configuration via a browser.
- **Customizable Settings**: Intuitive `config.ini` for configuring multiple accounts and notifications.

## Benefits 🚀
- **Extended Battery Life**: No need to maintain persistent IMAP connections on devices.
- **Real-Time Notifications**: Stay informed instantly with push notifications.
- **Reduced Data Consumption**: Save bandwidth with server-side processing.
- **Resilient and Secure**: Built with robust error handling and secure IMAP SSL connections.

## Installation Guide 🔧

### Prerequisites:
Ensure Python 3.6 or higher is installed. For full feature support, install Flask, Apprise, and Prometheus client.

### Step-by-Step Installation:
1. **Clone or Download the Repository**:
    ```bash
    git clone https://github.com/draga79/NotiMail.git
    cd NotiMail
    ```
2. **Set Up a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate   # macOS/Linux
    .\venv\Scripts\activate # Windows
    ```
3. **Install Required Libraries**:
    Install the core dependencies:
    ```bash
    pip install requests configparser sqlite3 datetime signal logging argparse threading
    ```
    For additional features, install these optional libraries:
    - **Flask** (for the web interface):
      ```bash
      pip install flask
      ```
    - **Prometheus Client** (for metrics):
      ```bash
      pip install prometheus_client
      ```
    - **Apprise** (for additional notification services):
      ```bash
      pip install apprise
      ```

4. **Configure NotiMail**:
    Edit `config.ini` to add email accounts and notification providers.
5. **Run NotiMail**:
    ```bash
    python NotiMail.py
    ```

## Troubleshooting:
- **Missing Dependencies**: Ensure all required and optional libraries are installed.
- **Flask/Prometheus Unavailable**: Ensure the respective libraries are installed and configured.
- **Configuration Errors**: Check the syntax of `config.ini` or use the `--test-config` option.

## Changelog:
Moved to `CHANGELOG.md`.

Enjoy smarter, more efficient email notifications with **NotiMail 2.0**!

