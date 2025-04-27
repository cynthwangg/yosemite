# Yosemite Availability Checker - Setup Instructions

This document provides detailed instructions for setting up and running the Yosemite Availability Checker, which automatically checks for accommodation availability at Yosemite National Park.

## What This Script Does

- Checks availability for specific dates (May 23-26, 2025 by default)
- Runs automatically every 15 minutes
- Sends email alerts when availability is found
- Sends daily recap emails even when no availability is found
- Saves screenshots of the calendar for verification

## Requirements

- Python 3.6 or newer
- Chrome or Chromium browser
- Internet connection
- Computer that can stay on while checking (or a server)
- Gmail account for sending notifications (or another email provider)

## Setup Instructions

### Step 1: Create Project Directory

```bash
# Create a new directory for the project
mkdir yosemite_checker
cd yosemite_checker
```

### Step 2: Copy Files

Place the following files in the project directory:
- `calendar_check.py` (the main script)
- `requirements.txt` (list of required Python packages)

### Step 3: Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Step 4: Create Results Directory

```bash
# Create directory for saving results
mkdir results
```

### Step 5: Configure Email Settings

Edit `calendar_check.py` and modify the following variables:

```python
# Email settings for notifications
EMAIL_ENABLED = True
EMAIL_SENDER = "your_email@gmail.com"  # The email address sending notifications
EMAIL_PASSWORD = "your_app_password"    # App password (not your regular password)
EMAIL_RECIPIENT = "recipient@email.com" # Where to send notifications
EMAIL_SMTP_SERVER = "smtp.gmail.com"    # Or your email provider's SMTP server
EMAIL_SMTP_PORT = 587                   # Standard TLS port
```

**Important Note for Gmail Users**: You need to create an "App Password" for this script.
1. Go to your Google Account
2. Navigate to Security
3. Under "Signing in to Google," select "App passwords"
4. Generate a new app password for "Mail" and use it in the script

### Step 6: Test the Script

Run the script once manually to make sure everything works:

```bash
# Make sure your virtual environment is activated
python calendar_check.py
```

You should see output showing the script checking availability, and you should receive a test email.

### Step 7: Set Up Automated Running

#### For macOS/Linux (using cron):

```bash
# Open the cron configuration
crontab -e

# Add this line (replace /path/to/yosemite_checker with your actual path)
*/15 * * * * cd /path/to/yosemite_checker && ./venv/bin/python3 calendar_check.py >> check_log.txt 2>&1
```

#### For Windows (using Task Scheduler):

1. Open Task Scheduler
2. Create a new Basic Task
3. Set the trigger to run every 15 minutes
4. Set the action to start a program
5. Program/script: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `C:\path\to\yosemite_checker\calendar_check.py`
7. Start in: `C:\path\to\yosemite_checker`

### Step 8: Granting Permissions (macOS only)

On macOS, you may need to give cron and Terminal full disk access:
1. Go to System Preferences > Security & Privacy > Privacy tab
2. Select Full Disk Access from the left sidebar
3. Click the lock icon and enter your password
4. Add `/usr/sbin/cron` and Terminal app to the list

## Understanding the Output

### Log Files

- `check_log.txt`: Contains detailed logs of each run
- `results/` directory: Contains screenshots and HTML captures of the calendar

### Email Notifications

- **Availability alerts**: Sent immediately when dates become available
- **Daily recap emails**: Sent once per day summarizing the checks

## Troubleshooting Common Issues

### Script Doesn't Run

- Check if Python and Chrome are installed
- Verify your virtual environment is set up correctly
- Make sure the script has permission to access the internet

### Email Notifications Not Working

- Verify your email settings in the script
- For Gmail, make sure you're using an App Password, not your regular password
- Check if your email provider blocks automated emails

### Browser/Selenium Issues

- Update Chrome to the latest version
- Try running in non-headless mode for debugging (comment out the headless option)

## Modifying Target Dates

If you want to check for different dates, edit these values in `calendar_check.py`:

```python
# Target dates we're looking for
TARGET_DATES = {
    "check_in": {
        "date": "2025-05-23",
        "display": "May 23, 2025 (Friday)"
    },
    "check_out": {
        "date": "2025-05-26", 
        "display": "May 26, 2025 (Monday)"
    }
}
```

## Questions or Issues?

If you encounter any problems with the script, please:
1. Check the log file for error messages
2. Make sure all requirements are installed
3. Try running the script manually to see if it works 