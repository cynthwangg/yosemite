#!/usr/bin/env python3
"""
Yosemite availability checker focused on calendar date selectability
Using Selenium to interact with the calendar
"""
import requests
from bs4 import BeautifulSoup
import time
import datetime
import smtplib
from email.mime.text import MIMEText
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import os
from selenium.webdriver.support.ui import Select

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

# Booking URLs with calendar interfaces
BOOKING_URLS = {
    "Curry Village": "https://reservations.ahlsmsworld.com/Yosemite/Plan-Your-Trip/Accommodations/Curry-Village",
    "Yosemite Valley Lodge": "https://reservations.ahlsmsworld.com/Yosemite/Plan-Your-Trip/Accommodations/Yosemite-Valley-Lodge"
}

# Email settings for notifications
EMAIL_ENABLED = True
EMAIL_SENDER = "cynthwangg@gmail.com"
EMAIL_PASSWORD = "znhg vrsb gyfr ejyz"
EMAIL_RECIPIENT = "cynthwangg@gmail.com"
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# Directory for saving screenshots and HTML
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# File to track the last recap email sent
LAST_RECAP_FILE = os.path.join(RESULTS_DIR, "last_recap.txt")

# Function to check if it's time to send a daily recap email
def should_send_recap():
    """
    Check if we should send a daily recap email
    Returns True if last recap was sent more than 24 hours ago or never sent
    """
    today = datetime.datetime.now().date()
    
    if not os.path.exists(LAST_RECAP_FILE):
        return True
    
    try:
        with open(LAST_RECAP_FILE, "r") as f:
            last_date_str = f.read().strip()
            last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
            # Send if last recap was yesterday or earlier
            return today > last_date
    except:
        # If there's any error reading the file, assume we should send
        return True

# Function to update the last recap date
def update_last_recap_date():
    """Update the file that tracks when the last recap email was sent"""
    today = datetime.datetime.now().date().isoformat()
    with open(LAST_RECAP_FILE, "w") as f:
        f.write(today)
    print(f"✅ Updated last recap date to {today}")

