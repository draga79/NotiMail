### Version 2.0

#### New Features:

-   **Web Interface and API with Flask**:
    
    -   Introduced a Flask-based web interface providing endpoints for service status (`/status`), recent logs (`/logs`), and current configuration (`/config`).
    -   The `/status` endpoint is publicly accessible and returns a simple status (OK or ERROR) indicating if all email accounts are connected and functioning properly.
    -   When accessed with a valid API key, the `/status` endpoint provides detailed information about each monitored email account.
    -   The `/logs` and `/config` endpoints require an API key for access and are secured to prevent unauthorized viewing of sensitive information.
-   **Dynamic Configuration Reload**:
    
    -   Implemented the ability to reload the configuration without restarting the service by sending a `SIGHUP` signal to the process.
    -   The service re-reads the `config.ini` file and updates its settings accordingly, allowing for dynamic adjustments.
-   **Prometheus Metrics Integration**:
    
    -   Integrated Prometheus client to expose metrics for monitoring service performance.
    -   Metrics include the total number of emails processed, notifications sent, processing time, and the number of errors encountered.
    -   Metrics are available via an HTTP endpoint, configurable in the `config.ini` file.

#### Enhancements:

-   **Optional Support for Apprise**:
    
    -   Made the support for Apprise optional. If Apprise is not installed, the program continues to function using other notification providers (NTFY, Gotify, Pushover) without errors.
    -   At startup, the program logs whether Apprise is available and adjusts functionality accordingly.
-   **Configurable Flask and Prometheus Servers**:
    
    -   Both the Flask web interface and the Prometheus metrics server can now be enabled or disabled via the configuration file.
    -   If `FlaskHost` and `FlaskPort` are not specified in `config.ini`, the Flask web interface will not start.
    -   Similarly, if `PrometheusHost` and `PrometheusPort` are not specified, the Prometheus metrics server will not start.
    -   This provides flexibility in deploying the service with only the desired features enabled.
-   **Improved Security in Web Interface**:
    
    -   Implemented an API key mechanism for accessing sensitive endpoints (`/config` and `/logs`).
    -   Sensitive information such as passwords, tokens, and URLs are redacted in the `/config` endpoint to prevent security breaches.
    -   The `/status` endpoint provides detailed account information only when accessed with a valid API key.
-   **Enhanced Logging**:
    
    -   The program now logs the availability of optional modules (Apprise, Flask, Prometheus) and indicates which features are active based on the configuration.
    -   Improved logging practices to ensure that sensitive information (passwords, tokens) is never written to the logs.

#### Changes:

-   **Refined `/status` Endpoint Behavior**:
    
    -   The `/status` endpoint now returns a simple status (OK or ERROR) when accessed without an API key, suitable for monitoring systems.
    -   When accessed with a valid API key, it provides detailed status information for each email account.
-   **Conditional Module Imports**:
    
    -   The imports for Apprise, Flask, and Prometheus are now conditional.
    -   If these libraries are not installed, the program continues to run without errors, and the associated features are automatically disabled.
    -   This allows for a more customizable setup based on available dependencies.
-   **Configuration File Updates**:
    
    -   Added new configuration options in `config.ini` under the `[GENERAL]` section:
        -   `FlaskHost` and `FlaskPort` for configuring the Flask web interface.
        -   `PrometheusHost` and `PrometheusPort` for configuring the Prometheus metrics server.
        -   `APIKey` for securing access to sensitive API endpoints.
    -   Updated the parsing logic to handle these new options and activate features accordingly.

#### Upgrade Notes:

-   **Configuration Update Required**:
    
    -   Update your `config.ini` file to include the new configuration options if you wish to use the Flask web interface and Prometheus metrics server.
    -   Add the `APIKey` under the `[GENERAL]` section to secure access to the `/config` and `/logs` endpoints.
    -   Existing configurations will continue to work, but adding the new options is necessary to enable the latest features.
-   **Library Dependencies**:
    
    -   Install the `Flask` and `prometheus_client` libraries if you intend to use the web interface and Prometheus metrics.


### Version 1.1

#### New Features:

