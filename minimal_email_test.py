#!/usr/bin/env python3
"""
Absolutely minimal email testing script
"""
import smtplib
from email.mime.text import MIMEText
import sys

# Email credentials - IMPORTANT: Update these with your actual email and app password!
EMAIL = "cynthwangg@gmail.com"  # REPLACE WITH YOUR EMAIL
PASSWORD = "znhg vrsb gyfr ejyz"  # REPLACE WITH YOUR APP PASSWORD (not your regular password)

# NOTE: Before running this script, you need to:
# 1. Replace EMAIL with your actual Gmail address
# 2. Replace PASSWORD with your Gmail App Password (not your regular password)
# 3. To get an App Password: Go to your Google Account → Security → App Passwords

def test_email():
    if EMAIL == "your_email@gmail.com":
        sys.stderr.write("ERROR: You need to edit this file and add your email and password first.\n")
        return False
        
    try:
        sys.stderr.write("Connecting to email server...\n")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        
        sys.stderr.write("Logging in...\n")
        server.login(EMAIL, PASSWORD)
        
        sys.stderr.write("Creating test message...\n")
        msg = MIMEText("This is a test email from the Yosemite Availability Checker.")
        msg['Subject'] = "Test Email"
        msg['From'] = EMAIL
        msg['To'] = EMAIL  # Sending to yourself
        
        sys.stderr.write("Sending email...\n")
        server.send_message(msg)
        server.quit()
        
        sys.stderr.write("SUCCESS: Email sent! Check your inbox.\n")
        return True
    except Exception as e:
        sys.stderr.write(f"ERROR: {str(e)}\n")
        return False

if __name__ == "__main__":
    sys.stderr.write("Starting minimal email test...\n")
    test_email()
    sys.stderr.write("Test completed.\n") 