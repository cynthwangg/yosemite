# Yosemite Availability Checker Setup Guide

This guide provides detailed instructions for setting up and configuring the Yosemite Availability Checker.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- Git (optional, for version control)

## Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/cynthwangg/yosemite.git
   cd yosemite
   ```

2. **Create and Activate Virtual Environment (Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Email Settings**
   Open `calendar_check.py` and update the following variables:
   ```python
   EMAIL_SENDER = "your-email@gmail.com"
   EMAIL_PASSWORD = "your-app-specific-password"
   EMAIL_RECIPIENT = "recipient-email@example.com"
   ```

   Note: If using Gmail, you'll need to:
   - Enable 2-factor authentication
   - Generate an app-specific password
   - Use that password in the script

5. **Configure Target Dates**
   In `calendar_check.py`, update the `target_days` list with your desired dates:
   ```python
   target_days = [
       {"month": 5, "day": 1, "year": 2025},
       {"month": 5, "day": 2, "year": 2025},
       {"month": 5, "day": 3, "year": 2025}
   ]
   ```

## Setting Up Automatic Execution

### On macOS (using launchd)

1. **Create Launch Agent**
   ```bash
   cp com.user.yosemitechecker.plist ~/Library/LaunchAgents/
   ```

2. **Load the Launch Agent**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.user.yosemitechecker.plist
   ```

### On Windows (using Task Scheduler)

1. Open Task Scheduler
2. Create a new task
3. Set the trigger to repeat every 15 minutes
4. Set the action to run `run_checker.bat`

### On Linux (using cron)

1. Open crontab:
   ```bash
   crontab -e
   ```

2. Add the following line:
   ```
   */15 * * * * /path/to/yosemite/run_checker.sh
   ```

## Testing the Setup

1. **Run the Script Manually**
   ```bash
   python calendar_check.py
   ```

2. **Check the Logs**
   - Review `check_log.txt` for any errors
   - Check if screenshots are being captured in the `results` directory

3. **Verify Email Notifications**
   - The script will send a test email on first run
   - Check your email for the test notification

## Troubleshooting

1. **Common Issues**
   - If emails aren't sending, verify your email credentials
   - If the script can't find the calendar, check if the website structure has changed
   - If screenshots aren't being saved, verify the `results` directory exists

2. **Debug Mode**
   Run the script with debug mode for more detailed output:
   ```bash
   python calendar_check.py --debug
   ```

3. **Checking Logs**
   - Review `check_log.txt` for error messages
   - Check `manual_run.log` for manual run results

## Maintenance

1. **Regular Updates**
   - Keep the script updated with the latest website changes
   - Update dependencies regularly:
     ```bash
     pip install -r requirements.txt --upgrade
     ```

2. **Monitoring**
   - Check logs regularly for any issues
   - Verify that the script is running as scheduled

## Security Notes

1. **Email Security**
   - Never commit email credentials to the repository
   - Use app-specific passwords for email accounts
   - Consider using environment variables for sensitive data

2. **File Permissions**
   - Ensure log files and screenshots are properly secured
   - Set appropriate permissions for the script and its files

## Support

For issues or questions, please open an issue on the GitHub repository. 