-   **Per-Account Notification Providers**:
    
    -   Each email account can now have its own set of notification providers (Apprise, NTFY, Pushover, Gotify) configured separately from the global settings. This adds flexibility for account-specific notifications.
    -   Added a `parse_notification_providers()` function to handle both global and account-specific notification setups.

-   **Dynamic Notification Provider Configuration**:
    
    -   Ability to define notification providers globally or per account. If an account lacks its own configuration, it falls back to the global providers.
    -   Enhanced handling of configuration sections in `config.ini`, allowing for custom notifications per account.

-   **Refactoring of the `IMAPHandler` Class**:
    
    -   Now supports a `notifier` parameter to send notifications in case of errors or new messages, specific to the monitored account.

#### Enhancements:

-   **Configuration Validation**:
    
    -   Simplified validation to ensure at least one section starting with `EMAIL` exists, supporting multiple accounts seamlessly.
-   **Improved Logging & Error Handling**:
    
    -   Enhanced error notifications for each account. If a connection error occurs during idle, a notification is sent via the account-specific `notifier`.
    -   Increased granularity in notifications and logs to track specific connection errors and timeouts.
-   **Extended Support for NTFY Notifications**:
    
    -   Improved support for NTFY, allowing optional authentication tokens for each configured URL.
    -   Streamlined configuration handling for NTFY, Pushover, and Gotify to support multiple notification services.
-   **Thread-Safe Email Processing**:
    
    -   Optimized the use of `Lock` within the `MultiIMAPHandler` class to ensure thread-safe email processing without conflicts.

#### Changes:

-   **Configuration (`config.ini`)**:
    
    -   Added support for account-specific notifications (`EMAIL:account` sections).
    -   `[APPRISE]`, `[NTFY]`, `[PUSHOVER]`, and `[GOTIFY]` sections can now be defined globally or for individual accounts.
-   **Improved `test_config()` Function**:
    
    -   Now tests both global and account-specific providers to ensure all configurations are correctly set up before starting the service.
-   **Enhanced `multi_account_main()` Function**:
    
    -   Improved handling of multiple accounts with account-specific notifications. Accounts without dedicated providers will use the global notifier if available.

#### Bug Fixes

-   **IMAP Connection Stability**:
    -   Fixed an issue that caused premature disconnections from the `IDLE` mode under certain network conditions.

#### Upgrade Notes:

-   **Configuration**:
    
    -   Update your `config.ini` to include new sections for account-specific notification providers. See the new config.ini.sample for reference.
    -   Existing configurations will continue to work, but adding the new sections is recommended to take full advantage of the latest features.


### Version 1.0

#### New Features:

-   **Log Rotation**: Added support for log rotation. You can now configure log rotation based on size or time. This helps in managing log file sizes and ensures that old log files are archived.
-   **Thread-Safe Email Processing**: Improved the email processing to be thread-safe, ensuring that multiple email accounts can be processed simultaneously without conflicts.
-   **Enhanced Configuration Validation**: Added a `validate_config` function to ensure required sections are present in the `config.ini` file before proceeding.
-   **Improved Logging**: Introduced more robust logging mechanisms with options for size-based or time-based log rotation.

#### Changes:

-   **Logging Enhancements**:
    -   Introduced `RotatingFileHandler` and `TimedRotatingFileHandler` for better log management.
    -   Updated the logging configuration to use parameters from `config.ini` for log rotation.
-   **Codebase**:
    -   Refactored the `DatabaseHandler` class to use context management for better resource handling.
    -   Added a `Lock` mechanism in the `MultiIMAPHandler` class to ensure thread-safe email processing.
    -   Improved error handling and logging across the codebase to provide clearer insights and more robust operations.
-   **Configuration (`config.ini`)**:
    -   Introduced new configuration keys under `[GENERAL]`: `LogRotationType`, `LogRotationSize`, `LogRotationInterval`, and `LogBackupCount` for log rotation settings.

#### Upgrade Notes:

-   To use the new log rotation feature, update the `config.ini` file to include the new `[GENERAL]` configuration keys related to log rotation.
-   Ensure that the `config.ini` file is properly validated using the new validation mechanism.

