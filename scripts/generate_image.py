import sqlite3
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
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

# Check server reachability
if not is_server_reachable(web_ui_url):
    print("Web UI server is not reachable. Exiting.")
    exit(1)

if not is_server_reachable(api_url):
    print("API server is not reachable. Exiting.")
    exit(1)

# Configure WebDriver options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = "/usr/bin/google-chrome"

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Connect to the SQLite database
conn = sqlite3.connect('data/optideals.db')
cursor = conn.cursor()

# Get the latest date from recipes
cursor.execute('SELECT MAX(recipe_date) FROM recipes')
latest_date = cursor.fetchone()[0]

# Get all recipes with the latest date where recipe_image is NULL
cursor.execute("SELECT id, recipe_title, recipe_description FROM recipes")
recipes = cursor.fetchall()

all_images_processed = True  # Flag to track if all images were processed successfully

for id, recipe_title, recipe_description in recipes:
    # Fetch ingredients for the current recipe
    cursor.execute("SELECT recipe_ingredient, recipe_ingredient_amount FROM recipe_ingredients WHERE recipe_id = ?", (id,))
    ingredients = cursor.fetchall()

    # Construct the ingredients list
    ingredients_list = ", ".join([f"{amount} of {ingredient}" for ingredient, amount in ingredients])

    # Create the food prompt
    food_prompt = f"{recipe_title} - {recipe_description}. Ingredients: {ingredients_list}"

    # Print the processing message
    print(f"Processing recipe ID: {id}, Prompt: {food_prompt}")

    try:
        # Open the web UI
        driver.get(web_ui_url)
        print(f"Successfully opened {web_ui_url}")

        # Click 'Use Default Settings' to reset the browser
        use_default_settings_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Use Default Settings']"))
        )
        use_default_settings_button.click()

        # Enter the prompt
        prompt_input = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "prompt"))
        )
        prompt_input.send_keys(food_prompt)

        # Click the generate button
        generate_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".chakra-button.css-cos6y7"))
        )
        generate_button.click()

        # Wait for the image to be generated
        time.sleep(100)  # Adjust based on your server's processing time
    except Exception as e:
        print(f"Exception occurred: {e}")
        print(driver.page_source)  # Print page source for debugging
        all_images_processed = False
        break  # Stop processing further recipes
    finally:
        driver.quit()

    try:
        # Fetch the latest image from the API
        response = requests.get(api_url, params={"limit": 1, "offset": 0})
        if response.status_code == 200:
            image_data = response.json()
            latest_image = image_data['items'][0]
            image_url = f"http://172.30.1.6:9091/{latest_image['image_url']}"

            # Fetch the image as binary data without saving it to a file
            image_response = requests.get(image_url)
            image_blob = image_response.content

            # Update the database with the image BLOB
            cursor.execute('UPDATE recipes SET recipe_image = ? WHERE id = ?', (image_blob, id))
            conn.commit()
        else:
            print("Failed to fetch image details.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
            all_images_processed = False
            break  # Stop processing further recipes
    except Exception as e:
        print(f"Exception occurred while fetching the image: {e}")
        all_images_processed = False
        break  # Stop processing further recipes

# Close the database connection
conn.close()

if all_images_processed:
    print("All images have been processed and stored in the database.")
else:
    print("Some images could not be processed. Check the error messages for details.")
