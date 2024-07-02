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
