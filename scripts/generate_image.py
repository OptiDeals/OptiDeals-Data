import os
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import urllib.request
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def is_server_reachable(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error reaching the server: {e}")
        return False

# Define the URLs
web_ui_url = "http://172.30.1.6:9091/"
api_url = "http://172.30.1.6:9091/api/v1/images/"

if not is_server_reachable(web_ui_url):
    print("Web UI server is not reachable. Exiting.")
    exit(1)

recipe_id = os.getenv('RECIPE_ID')
food_prompt = os.getenv('PROMPT')

print("Configuring WebDriver options")
# Configure WebDriver options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

print("Initializing WebDriver in headless mode")
# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

print("Opening the web UI")
# Open the web UI
driver.get(web_ui_url)

try:
    print("Clicking 'Use Default Settings' to reset the browser")
    use_default_settings_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Use Default Settings']"))
    )
    use_default_settings_button.click()
    
    print("Waiting for the prompt input to be present")
    prompt_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "prompt"))
    )
    print("Entering the prompt")
    prompt_input.send_keys(food_prompt)

    print("Waiting for the generate button to be clickable")
    generate_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".chakra-button.css-cos6y7"))
    )
    generate_button.click()

    print("Waiting for the image to be generated")
    time.sleep(100)  # Adjust the sleep duration based on your server's processing time

finally:
    print("Closing the WebDriver")
    driver.quit()

if not is_server_reachable(api_url):
    print("API server is not reachable. Exiting.")
    exit(1)

print("Fetching the latest image from the API")
# Send a GET request to the API to fetch image details
response = requests.get(api_url, params={"limit": 1, "offset": 0})

if response.status_code == 200:
    print("Image details fetched successfully")
    image_data = response.json()
    latest_image = image_data['items'][0]
    image_url = f"http://172.30.1.6:9091/{latest_image['image_url']}"
    image_name = latest_image['image_name']

    print(f"Saving the image as {image_name}")
    # Save the image
    urllib.request.urlretrieve(image_url, f"{image_name}")
    print(f"Image saved successfully as {image_name}!")
else:
    print("Failed to fetch image details.")
    print("Status code:", response.status_code)
    print("Response:", response.text)
