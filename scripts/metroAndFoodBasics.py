# Import necessary libraries
import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime

# Get today's date in the format YYYYMMDD
today = datetime.today().strftime('%Y%m%d')

# Define the URLs for the Food Basics and Metro websites
foodBasicsURL = "https://www.foodbasics.ca/search-page-{page}?sortOrder=popularity&filter=%3Apopularity%3Adeal%3AFlyer+%26+Deals%2F%3Adeal%3AFlyer+%26+Deals&fromEcomFlyer=true"
metroURL = "https://www.metro.ca/en/online-grocery/flyer-page-{page}"

# Define a function to scrape product data from a given URL
def scrape_products(base_url, csv_file_path):
    product_data = []  # Initialize an empty list to store product data

    # Get the first page to find the last page number
    response = requests.get(base_url.format(page=1))  # Send a GET request to the URL
    soup = BeautifulSoup(response.content, 'html.parser')  # Parse the HTML content of the page
    pagination = soup.find('div', class_='ppn--pagination')  # Find the pagination element on the page
    if pagination is None:
        print("Pagination element not found. Please check the URL or the structure of the webpage.")
        return
    else:
        #last_page_number = int(pagination.find_all('a', class_='ppn--element')[-2].text)
        last_page_number = 1 #Testing purposes
        print(f"Found {last_page_number} pages of products.")

    # Loop through each page until the last page
    for page_number in range(1, last_page_number + 1):
        url = base_url.format(page=page_number)  # Format the URL with the current page number
        response = requests.get(url,)  # Send a GET request to the URL
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
            product_data.append({"Product": product_name, "Amount": product_amount, "Price": price})  # Append the product data to the list

        time.sleep(5)  # Add a delay of 5 seconds

    # Write the data to a CSV file
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["Product", "Amount", "Price"]  # Define the fieldnames for the CSV file
        writer = csv.DictWriter(file, fieldnames=fieldnames)  # Create a CSV writer

        # Write header
        writer.writeheader()

        # Write data
        for product in product_data:
            writer.writerow(product)  # Write each product to the CSV file

    print(f"Data has been successfully written to {csv_file_path}.")  # Print a success message

# Call the function with the URLs and output files
print("Scraping Food Basics...")
scrape_products(foodBasicsURL, f"data/scrapedData/foodBasics/foodbasics_{today}.csv")
print("Scraping Metro...")
scrape_products(metroURL, f"data/scrapedData/metro/metro_{today}.csv")
