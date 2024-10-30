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
import subprocess

def is_server_reachable(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error reaching the server: {e}")
        return False

# Ensure ChromeDriver dependencies are installed
def install_chrome_dependencies():
    subprocess.run(['apt-get', 'update'], check=True)
    subprocess.run(['apt-get', 'install', '-y', 'wget', 'unzip', 'xvfb', 'libxi6', 'libgconf-2-4'], check=True)
    subprocess.run(['wget', '-q', 'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb'], check=True)
    subprocess.run(['dpkg', '-i', 'google-chrome-stable_current_amd64.deb'], check=True)
    subprocess.run(['apt-get', '-f', 'install', '-y'], check=True)

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

# Install ChromeDriver dependencies
install_chrome_dependencies()

# Configure WebDriver options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Connect to the SQLite database
conn = sqlite3.connect('data/optideals.db')
cursor = conn.cursor()

# Get the latest date from recipes
cursor.execute('SELECT MAX(recipe_date) FROM recipes')
latest_date = cursor