# Add a retry decorator for functions that might encounter stale elements
def retry_on_stale_element(max_attempts=3, delay=1):
    """Decorator to retry functions when StaleElementReferenceException occurs"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        print(f"⚠️ Max retry attempts ({max_attempts}) reached for stale element")
                        raise e
                    print(f"⚠️ Stale element detected, retrying... (Attempt {attempts}/{max_attempts})")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# Use WebDriverWait with a retry mechanism for finding elements
def find_element_with_retry(driver, by, value, wait_time=10, clickable=False):
    """Find an element with retry on StaleElementReferenceException"""
    wait = WebDriverWait(driver, wait_time, ignored_exceptions=[StaleElementReferenceException])
    try:
        if clickable:
            return wait.until(EC.element_to_be_clickable((by, value)))
        else:
            return wait.until(EC.presence_of_element_located((by, value)))
    except (TimeoutException, StaleElementReferenceException) as e:
        print(f"⚠️ Could not find element {by}:{value} - {str(e)}")
        return None

def setup_webdriver():
    """
    Set up and return a Chrome WebDriver instance
    with settings to better avoid detection
    """
    chrome_options = Options()
    
    # Uncomment the headless option if you want to run without a browser UI
    chrome_options.add_argument("--headless")
    
    # These settings help avoid detection as an automated browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    
    # Use a realistic user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Exclude the "Chrome is being controlled by automated software" infobar
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    service = Service()  # You can specify the path to chromedriver if needed
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Additional settings via JavaScript to hide automation
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def check_calendar_availability(name, url):
    """
    Check if the target dates are selectable in the calendar using Selenium
    """
    print(f"\nChecking calendar for {name}...")
    print(f"URL: {url}")
    
    driver = setup_webdriver()
    date_selectability = {}
    calendar_available = False
    filename = None
    
    try:
        # Visit the booking page
        driver.get(url)
        print("✅ Successfully loaded booking page")
        
        # Wait for the page to load (adjust timeout as needed)
        wait = WebDriverWait(driver, 30)
        
        # Take a screenshot of the initial page
        screenshot_path = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_initial.png"
        driver.save_screenshot(screenshot_path)
        print(f"✅ Saved initial page screenshot to {screenshot_path}")
        
        # Save the initial HTML for inspection
        html_filename = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_initial.html"
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Find the date input elements
        try:
            # Create a list of selectors to try
            date_input_selectors = [
                (By.CLASS_NAME, "wxa-input-date-picker"),
                (By.CSS_SELECTOR, "input.wxa-input-date-picker"),
                (By.CSS_SELECTOR, "input[name='ArrivalDate']"),
                (By.CSS_SELECTOR, ".hasDatepicker"),
                (By.ID, "box-widget_ArrivalDate"),
                (By.XPATH, "//input[contains(@class, 'wxa-input-date-picker')]"),
                (By.XPATH, "//input[contains(@class, 'hasDatepicker')]"),
                (By.XPATH, "//label[text()='Check-in']/following::input[1]")
            ]
            
            # Try each selector until we find a clickable element
            arrival_date_input = None
            for selector_type, selector_value in date_input_selectors:
                try:
                    print(f"Trying to find date input with {selector_type}: {selector_value}")
                    arrival_date_input = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                    print(f"✅ Found date picker input element with {selector_type}: {selector_value}")
                    break
                except TimeoutException:
                    print(f"❌ Could not find element with {selector_type}: {selector_value}")
                    continue
            
            if not arrival_date_input:
                # Try an alternative approach - look for the calendar icon instead
                print("Trying to find calendar icon...")
                try:
                    calendar_icon = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".icon-ARMKicomooncalendar, .glyphicon-calendar, .input-group-addon")
                    ))
                    print("✅ Found calendar icon, will click on it")
                    calendar_icon.click()
                    print("✅ Clicked on calendar icon")
                    time.sleep(2)  # Wait for calendar to appear
                except TimeoutException:
                    print("❌ Could not find calendar icon")
                    
                    # Navigate to May 2025 in the calendar
                    try:
                        # First try to directly set the calendar to May 2025 using JavaScript
                        print("Attempting to set calendar to May 2025 using JavaScript...")
                        try:
                            # Different JavaScript approaches for different calendar implementations
                            js_approaches = [
                                # jQuery UI datepicker
                                """
                                if (jQuery && jQuery('.hasDatepicker').datepicker) {
                                    jQuery('.hasDatepicker').datepicker('setDate', new Date(2025, 4, 1));
                                    return true;
                                }
                                return false;
                                """,
                                # Bootstrap datepicker
                                """
                                if (jQuery && jQuery('.wxa-input-date-picker').bootstrapDP) {
                                    jQuery('.wxa-input-date-picker').bootstrapDP('update', new Date(2025, 4, 1));
                                    return true;
                                }
                                return false;
                                """,
                                # Generic approach - set the input value and trigger change
                                """
                                var dateInput = document.querySelector('input.wxa-input-date-picker') || 
                                               document.querySelector('input.hasDatepicker') ||
                                               document.querySelector('[name="ArrivalDate"]');
                                if (dateInput) {
                                    dateInput.value = '05/01/2025';
                                    
                                    // Create and dispatch change event
                                    var event = new Event('change', { bubbles: true });
                                    dateInput.dispatchEvent(event);
                                    
                                    // If using jQuery
                                    if (jQuery) {
                                        jQuery(dateInput).trigger('change');
                                    }
                                    return true;
                                }
                                return false;
                                """
                            ]
                            
                            javascript_success = False
                            for js_approach in js_approaches:
                                result = driver.execute_script(js_approach)
                                if result:
                                    javascript_success = True
                                    print("✅ Successfully set calendar to May 2025 using JavaScript")
                                    time.sleep(1)  # Wait for calendar to update
                                    break
                            
                            if javascript_success:
                                # Re-click the input to ensure the calendar is open
                                for selector_type, selector_value in date_input_selectors:
                                    try:
                                        date_input = driver.find_element(selector_type, selector_value)
                                        date_input.click()
                                        time.sleep(1)
                                        print("Re-clicked date input after JavaScript update")
                                        break
                                    except:
                                        continue
                        except Exception as js_error:
                            print(f"❌ JavaScript approach failed: {str(js_error)}")
                        
                        # Take a screenshot after JavaScript attempt
                        js_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_after_js.png"
                        driver.save_screenshot(js_screenshot)
                        print(f"✅ Saved screenshot after JavaScript attempt")
                        
                    except Exception as e:
                        print(f"❌ Error in JavaScript navigation: {str(e)}")
            else:
                # We found the date input, click it
                arrival_date_input.click()
                print("✅ Clicked on date input to show calendar")
                
            # Wait briefly for the calendar to appear
            time.sleep(2)
            
            # Wait for loading to complete
            try:
                wait.until(EC.invisibility_of_element_located((
                    By.XPATH, "//div[contains(text(), 'update the calendar with current availability')]"
                )), message="Calendar loading did not complete")
                print("✅ Calendar finished loading")
            except TimeoutException:
                print("⚠️ Loading message didn't disappear, calendar might not be fully loaded")
                # Take screenshot of loading state
                loading_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_loading_state.png"
                driver.save_screenshot(loading_screenshot)
                print(f"✅ Saved loading state screenshot to {loading_screenshot}")
            
            # Take a screenshot with the calendar open
            calendar_screenshot_path = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_calendar_open.png"
            driver.save_screenshot(calendar_screenshot_path)
            print(f"✅ Saved calendar screenshot to {calendar_screenshot_path}")
            
            # Save the HTML with the calendar open
            calendar_html_filename = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_calendar.html"
            with open(calendar_html_filename, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            filename = calendar_html_filename
            
            # Now find the datepicker component - try multiple possible selectors
            calendar_selectors = [
                ".ui-datepicker", 
                ".datepicker", 
                ".calendar-container",
                "#ui-datepicker-div"
            ]
            
            calendar = None
            for selector in calendar_selectors:
                try:
                    calendar = driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found calendar element with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not calendar:
                print("❌ Could not find calendar element on the page")
                return False, filename, date_selectability
            
            # Look for indicators of unavailable dates
            unavailable_indicators = [
                "ui-datepicker-unselectable", 
                "ui-state-disabled", 
                "unavailable", 
                "disabled", 
                "booked", 
                "sold-out",
                "ui-state-inactive",
                "not-available",
                "strikethrough"
            ]
            
            # Navigate to May 2025 in the calendar
            # We need to click on the next month button repeatedly until we reach May 2025
            # First, get current month/year displayed
            current_month_year = None
            try:
                # Look for the month/year header using various selectors
                month_header_selectors = [
                    (By.CLASS_NAME, "ui-datepicker-title"),
                    (By.CSS_SELECTOR, ".ui-datepicker-month"),
                    (By.CSS_SELECTOR, ".datepicker-switch"),
                    (By.CSS_SELECTOR, ".calendar-title")
                ]
                
                for selector_type, selector_value in month_header_selectors:
                    try:
                        month_header = driver.find_element(selector_type, selector_value)
                        current_month_year = month_header.text
                        print(f"Current calendar view: {current_month_year}")
                        break
                    except NoSuchElementException:
                        continue
                        
                if not current_month_year:
                    print("⚠️ Could not find month/year header in calendar")
            except Exception as e:
                print(f"⚠️ Error finding month header: {str(e)}")
            
            # Look for next button with different selectors
            try:
                next_button_selectors = [
                    (By.CLASS_NAME, "ui-datepicker-next"),
                    (By.CSS_SELECTOR, ".next"),
                    (By.CSS_SELECTOR, "[title='Next']"),
                    (By.CSS_SELECTOR, ".ui-icon-circle-triangle-e"),
                    (By.XPATH, "//a[contains(@class, 'ui-datepicker-next')]"),
                    (By.XPATH, "//a[contains(@class, 'next')]"),
                    (By.XPATH, "//button[contains(@class, 'next')]")
                ]
                
                next_button = None
                for selector_type, selector_value in next_button_selectors:
                    next_button = find_element_with_retry(driver, selector_type, selector_value, clickable=True)
                    if next_button:
                        print(f"Found next button with {selector_type}: {selector_value}")
                        break
                
                if not next_button:
                    print("❌ Could not find next month button in calendar")
                    raise NoSuchElementException("Next button not found")
                
                # If we have a 'month' dropdown and 'year' dropdown, try using them directly
                try:
                    # Look for month and year select elements - more reliable than clicking
                    month_select = find_element_with_retry(driver, By.CSS_SELECTOR, "select.ui-datepicker-month, select.month")
                    year_select = find_element_with_retry(driver, By.CSS_SELECTOR, "select.ui-datepicker-year, select.year")
                    
                    if month_select and year_select:
                        print("✅ Found month/year dropdowns - will try to set directly")
                        
                        # Add a small wait to ensure dropdowns are fully loaded
                        time.sleep(1)
                        
                        try:
                            # Set month (May is usually value 4, since it's 0-indexed)
                            month_dropdown = Select(month_select)
                            month_dropdown.select_by_visible_text("May")
                            print("✅ Set month dropdown to May")
                            
                            # Set year to 2025
                            year_dropdown = Select(year_select)
                            year_dropdown.select_by_visible_text("2025")
                            print("✅ Set year dropdown to 2025")
                            
                            time.sleep(2)  # Give more time for calendar to update
                            
                            # Take a screenshot after direct selection
                            direct_select_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_direct_select.png"
                            driver.save_screenshot(direct_select_screenshot)
                            print(f"✅ Saved screenshot after direct month/year selection")
                            
                            # Skip the click-based navigation since we set it directly
                            reached_target = True
                        except Exception as select_error:
                            print(f"⚠️ Error setting month/year: {str(select_error)}")
                            reached_target = False
                    else:
                        print("No month/year dropdowns found, will navigate by clicking")
                        reached_target = False
                except NoSuchElementException:
                    print("No month/year dropdowns found, will navigate by clicking")
                    reached_target = False
                
                # If direct selection failed, proceed with click-based navigation
                if not reached_target:
                    # Keep clicking until we reach May 2025
                    clicks = 0
                    max_clicks = 36  # Maximum 3 years of clicking next
                    
                    @retry_on_stale_element(max_attempts=3)
                    def click_next_and_check():
                        nonlocal clicks, current_month_year, reached_target
                        
                        # Take a screenshot before clicking
                        month_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_month_{clicks}.png"
                        driver.save_screenshot(month_screenshot)
                        
                        # Check if we're already at May 2025
                        if current_month_year:
                            print(f"Current view: '{current_month_year}'")
                            
                            # Exact match
                            if current_month_year == "May 2025":
                                print(f"✅ Already at target month: {current_month_year}")
                                return True
                            
                            # Check if both "May" and "2025" are in the text
                            if "May" in current_month_year and "2025" in current_month_year:
                                print(f"✅ Text contains both May and 2025: {current_month_year}")
                                return True
                            
                            # Check if we're at April 2025 - this is a problem!
                            if ("April" in current_month_year or "Apr" in current_month_year) and "2025" in current_month_year:
                                print(f"⚠️ We're at April 2025, need to click Next once more: {current_month_year}")
                        
                        # Click the next button - wrap in try/except for stale elements
                        try:
                            # Refind the next button in case the DOM updated
                            next_button = None
                            for selector_type, selector_value in next_button_selectors:
                                next_button = find_element_with_retry(driver, selector_type, selector_value, clickable=True)
                                if next_button:
                                    break
                                    
                            if not next_button:
                                print("❌ Could not find next month button after page update")
                                return False
                                
                            next_button.click()
                            print(f"Clicked next button (click #{clicks+1})")
                            time.sleep(2)  # Give UI more time to update
                            
                            # Take a screenshot after clicking to see the change
                            after_click_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_after_click_{clicks+1}.png"
                            driver.save_screenshot(after_click_screenshot)
                            
                        except StaleElementReferenceException:
                            print("⚠️ Stale element when clicking next - will retry with fresh element")
                            time.sleep(1)
                            return False
                            
                        # Update current month/year
                        month_found = False
                        for selector_type, selector_value in month_header_selectors:
                            try:
                                month_header = find_element_with_retry(driver, selector_type, selector_value)
                                if month_header:
                                    current_month_year = month_header.text
                                    print(f"Navigated to: {current_month_year}")
                                    month_found = True
                                    
                                    # Check if we've reached May 2025
                                    if (current_month_year == "May 2025" or
                                        ("May" in current_month_year and "2025" in current_month_year)):
                                        print(f"✅ Reached target month: {current_month_year}")
                                        return True
                                        
                                    # Also check separately for month and year parts
                                    if selector_type == By.CLASS_NAME and selector_value == "ui-datepicker-title":
                                        # The title might have month and year as separate elements
                                        try:
                                            month_el = find_element_with_retry(driver, By.CLASS_NAME, "ui-datepicker-month")
                                            year_el = find_element_with_retry(driver, By.CLASS_NAME, "ui-datepicker-year")
                                            if month_el and year_el:
                                                print(f"Month: '{month_el.text}', Year: '{year_el.text}'")
                                                if month_el.text.strip() == "May" and year_el.text.strip() == "2025":
                                                    print("✅ Reached May 2025 (from separate elements)")
                                                    return True
                                        except:
                                            pass
                            except:
                                continue
                        
                        if not month_found:
                            print("⚠️ Could not find month/year header after click")
                        
                        return False
                    
                    # Use the wrapped function to navigate to May 2025
                    while clicks < max_clicks and not reached_target:
                        reached_target = click_next_and_check()
                        if reached_target:
                            break
                            
                        clicks += 1
                
                if reached_target:
                    print(f"✅ Successfully navigated to the target month")
                    
                    # Take a screenshot of May 2025
                    may_2025_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_may_2025.png"
                    driver.save_screenshot(may_2025_screenshot)
                    print(f"✅ Saved May 2025 calendar screenshot to {may_2025_screenshot}")
                    
                    # Save the HTML with May 2025 calendar open
                    may_2025_html = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_may_2025.html"
                    with open(may_2025_html, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    
                    # Check our target days (May 23-26, 2025)
                    target_days = ["23", "24", "25", "26"]
                    
                    # Take a full screenshot of May 2025 for reference
                    may_2025_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_may_2025.png"
                    driver.save_screenshot(may_2025_screenshot)
                    print(f"✅ Saved May 2025 calendar screenshot to {may_2025_screenshot}")
                    
                    # Save the HTML with May 2025 calendar open
                    may_2025_html = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_may_2025.html"
                    with open(may_2025_html, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    
                    # Add a double check that we're really in May 2025
                    is_may_2025_confirmed = False
                    
                    # Check using text content on page
                    try:
                        month_content = driver.find_element(By.CSS_SELECTOR, ".ui-datepicker-title, .month, .datepicker-switch").text
                        print(f"Month header text: '{month_content}'")
                        if "May" in month_content and "2025" in month_content:
                            is_may_2025_confirmed = True
                            print("✅ Confirmed via text that we're in May 2025")
                        elif "April" in month_content or "Apr" in month_content:
                            print("❌ WARNING: We appear to be in April, not May! Results may be incorrect")
                    except NoSuchElementException:
                        print("⚠️ Could not find month header for verification")
                    
                    # Look for typical May 2025 calendar patterns
                    try:
                        # May 2025 starts on a Thursday, so the first days should be empty cells
                        # Find all day cells in the first row
                        first_week_cells = driver.find_elements(By.CSS_SELECTOR, "tr:first-child td")
                        if len(first_week_cells) >= 7:  # Most calendars have 7 day columns
                            first_day_text = first_week_cells[3].text.strip()  # Thursday is index 3 (0-indexed from Sunday)
                            if first_day_text == "1":
                                print("✅ Calendar starts on Thursday with day 1 - matches May 2025 pattern")
                                is_may_2025_confirmed = True
                            else:
                                print(f"⚠️ First Thursday cell has text '{first_day_text}', not '1' as expected for May 2025")
                    except Exception as e:
                        print(f"⚠️ Error checking calendar pattern: {str(e)}")
                    
                    # Print a message if we couldn't confirm May 2025
                    if not is_may_2025_confirmed:
                        print("⚠️ Could not definitively confirm we're looking at May 2025 - proceed with caution")
                    
                    for day in target_days:
                        print(f"\nChecking for day {day}...")
                        # Different ways to find day cells
                        day_cell = None
                        day_cell_selectors = [
                            f"//td[@data-date='2025-05-{day}']",
                            f"//td[@data-date='05/{day}/2025']",
                            f"//td[@data-date='05-{day}-2025']",
                            f"//td[@data-month='4'][@data-day='{day}'][@data-year='2025']",  # May is month 4 (0-indexed)
                            f"//a[text()='{day}']",  # Simple text match (may need parent td check)
                            f"//td[contains(@class, 'ui-datepicker-day')]//a[text()='{day}']",
                            f"//td[not(contains(@class, 'ui-datepicker-other-month'))]//a[text()='{day}']",
                            f"//td[contains(@class, 'day')]//span[text()='{day}']",  # Another common pattern
                            f"//table//td[.//text()='{day}']"  # Broader match for any text in table cell
                        ]
                        
                        # Try to find the day cell with retries
                        @retry_on_stale_element(max_attempts=3)
                        def find_day_cell():
                            nonlocal day_cell
                            for selector in day_cell_selectors:
                                try:
                                    candidate = find_element_with_retry(driver, By.XPATH, selector, wait_time=3)
                                    if candidate:
                                        print(f"✅ Found day {day} with selector: {selector}")
                                        return candidate
                                except Exception as e:
                                    pass
                            return None
                            
                        # Try to find the day cell
                        day_cell = find_day_cell()
                            
                        if day_cell:
                            # Take screenshot highlighting this date cell
                            try:
                                # Reset any previous red borders
                                driver.execute_script("""
                                    var prevHighlighted = document.querySelectorAll('[data-highlight="true"]');
                                    for(var i=0; i<prevHighlighted.length; i++) {
                                        prevHighlighted[i].style.border = '';
                                    }
                                """)
                                
                                # Add red border and set attribute so we can find it
                                driver.execute_script("""
                                    arguments[0].style.border = '3px solid red';
                                    arguments[0].setAttribute('data-highlight', 'true');
                                """, day_cell)
                                day_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_day_{day}.png"
                                driver.save_screenshot(day_screenshot)
                                print(f"✅ Saved screenshot highlighting day {day}")
                            except Exception as e:
                                print(f"⚠️ Could not highlight day: {str(e)}")
                                
                            # Get the complete text including any child elements
                            try:
                                cell_text = day_cell.text.strip()
                                print(f"Day {day} cell text: '{cell_text}'")
                                
                                # Look for N/A text
                                has_na = "N/A" in cell_text
                                if has_na:
                                    print(f"⚠️ Found N/A text in day {day} cell")
                            except StaleElementReferenceException:
                                print("⚠️ Stale element when getting cell text")
                                has_na = False
                                
                            # Check if the parent TD is disabled
                            parent_td = None
                            try:
                                if day_cell.tag_name == 'a' or day_cell.tag_name == 'span':
                                    # Get the parent TD element
                                    try:
                                        parent_td = find_element_with_retry(driver, By.XPATH, "./ancestor::td", wait_time=2)
                                        if not parent_td:
                                            parent_td = day_cell.find_element(By.XPATH, "./..")
                                    except:
                                        parent_td = day_cell
                                else:
                                    parent_td = day_cell
                            except StaleElementReferenceException:
                                print("⚠️ Stale element when finding parent TD")
                                parent_td = day_cell
                            
                            # Check for unavailability indicators
                            is_unavailable = False
                            
                            try:
                                element_classes = parent_td.get_attribute("class") or ""
                                print(f"Day {day} classes: '{element_classes}'")
                                
                                # Check classes for unavailability indicators
                                for indicator in unavailable_indicators:
                                    if indicator in element_classes:
                                        is_unavailable = True
                                        print(f"❌ Found unavailability indicator '{indicator}' in classes")
                                        break
                                
                                # Also check for N/A text or grayed out appearance
                                if has_na:
                                    is_unavailable = True
                                
                                # Check for gray background or text color via computed style
                                try:
                                    background_color = driver.execute_script(
                                        "return window.getComputedStyle(arguments[0]).backgroundColor", parent_td)
                                    text_color = driver.execute_script(
                                        "return window.getComputedStyle(arguments[0]).color", parent_td)
                                    print(f"Background color: {background_color}, Text color: {text_color}")
                                    
                                    # Check if colors suggest it's disabled (gray/light colors)
                                    if ("rgb(211, 211, 211)" in background_color or 
                                        "rgba(0, 0, 0, 0.3)" in text_color or 
                                        "lightgrey" in background_color or
                                        "gray" in background_color):
                                        print("❌ Cell appears to be grayed out based on colors")
                                        is_unavailable = True
                                except Exception as style_error:
                                    print(f"⚠️ Could not check cell styles: {str(style_error)}")
                            except StaleElementReferenceException:
                                print("⚠️ Stale element when checking availability indicators")
                                # Be conservative - if we had a stale element reference, play it safe
                                is_unavailable = True
                            
                            # Check if the element is actually clickable (a good test for availability)
                            try:
                                is_clickable = EC.element_to_be_clickable((By.XPATH, f"//a[text()='{day}']"))
                                if not is_clickable:
                                    print("❌ Day cell is not clickable")
                                    is_unavailable = True
                            except:
                                pass
                            
                            # Set final availability status
                            selectable = not is_unavailable
                            date_selectability[f"May {day}, 2025"] = selectable
                            
                            if selectable:
                                print(f"✅ Date May {day}, 2025 appears to be SELECTABLE!")
                                calendar_available = True
                            else:
                                print(f"❌ Date May {day}, 2025 appears to be NOT SELECTABLE")
                        else:
                            print(f"⚠️ Could not find day {day} in the calendar")
                            # Set this date as not available since we couldn't find it
                            date_selectability[f"May {day}, 2025"] = False
                    
                    # After checking all dates, if we couldn't confirm May 2025, override results
                    if not is_may_2025_confirmed:
                        # If we couldn't confirm we were in May 2025, set all dates as not available
                        print("⚠️ Since we couldn't confirm May 2025, marking all dates as unavailable for safety")
                        for day in target_days:
                            date_selectability[f"May {day}, 2025"] = False
                        calendar_available = False
                else:
                    print(f"❌ Could not navigate to target month after {clicks} attempts")
                    print(f"   Last view: {current_month_year}")
                    # Set all dates as not available
                    for day in target_days:
                        date_selectability[f"May {day}, 2025"] = False
            except NoSuchElementException as e:
                print(f"❌ Could not find next month button in calendar: {str(e)}")
                # Take a screenshot when we can't find the next button
                error_screenshot = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_next_button_error.png"
                driver.save_screenshot(error_screenshot)
                print(f"✅ Saved error screenshot to {error_screenshot}")
                
                # Try to examine the document structure for debugging
                try:
                    calendar_html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
                    calendar_html_path = f"{RESULTS_DIR}/{name.lower().replace(' ', '_')}_calendar_html.html"
                    with open(calendar_html_path, "w", encoding="utf-8") as f:
                        f.write(calendar_html)
                    print(f"✅ Saved calendar HTML to {calendar_html_path}")
                except:
                    pass
                
        except TimeoutException:
            print("❌ Timed out waiting for date input element")
            capture_page_debug_info(driver, name, "timeout_finding_datepicker")
            
    except Exception as e:
        print(f"❌ Error checking calendar for {name}: {str(e)}")
        capture_page_debug_info(driver, name, "general_error")
        import traceback
        traceback.print_exc()
    finally:
        # Close the browser
        driver.quit()
    
    # Analyze overall calendar selectability
    if calendar_available:
        print(f"✅ POTENTIAL AVAILABILITY FOUND in calendar for {name}!")
        print(f"   At least one of your target dates appears selectable")
        return True, filename, date_selectability
    else:
        print(f"❌ No availability found in calendar for {name}")
        print(f"   None of your target dates appear selectable")
        return False, filename, date_selectability

def send_notification(name, url, date_info, filename):
    """Send an email notification when availability is found"""
    if not EMAIL_ENABLED:
        print("Email notifications are disabled")
        return
    
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"Yosemite Availability Alert: {name}"
        
        # Format the selectable dates
        date_details = ""
        for date, is_selectable in date_info.items():
            status = "SELECTABLE ✓" if is_selectable else "Not selectable ✗"
            date_details += f"{date}: {status}\n        "
        
        body = f"""
        Potential availability detected at {name}!
        
        Target dates:
        Check-in: {TARGET_DATES["check_in"]["display"]}
        Check-out: {TARGET_DATES["check_out"]["display"]}
        
        Status of dates in calendar:
        {date_details}
        
        Time detected: {current_time}
        
        Book now at: {url}
        
        This is an automated message from your Yosemite Availability Checker.
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        
        print(f"Sending email notification to {EMAIL_RECIPIENT}...")
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Notification email sent!")
    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")

