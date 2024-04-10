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

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Load data from CSV file
with open(DATA_FILE_PATH, 'r') as file:
    reader = csv.reader(file)
    data = list(reader)

# Prepare messages for the assistant
messages = [
    {
        "role": "system",
        "content": "You are a recipe generation assistant created to generate recipes from a specific set of ingredients defined in a csv file. You will ensure all ingredients in the recipes come specifically from the data provided. You will ensure the user has basic essentials like butter, milk, eggs, oil, rice, and seasonings, do not add that to costs. You will also ensure you provide/output it in a specific JSON format as follows. \n[\n      {\n          \"name\": \"Recipe Name\",\n          \"description\": \"Description of Recipe\",\n          \"ingredients\": [\n              {\"name\": \"Ingredient 1\", \"amount\": \"Amount\", \"cost\": \"Cost\"},\n              {\"name\": \"Ingredient ...\", \"amount\": \"Amount\", \"cost\": \"Cost\"}`\n          ],`\n          \"total_cost\": \"Total Cost for Recipe\",\n          \"serves\": \"Number of Servings for Recipe\",\n          \"vegan\": \"true or false\n      },\n      {\n          \"name\": \"Recipe Name\",\n          \"description\": \"Description of Recipe\",\n          \"ingredients\": [`\n              {\"name\": \"Ingredient 1\", \"amount\": \"Amount\", \"cost\": \"Cost\"},\n              {\"name\": \"Ingredient ...\", \"amount\": \"Amount\", \"cost\": \"Cost\"}\n          ],`\n          \"total_cost\": \"Total Cost for Recipe \",\n          \"serves\": \"Number of Servings for Recipe \",\n          \"vegan\": \"true or false\"\n      },\n      ...\n  ]"
    },
    {
        "role": "user",
        "content": "Using the food items from the provided data file, create seven meal recipes that align with the specified diet type. Each recipe should include the following details: name, description, ingredients, quantities and costs of each ingredient, total cost of the recipe, and the number of servings it provides. Ensure all ingredients are suitable for a diet of type {DIET_TYPE}."
    }
]

# Generate recipes using OpenAI API
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
)

# Parse response and save recipes to JSON file
recipes = response['choices'][0]['message']['content']
recipe_file_path = os.path.join(RECIPE_FILE_PATH, f"{STORE_NAME}/{STORE_NAME}_{CURRENT_DATE}.csv")
with open(recipe_file_path, 'w') as file:
    json.dump(recipes, file)
