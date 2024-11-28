# Import necessary modules and libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import sqlite3
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Function to check if a server is reachable
def is_server_reachable(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error reaching the server: {e}")
        return False

# URLs for the web UI and API
web_ui_url = "http://172.30.1.6:9090/"
api_url = "http://172.30.1.6:9090/api/v1/images/"

# Check if the web UI server is reachable
if not is_server_reachable(web_ui_url):
    print("Web UI server is not reachable. Exiting.")
    exit(1)

# Check if the API server is reachable
if not is_server_reachable(api_url):
    print("API server is not reachable. Exiting.")
    exit(1)

# Set up Chrome options for headless browsing
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--no-sandbox")  # Disable sandboxing
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Connect to the SQLite database
conn = sqlite3.connect('data/optideals.db')
cursor = conn.cursor()

# Retrieve the latest recipe date
cursor.execute('SELECT MAX(recipe_date) FROM recipes')
latest_date = cursor.fetchone()[0]

# Updated query to only select recipes with NULL images
cursor.execute("SELECT id, recipe_title, recipe_description FROM recipes WHERE recipe_image IS NULL")
recipes = cursor.fetchall()
all_images_processed = True

try:
    # Open the web UI
    driver.get(web_ui_url)

    # Wait until the UI is loaded
    WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.ID, "invoke-app-wrapper"))
    )

    # Click the "Use Default Settings" button
    use_default_settings_button = WebDriverWait(driver, 90).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Use Default Settings']"))
    )
    use_default_settings_button.click()

    # Process each recipe without an image
    for id, recipe_title, recipe_description in recipes:
        # Retrieve ingredients for the current recipe
        cursor.execute("SELECT recipe_ingredient, recipe_ingredient_amount FROM recipe_ingredients WHERE recipe_id = ?", (id,))
        ingredients = cursor.fetchall()
        ingredients_list = ", ".join([f"{amount} of {ingredient}" for ingredient, amount in ingredients])
        food_prompt = f"{recipe_title} - {recipe_description}. Ingredients: {ingredients_list}"
        print(f"Processing recipe ID: {id}, Prompt: {food_prompt}")

        try:
            # Enter the food prompt into the web UI input field
            prompt_input = WebDriverWait(driver, 90).until(
                EC.presence_of_element_located((By.ID, "prompt"))
            )
            prompt_input.clear()  # Clear any existing text in the input field
            prompt_input.send_keys(food_prompt)  # Enter the food prompt

            # Click the generate button to create an image
            generate_button = WebDriverWait(driver, 90).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".chakra-button.css-cos6y7"))
            )
            generate_button.click()
            print("Generate button clicked.")
            print("Waiting for the image to be generated...")
            time.sleep(100)  # Wait for the image to be generated (adjust based on your server's processing time)
            print("Image generation complete.")
        except Exception as e:
            print(f"Exception occurred during image generation for recipe ID {id}: {e}")
            print(driver.page_source)
            all_images_processed = False
            continue  # Continue with the next recipe

        try:
            # Fetch the generated image from the API
            response = requests.get(api_url, params={"limit": 1, "offset": 0})
            if response.status_code == 200:
                image_data = response.json()
                latest_image = image_data['items'][0]
                image_url = f"http://172.30.1.6:9090/{latest_image['image_url']}"
                image_response = requests.get(image_url)
                image_blob = image_response.content
                print(f"Fetched image for recipe ID {id}: {image_url}")
                if image_blob:
                    print(f"Image blob size: {len(image_blob)} bytes")
                    cursor.execute('UPDATE recipes SET recipe_image = ? WHERE id = ?', (image_blob, id))  # Update the database with the image
                    print(f"Image for recipe ID {id} has been updated in the database.")
                    conn.commit()  # Commit the changes to the database
                else:
                    print("Image blob is empty.")
                    all_images_processed = False
            else:
                print("Failed to fetch image details.")
                print("Status code:", response.status_code)
                print("Response:", response.text)
                all_images_processed = False
        except Exception as e:
            print(f"Exception occurred while fetching the image: {e}")
            all_images_processed = False

finally:
    driver.quit()  # Ensure the browser is closed

conn.close()  # Close the database connection
if all_images_processed:
    print("All images have been processed and stored in the database.")
else:
    print("Some images could not be processed. Check the error messages for details.")
