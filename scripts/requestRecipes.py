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
        JSON_FORMAT = file.read()
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
        "content": '''You are an assistant that generates recipes from a CSV file of ingredients. The recipes will only use these ingredients, assuming basic essentials like butter, milk, eggs, oil, rice, and seasonings are already available. The output will be in this JSON format:
        {
          "name": "recipe name",
          "description": "description",
          "ingredients": [
            {"name": "ingredient name", "amount": "amount", "cost": "cost"},
            {"name": "ingredient name", "amount": "amount", "cost": "cost"}
          ],
          "total_cost": "total cost",
          "serves": "number of servings"
        }'''
    },
    {
        "role": "user",
        "content": f"Please create {RECIPE_NUMBER} recipes that align with the {DIET_TYPE} diet type using the ingredients from the provided data file. Each recipe should include the name, description, ingredients with their quantities and costs, total cost of the recipe, and the number of servings it provides."
    }
]


# Generate recipes using OpenAI API
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
)

# Parse response and save recipes to JSON file
recipes = json.loads(response.choices[0].message.content)

recipe_file_path = os.path.join(RECIPE_FILE_PATH, f"{STORE_NAME}/{STORE_NAME}_{CURRENT_DATE}.json")
recipe_file_path2 = os.path.join(RECIPE_FILE_PATH, f"{STORE_NAME}/recipes.json")
os.makedirs(os.path.dirname(recipe_file_path), exist_ok=True)
os.makedirs(os.path.dirname(recipe_file_path2), exist_ok=True)

# Write the recipes to the first file
with open(recipe_file_path, 'w') as file:
    json.dump(recipes, file)

# Write the recipes to the second file (recipes.json)
with open(recipe_file_path2, 'w') as file:
    json.dump(recipes, file)

# Print a success message
print(f"The recipes were successfully saved to {recipe_file_path} and {recipe_file_path2}.")
