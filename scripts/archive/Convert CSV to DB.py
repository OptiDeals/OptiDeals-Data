import sqlite3
import pandas as pd
import os
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect('optideals.db')
cursor = conn.cursor()

# Folder containing the CSV files
folder_path = './csv'

# Process each CSV file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        # Extract store name and date from the filename
        store_name, date_str = filename.split('_')
        date_str = date_str.split('.')[0]  # Remove file extension
        try:
            date_scraped = datetime.strptime(date_str, '%Y%m%d').date()
        except ValueError as e:
            print(f"Error parsing date from filename {filename}: {e}")
            continue

        # Read the CSV file
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path)

        # Insert data into the grocery_ingredients table
        for _, row in df.iterrows():
            cursor.execute('''
            INSERT INTO grocery_ingredients (grocery_ingredient, grocery_amount, grocery_cost, grocery_store, date_scraped)
            VALUES (?, ?, ?, ?, ?)''', (row['Product'], row['Amount'], row['Price'], store_name, date_scraped))

# Commit changes and close the connection
conn.commit()
conn.close()

print("Grocery ingredients imported successfully!")