def send_daily_recap(results):
    """Send a daily recap email even if no availability was found"""
    if not EMAIL_ENABLED:
        print("Email notifications are disabled")
        return
    
    if not should_send_recap():
        print("Daily recap email was already sent today, skipping")
        return
    
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"Yosemite Availability Checker - Daily Recap"
        
        # Check if any location had availability
        any_available = any(status == "POTENTIAL AVAILABILITY" for status in results.values())
        
        # Create summary of results
        results_summary = ""
        for name, status in results.items():
            results_summary += f"{name}: {status}\n        "
        
        # Different message based on availability
        if any_available:
            main_message = "Good news! Some availability was detected today. Check your other emails for details."
        else:
            main_message = "No availability was found today for your desired dates."
        
        body = f"""
        Yosemite Availability Checker - Daily Recap
        
        {main_message}
        
        Target dates:
        Check-in: {TARGET_DATES["check_in"]["display"]}
        Check-out: {TARGET_DATES["check_out"]["display"]}
        
        Summary of checks:
        {results_summary}
        
        Time of report: {current_time}
        
        The script will continue checking every 15 minutes.
        
        This is an automated message from your Yosemite Availability Checker.
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        
        print(f"Sending daily recap email to {EMAIL_RECIPIENT}...")
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Daily recap email sent!")
        
        # Update the last recap date
        update_last_recap_date()
        
    except Exception as e:
        print(f"❌ Error sending daily recap: {str(e)}")

def capture_page_debug_info(driver, name, error_context):
    """
    Capture debug information about the page when an error occurs
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = f"{RESULTS_DIR}/debug"
    os.makedirs(debug_dir, exist_ok=True)
    
    # Take a screenshot
    screenshot_path = f"{debug_dir}/{name.lower().replace(' ', '_')}_{error_context}_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    
    # Save the HTML
    html_path = f"{debug_dir}/{name.lower().replace(' ', '_')}_{error_context}_{timestamp}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    # Extract and save information about visible elements
    visible_elements_path = f"{debug_dir}/{name.lower().replace(' ', '_')}_{error_context}_{timestamp}_elements.txt"
    try:
        # Get all visible input elements, buttons, and links
        elements_info = []
        
        # Check input elements
        input_elements = driver.find_elements(By.TAG_NAME, "input")
        for el in input_elements:
            try:
                if el.is_displayed():
                    elements_info.append({
                        "tag": "input",
                        "type": el.get_attribute("type"),
                        "id": el.get_attribute("id"),
                        "name": el.get_attribute("name"),
                        "class": el.get_attribute("class"),
                        "value": el.get_attribute("value")
                    })
            except:
                pass
        
        # Check div elements with potential datepicker classes
        div_elements = driver.find_elements(By.CSS_SELECTOR, "div.datepicker, div.ui-datepicker, #ui-datepicker-div")
        for el in div_elements:
            try:
                elements_info.append({
                    "tag": "div",
                    "id": el.get_attribute("id"),
                    "class": el.get_attribute("class"),
                    "visible": el.is_displayed()
                })
            except:
                pass
                
        # Save to file
        with open(visible_elements_path, "w", encoding="utf-8") as f:
            json.dump(elements_info, f, indent=2)
            
    except Exception as element_error:
        print(f"Error gathering element info: {str(element_error)}")
    
    print(f"✅ Saved debug information to {debug_dir}")
    return screenshot_path, html_path, visible_elements_path

def main():
    """Run calendar availability checks"""
    print("\n===== YOSEMITE CALENDAR AVAILABILITY CHECKER =====")
    print(f"Checking if dates are selectable: {TARGET_DATES['check_in']['display']} to {TARGET_DATES['check_out']['display']}")
    print("=================================================")
    
    results = {}
    
    # Check each booking site
    for name, url in BOOKING_URLS.items():
        available, filename, date_info = check_calendar_availability(name, url)
        
        if available:
            results[name] = "POTENTIAL AVAILABILITY"
            send_notification(name, url, date_info, filename)
        elif available is None:
            results[name] = "ERROR CHECKING"
        else:
            results[name] = "NO AVAILABILITY"
            
        # Pause between checks to avoid overloading the server
        time.sleep(2)
    
    # Print summary
    print("\n===== CHECK SUMMARY =====")
    for name, status in results.items():
        print(f"{name}: {status}")
    print("========================\n")
    
    print("Check completed! Review saved screenshots and HTML files in the results directory.")
    
    # Send daily recap email
    send_daily_recap(results)

if __name__ == "__main__":
    main() 