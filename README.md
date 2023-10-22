# NotiMail 📧

**Version 0.10 is here, featuring support for ntfy auth tokens!**

**Development is ongoing, and the project is in the early alpha stage - things may break!**

Stay connected without the constant drain on your battery. Introducing **NotiMail** - the future of server-side email notifications supporting multiple push providers and multiple email accounts!

Mobile devices often use IMAP IDLE, maintaining a persistent connection to ensure real-time email notifications. Such continuous connections rapidly consume battery power. The modern era demanded a smarter, more energy-efficient solution. Meet NotiMail.

## Features 🌟

-   **Monitors Multiple Emails on the Server**: With version 0.9, NotiMail can now monitor multiple email accounts. Ensure you never miss an email regardless of which account it's sent to.
    
-   **Processes and Notifies**: Once a new email is detected, NotiMail swiftly processes its details.
    
-   **Leverages Multiple Push Providers for Alerts**: Rather than having your device always on alert, NotiMail sends notifications via multiple push providers, ensuring you're promptly informed.

-   **Database Integration**: NotiMail uses an SQLite3 database to store and manage processed email UIDs, preventing repeated processing.
    
-   **Built for Resilience**: With connectivity hiccups in mind, NotiMail ensures you're always the first to know.

-   **Multiple And Different Push providers supported**: You can use one or more of the supported Push providers - all support authentication, which currently include ntfy, Gotify and Pushover.
    

## Benefits 🚀

-   **Extended Battery Life**: Experience a noticeable improvement in your device's battery lifespan.
    
-   **Swift Notifications**: Using one of the supported push providers, NotiMail provides real-time notifications without delay.
    
-   **Reduced Data Consumption**: With notifications being the primary data exchange, you can save on unnecessary data usage.
    
-   **Always in the Loop**: Whether it's a new email or a server glitch, NotiMail and push notifications guarantee you're always informed.
    

## Implementation Details 🔧

-   **Efficient Operation**: Crafted for server-side operations, NotiMail guarantees a smooth, lightweight experience.
    
-   **Customizable Settings**: Through an intuitive `config.ini`, customize NotiMail to fit your needs. With the new 0.9 version, configure multiple email accounts for monitoring.
    
-   **Dependable Error Handling**: With robust mechanisms, NotiMail ensures you're notified of any hitches or anomalies.
    
-   **Safety First**: Employing secure IMAP SSL encryption, your email data is always safe.
    

----------

Contributions, feedback, and stars ⭐ are always welcome.


## NotiMail Installation Walkthrough

----------

### Prerequisites:

Ensure you have Python installed on your machine. NotiMail is written in Python, and you'd need it to run the script. If you haven't already installed Python, download it from the [official website](https://www.python.org/downloads/) or your OS package manager.

----------

### Step-by-Step Installation:

**1. Clone or Download NotiMail:**

If you've hosted `NotiMail` on a platform like GitHub, provide the link and the command. For this example, I'll use a placeholder link:

bash

`git clone https://github.com/draga79/NotiMail.git` 

If you're not using version control, ensure users have a link to download the `.zip` or `.tar.gz` of the project and then extract it.

**2. Navigate to the NotiMail Directory:**

bash

`cd NotiMail` 

**3. Set Up a Virtual Environment (Optional but Recommended):**

A virtual environment ensures that the dependencies for the project don't interfere with your other Python projects or system libraries.

bash

`python -m venv notimail-env` 

Activate the virtual environment:

-   On macOS and Linux:
    
    bash
    

-   `source notimail-env/bin/activate` 
    
-   On Windows:
    
    bash
    

-   `.\notimail-env\Scripts\activate` 
    

**4. Install the Required Libraries:**

Install the necessary Python libraries using `pip`, for example:

bash

`pip install requests` 

**5. Configure NotiMail:**

Open the `config.ini` file in a text editor. From version 0.9, you can configure multiple email accounts for monitoring by adding sections like `[EMAIL:account1]`, `[EMAIL:account2]`, etc. If you're upgrading from an earlier version, your old single `[EMAIL]` configuration is still supported. Also, update the configuration for one (or more) of the supported push providers.

**6. Run NotiMail:**

bash

`python NotiMail.py` 

----------

### Troubleshooting:

1.  **Python Not Found**: Ensure Python is installed and added to your system's PATH.
    
3.  **Dependencies Missing**: If the script raises an error about missing modules, ensure you've activated your virtual environment and installed all necessary libraries.
    

----------

With that, you should have NotiMail up and running on your system! Enjoy a more efficient email notification experience.

### Changelog:

-   **Version 0.11 Alpha - not yet released:**

New Features:

-   **Configurable Paths:** Introduced the ability to configure the location of the log file and the SQLite database from the configuration file.
-   **Flexible Configuration:** Added support to specify a custom configuration file when running the script.

Changes:

-   **Codebase:**
    -   Introduced `argparse` to enable command-line arguments. Users can now specify the path to a configuration file using `-c` or `--config` option.
    -   Moved the config reading to the top of the script to make it globally accessible.
    -   Updated the logging setup to fetch the log file location from the config file (`LogFileLocation`). If not set, it defaults to `notimail.log`.
    -   Modified the `DatabaseHandler` class to fetch the database location from the config file (`DataBaseLocation`). If not set, it defaults to `processed_emails.db`.
-   **Configuration (`config.ini`):**
    -   Introduced a new `[GENERAL]` section. Users can specify `LogFileLocation` and `DataBaseLocation` within this section to set the desired paths for the log file and database, respectively.

-   **Version 0.10:**
    -   Authentication Tokens for NTFY Notifications: Enhanced the NTFYNotificationProvider to support optional authentication tokens. If a token is provided in the config.ini file for a specific NTFY URL, the notification request will include an "Authorization" header for authentication.

-   **Version 0.9:**
    -   Introduced support for monitoring multiple email accounts. Configure multiple accounts in the `config.ini` using the format `[EMAIL:account1]`, `[EMAIL:account2]`, and so on.
    -   Maintained compatibility with the old single `[EMAIL]` configuration for a smooth upgrade path.