### Version 0.13

#### New Features:

-   **Apprise Notification Support**: Introduced the `AppriseNotificationProvider` to allow for notifications through a variety of services via the Apprise library.

#### Changes:

-   Added an import statement for the `apprise` library to the script to facilitate the new notification method.
-   Updated the `multi_account_main` function to read Apprise configuration from `config.ini` and initialize the `AppriseNotificationProvider`.
-   The notification dispatch process within the script now includes the capability to use Apprise, broadening the range of supported notification services.

#### Upgrade Notes:

-   To use Apprise, ensure that the `apprise` package is installed (`pip install apprise`).
-   Update the `config.ini` file to include a new section `[APPRISE]` with the required service URLs for notifications.

### Version 0.12.1

#### Changes:

- **Moved the Changelog** to its own file
- **Introduced a new column**, email_account, to the processed_emails table. This differentiates emails based on the account they belong to, avoiding potential UID conflicts between different mailboxes.
- **Added logic** in the DatabaseHandler class to automatically check the existing schema and update it to include the email_account column if it doesn't exist.


### Version 0.12

#### New Features:

- **Multiple Folder Monitoring**: From this version onwards, NotiMail supports monitoring multiple folders for each configured email account. This allows users to, for example, monitor both the 'inbox' and 'junk' folders simultaneously. Each folder is treated as a separate connection, ensuring robust and comprehensive monitoring.
- **Configuration Validation**: Introduced command-line functions to validate the config.ini file. This ensures that your settings are correctly configured before you start the NotiMail service.
- **Notification Provider Testing**: You can now test the notification providers by sending a test notification to verify their correct setup and functioning.
- **IMAP Folder Listing**: Added a feature to list all IMAP folders of the configured mailboxes, providing better insights and facilitating precise folder monitoring.

#### Changes:

- **Configuration (`config.ini`)**: Introduced the ability to specify multiple folders for each email account using the `Folders` configuration key. If not specified, it defaults to the 'inbox' folder.
- **Logging Enhancements**: All logging and print statements now include the folder name, providing a clearer understanding of ongoing operations per folder.
- **Codebase**: Enhanced error handling, and improved logging to provide clearer insights into the application's operations.

### Version 0.11

#### New Features:

- Command-Line Flexibility: Now you can customize your config file path using -c or --config flags. The default remains 'config.ini'.
- Man Page: Introduced a man page for NotiMail, making it easier for users to understand usage and options.
- Dynamic Database Location: Configure your database path in the settings, allowing for more flexible deployments.

#### Changes:

- **Codebase:**
  - Introduced `argparse` to enable command-line arguments. You can now specify the path to a configuration file using the `-c` or `--config` option.
  - Moved the configuration reading to the top of the script to make it globally accessible.
  - Updated the logging setup to use the log file location from the config file (`LogFileLocation`). If not set, it defaults to `notimail.log`.
  - Modified the `DatabaseHandler` class to use the database location from the config file (`DataBaseLocation`). If not set, it defaults to `processed_emails.db`.
  - Improved Logging: Logs now include thread names, providing clearer insights into operations.
  - Stability Upgrades: Enhanced handling of 'BYE' responses from servers. Plus, in case of connection loss, the tool will now auto-retry to maintain smooth operations.
  - Socket Timeout: Adjusted the default socket timeout setting to further optimize responsiveness.
- **Configuration (`config.ini`):**
  - Introduced a new `[GENERAL]` section. You can specify `LogFileLocation` and `DataBaseLocation` within this section to set the desired paths for the log file and database, respectively.

### Version 0.10

- Authentication Tokens for NTFY Notifications: Enhanced the NTFYNotificationProvider to support optional authentication tokens. If a token is provided in the `config.ini` file for a specific NTFY URL, the notification request will include an "Authorization" header for authentication.

### Version 0.9

- Introduced support for monitoring multiple email accounts. Configure multiple accounts in the `config.ini` using the format `[EMAIL:account1]`, `[EMAIL:account2]`, and so on.
- Maintained compatibility with the old single `[EMAIL]` configuration for a smooth upgrade path.
