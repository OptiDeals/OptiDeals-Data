from seleniumwire import webdriver  # Importing from seleniumwire for better debugging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import sqlite3
from datetime import datetime
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

web_ui_url = "http://172.30.1.6:9091/"
api_url = "http://172.30.1.6:9091/api/v1/images/"

if not is_server_reachable(web_ui_url):
    print("Web UI server is not reachable. Exiting.")
    exit(1)
if not is_server_reachable(api_url):
    print("API server is not reachable. Exiting.")
    exit(1)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = "/usr/bin/google-chrome"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

conn = sqlite3.connect('data/optideals.db')
cursor = conn.cursor()

cursor.execute('SELECT MAX(recipe_date) FROM recipes')
latest_date = cursor.fetchone()[0]

cursor.execute("SELECT id, recipe_title, recipe_description FROM recipes")
recipes = cursor.fetchall()
all_images_processed = True

for id, recipe_title, recipe_description in recipes:
    cursor.execute("SELECT recipe_ingredient, recipe_ingredient_amount FROM recipe_ingredients WHERE recipe_id = ?", (id,))
    ingredients = cursor.fetchall()
    ingredients_list = ", ".join([f"{amount} of {ingredient}" for ingredient, amount in ingredients])
    food_prompt = f"{recipe_title} - {recipe_description}. Ingredients: {ingredients_list}"
    print(f"Processing recipe ID: {id}, Prompt: {food_prompt}")
    try:
        driver.get(web_ui_url)
        print(f"Successfully opened {web_ui_url}")

        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.ID, "invoke-app-wrapper"))
        )
        print("Main container is present.")

        use_default_settings_button = WebDriverWait(driver, 90).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Use Default Settings']"))
        )
        use_default_settings_button.click()
        print("'Use Default Settings' button clicked.")

        prompt_input = WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.ID, "prompt"))
        )
        prompt_input.send_keys(food_prompt)
        print("Entered the prompt.")

        generate_button = WebDriverWait(driver, 90).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".chakra-button.css-cos6y7"))
        )
        generate_button.click()
        print("Generate button clicked.")

        print("Waiting for the image to be generated...")
        time.sleep(100)  # Adjust based on your server's processing time
        print("Image generation complete.")

    except Exception as e:
        print(f"Exception occurred: {e}")
        print(driver.page_source)  # This will help debug
        driver.quit()
        exit("Exiting due to failure in loading the web UI.")
    finally:
        driver.quit()

    try:
        response = requests.get(api_url, params={"limit": 1, "offset": 0})
        if response.status_code == 200:
            image_data = response.json()
            latest_image = image_data['items'][0]
            image_url = f"http://172.30.1.6:9091/{latest_image['image_url']}"
            image_response = requests.get(image_url)
            image_blob = image_response.content
            cursor.execute('UPDATE recipes SET recipe_image = ? WHERE id = ?', (image_blob, id))
            conn.commit()
        else:
            print("Failed to fetch image details.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
            all_images_processed = False
            break
    except Exception as e:
        print(f"Exception occurred while fetching the image: {e}")
        all_images_processed = False
        break

conn.close()
if all_images_processed:
    print("All images have been processed and stored in the database.")
else:
    print("Some images could not be processed. Check the error messages for details.")
