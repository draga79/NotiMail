# NotiMail 📧

Stay connected without the constant drain on your battery. Introducing **NotiMail** - the future of server-side email notifications using the renowned `ntfy` service!

Mobile devices often use IMAP IDLE, maintaining a persistent connection to ensure real-time email notifications. Such continuous connections rapidly consume battery power. The modern era demanded a smarter, more energy-efficient solution. Meet NotiMail.

## Features 🌟

-   **Monitors Emails on the Server**: NotiMail checks for new, unseen emails without needing a constant client connection.
    
-   **Processes and Notifies**: Once a new email is detected, NotiMail swiftly processes its details.
    
-   **Leverages 'ntfy' for Alerts**: Rather than having your device always on alert, NotiMail sends notifications via the `ntfy` service, ensuring you're promptly informed.

-   **Database Integration**: NotiMail uses an SQLite3 database to store and manage processed email UIDs, preventing repeated processing.
    
-   **Built for Resilience**: With connectivity hiccups in mind, NotiMail ensures you're always the first to know.
    

## Benefits 🚀

-   **Extended Battery Life**: Experience a noticeable improvement in your device's battery lifespan.
    
-   **Swift Notifications**: With the `ntfy` service, NotiMail provides real-time notifications without delay.
    
-   **Reduced Data Consumption**: With notifications being the primary data exchange, you can save on unnecessary data usage.
    
-   **Always in the Loop**: Whether it's a new email or a server glitch, NotiMail and `ntfy` guarantee you're always informed.
    

## Implementation Details 🔧

-   **Efficient Operation**: Crafted for server-side operations, NotiMail guarantees a smooth, lightweight experience.
    
-   **Customizable Settings**: Through an intuitive `config.ini`, customize NotiMail to fit your needs.
    
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

Open the `config.ini` file in a text editor. Update the `[EMAIL]` section with your email credentials and host, and the `[NTFY]` section with the appropriate `NtfyURL`. For more information about ntfy and its configuration, please read the [official website](https://docs.ntfy.sh/)

**6. Run NotiMail:**

bash

`python NotiMail.py` 

----------

### Troubleshooting:

1.  **Python Not Found**: Ensure Python is installed and added to your system's PATH.
    
3.  **Dependencies Missing**: If the script raises an error about missing modules, ensure you've activated your virtual environment and installed all necessary libraries.
    

----------

With that, you should have NotiMail up and running on your system! Enjoy a more efficient email notification experience.


