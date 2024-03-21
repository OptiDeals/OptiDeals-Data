# Import necessary libraries
import csv
import os
from datetime import date

# Load OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key}")

# Open CSV file containing ingredients
csv_file_path = os.getenv('CSV_FILE_PATH')
print(f"CSV File Path: {csv_file_path}")

with open(csv_file_path, 'r') as file:
    # Create CSV reader to read the file
    reader = csv.reader(file)
    # Read all data from the file into a list
    data = list(reader)
print(f"Data: {data}")

# Get number of recipes to generate from environment variables
num_recipes = int(os.getenv('NUM_RECIPES'))
print(f"Number of Recipes: {num_recipes}")

# Get filters from environment variables
total_cost = float(os.getenv('TOTAL_COST'))  # Desired total cost
print(f"Total Cost: {total_cost}")

is_vegan = os.getenv('IS_VEGAN').lower() == 'true'  # Whether recipes should be vegan
print(f"Is Vegan: {is_vegan}")

total_servings = int(os.getenv('TOTAL_SERVINGS'))  # Desired number of servings
print(f"Total Servings: {total_servings}")
