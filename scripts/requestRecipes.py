from openai import OpenAI
import os
import csv
import json

# Load environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DATA_FILE_PATH = os.getenv('DATA_FILE_PATH')
DIET_TYPE = os.getenv('DIET_TYPE')
STORE_NAME = os.getenv('STORE_NAME')
CURRENT_DATE = os.getenv('CURRENT_DATE')
RECIPE_NUMBER = os.getenv('RECIPE_NUMBER')
RECIPE_FILE_PATH = os.getenv('RECIPE_FILE_PATH')
JSON_FORMAT_PATH = os.getenv('JSON_FORMAT_PATH')

# Check if environment variables are set
assert OPENAI_API_KEY, "OPENAI_API_KEY is not set"
assert DATA_FILE_PATH, "DATA_FILE_PATH is not set"
assert DIET_TYPE, "DIET_TYPE is not set"
assert STORE_NAME, "STORE_NAME is not set"
assert CURRENT_DATE, "CURRENT_DATE is not set"
assert RECIPE_NUMBER, "RECIPE_NUMBER is not set"
assert RECIPE_FILE_PATH, "RECIPE_FILE_PATH is not set"
assert JSON_FORMAT_PATH, "JSON_FORMAT_PATH is not set"

try:
    with open(JSON_FORMAT_PATH, 'r') as file:
        JSON_FORMAT = json.load(file)
except FileNotFoundError:
    print(f"File {JSON_FORMAT_PATH} not found")
    exit(1)
    
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Load data from CSV file
try:
    with open(DATA_FILE_PATH, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)
except FileNotFoundError:
    print(f"File {DATA_FILE_PATH} not found")
    exit(1)

# Prepare messages for the assistant
messages = [
    {
        "role": "system",
        "content": f"You are a recipe generation assistant created to generate recipes from a specific set of ingredients defined in a csv file. You will ensure all ingredients in the recipes come specifically from the data provided. You will ensure the user has basic essentials like butter, milk, eggs, oil, rice, and seasonings, do not add that to costs. You will also ensure you provide/output it in a specific JSON format as follows. {JSON_FORMAT}"
    },
    {
        "role": "user",
        "content": f"Using the food items from the provided data file, create {RECIPE_NUMBER} meal recipes that align with the specified diet type. Each recipe should include the following details: name, description, ingredients, quantities and costs of each ingredient, total cost of the recipe, and the number of servings it provides. Ensure all ingredients are suitable for a diet of type {DIET_TYPE}."
    }
]

# Generate recipes using OpenAI API
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
)

# Parse response and save recipes to JSON file
recipes = response.choices[0].message.content
recipe_file_path = os.path.join(RECIPE_FILE_PATH, f"{STORE_NAME}/{STORE_NAME}_{CURRENT_DATE}.json")
try:
    with open(recipe_file_path, 'w') as file:
        json.dump(recipes, file)
except FileNotFoundError:
    print(f"Directory {os.path.dirname(recipe_file_path)} not found")
    exit(1)
