import os
import time
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

linkedin_email = os.getenv('LINKEDIN_EMAIL')
linkedin_password = os.getenv('LINKEDIN_PASSWORD')

print(f"Email: {linkedin_email}")
print(f"Password: {linkedin_password}")

if linkedin_email is None or linkedin_password is None:
    print("Please set the environment variables LINKEDIN_EMAIL and LINKEDIN_PASSWORD.")
    exit(1)

def get_otp_email(username, password):
    otp = None
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)
    mail.select("inbox")
    status, messages = mail.search(None, "ALL")
    messages = messages[0].split()
    latest_email_id = messages[-1]
    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        otp = parse_otp_from_email_body(body)
                        break
            else:
                body = msg.get_payload(decode=True).decode()
                otp = parse_otp_from_email_body(body)
    mail.logout()
    return otp

def parse_otp_from_email_body(body):
    import re
    match = re.search(r'\b\d{6}\b', body)
    if match:
        return match.group(0)
    return None

def login_and_get_otp(driver):
    login(driver)
    otp = None
    while not otp:
        otp = get_otp_email(os.getenv('EMAIL_USERNAME'), os.getenv('EMAIL_PASSWORD'))
        if not otp:
            time.sleep(5)
    return otp

def login(driver):
    try:
        driver.get("https://www.linkedin.com/jobs/search/?f_AL=true&geoId=102713980&keywords=python%20developer&location=India")
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "nav__button-secondary"))).click()
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        if linkedin_email and linkedin_password:
            driver.find_element(By.NAME, "session_key").send_keys(linkedin_email)
            driver.find_element(By.ID, "password").send_keys(linkedin_password)
            driver.find_element(By.CSS_SELECTOR, "form button").send_keys(Keys.ENTER)
            otp = login_and_get_otp(driver)
            if otp:
                driver.find_element(By.ID, "otp-code").send_keys(otp)
                driver.find_element(By.CSS_SELECTOR, ".submit-otp-btn").click()
        else:
            print("Please set the environment variables LINKEDIN_EMAIL and LINKEDIN_PASSWORD.")
    except NoSuchWindowException as e:
        print(f"Exception occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def apply_to_jobs(driver):
    listings = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".job-card-container--clickable")))
    for listing in listings:
        print("Clicked Easy_apply confirmed")
        listing.click()
        time.sleep(3)
        try:
            apply_button = driver.find_element(By.CSS_SELECTOR, ".jobs-s-apply button")
            apply_button.click()
            time.sleep(5)
            phone_number = driver.find_element(By.CLASS_NAME, "fb-single-line-text__input")
            if phone_number.text == "":
                phone_number.send_keys("1234567899")
            cancel_button = driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss")
            cancel_button.click()
            discard_button = driver.find_element(By.CLASS_NAME, "artdeco-modal__confirm-dialog-btn")
            discard_button.click()
        except NoSuchElementException:
            print("No Application button available, skipped")
            continue

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 10)

login(driver)
apply_to_jobs(driver)

driver.quit()
