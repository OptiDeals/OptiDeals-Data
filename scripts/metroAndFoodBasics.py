# Import necessary libraries
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime
import os

# Get today's date in the format YYYYMMDD
today = datetime.today().strftime('%Y%m%d')

# Define the URLs for the Food Basics and Metro websites
foodBasicsURL = "https://www.foodbasics.ca/search?sortOrder=relevance&filter=%3Arelevance%3Adeal%3AFLYER_DEAL"
metroURL = "https://www.metro.ca/en/online-grocery/flyer-page-{page}?sortOrder=relevance&filter=%3Arelevance%3Adeal%3AFlyer+%26+Deals"

# Define a function to scrape product data from a given URL and store it in a database
def scrape_products(base_url, store_name, unwanted_words):
    product_data = []  # Initialize an empty list to store product data

    # Get the first page to find the last page number
    response = requests.get(base_url.format(page=1))  # Send a GET request to the URL
    soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content of the page
    pagination = soup.find('div', class_='ppn--pagination')  # Find the pagination element on the page
    if pagination is None:
        print("Pagination element not found. Please check the URL or the structure of the webpage.")
        return
    else:
        last_page_number = int(pagination.find_all('a', class_='ppn--element')[-2].text)
        print(f"Found {last_page_number} pages of products.")

    # Loop through each page until the last page
    for page_number in range(1, last_page_number + 1):
        url = base_url.format(page=page_number)  # Format the URL with the current page number
        response = requests.get(url)  # Send a GET request to the URL
        if response.status_code == 403:
            print("Error 403: Forbidden")  # Print an error message if the status code is 403
        elif response.status_code != 200:
            print(f"Error accessing page {page_number}. Continuing to next page.")  # Print an error message if the status code is not 200
            continue

        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content of the page
        product_tiles = soup.find_all('div', class_='default-product-tile')  # Find all product tiles on the page

        if not product_tiles:
            print(f"No more products found on page {page_number}. Continuing to next page.")  # Print a message if no more products are found
            continue

        # Loop through each product tile and extract the product data
        for product_tile in product_tiles:
            product_name = product_tile.find('div', class_='head__title')  # Find the product name element
            product_name = product_name.text.strip() if product_name else None  # Get the text of the product name element, if it exists

            # Check if the element is present before accessing its text attribute
            product_amount_elem = product_tile.find('span', class_='head__unit-details')  # Find the product amount element
            product_amount = product_amount_elem.text.strip() if product_amount_elem else None  # Get the text of the product amount element, if it exists

            price_div = product_tile.find('div', {'data-main-price': True})  # Find the price element
            price = price_div['data-main-price'] if price_div else None  # Get the price, if the element exists

            # Check for unwanted words
            if any(word in product_name.lower() for word in unwanted_words):
                continue

            product_data.append({"Product": product_name, "Amount": product_amount, "Price": price})  # Append the product data to the list

        time.sleep(5)  # Add a delay of 5 seconds

    # Connect to the SQLite database
    conn = sqlite3.connect('data/optideals.db')
    cursor = conn.cursor()

    # Insert the data into the database
    for product in product_data:
        cursor.execute('''
            INSERT INTO grocery_ingredients (grocery_ingredient, grocery_amount, grocery_cost, grocery_store, date_scraped)
            VALUES (?, ?, ?, ?, ?)
        ''', (product["Product"], product["Amount"], product["Price"], store_name, today))
        count = count + 1

    # Commit the changes and close the connection
    print(count + "items scraped from " + storeName + " and placed in database.")
    count=0
    conn.commit()
    conn.close()

    print(f"Data has been successfully added to the database.")  # Print a success message

# Read unwanted words from file
def get_unwanted_words(unwanted_words_file):
    try:
        with open(unwanted_words_file, 'r') as f:
            return [line.strip().lower() for line in f]
    except Exception as e:
        print(f"An error occurred while reading the file {unwanted_words_file}: {e}")
        return []

# Call the function with the URLs, store names, and unwanted words
unwanted_words = get_unwanted_words('scripts/unwanted_words.txt')
print("Scraping Food Basics...")
scrape_products(foodBasicsURL, "foodbasics", unwanted_words)
print("Scraping Metro...")
scrape_products(metroURL, "metro", unwanted_words)
