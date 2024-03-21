# Import necessary libraries
import csv
import json
from openai import OpenAI
import os
from datetime import date

# Load OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')
# Initialize OpenAI client with API key
client = OpenAI(api_key=api_key)

# Open CSV file containing ingredients
with open(os.getenv('CSV_FILE_PATH'), 'r') as file:
    # Create CSV reader to read the file
    reader = csv.reader(file)
    # Read all data from the file into a list
    data = list(reader)

# Get number of recipes to generate from environment variables
num_recipes = int(os.getenv('NUM_RECIPES'))

# Get filters from environment variables
total_cost = float(os.getenv('TOTAL_COST'))  # Desired total cost
is_vegan = os.getenv('IS_VEGAN').lower() == 'true'  # Whether recipes should be vegan
total_servings = int(os.getenv('TOTAL_SERVINGS'))  # Desired number of servings

# Create message for AI
message = f"Create {num_recipes} recipes using these ingredients: {data}. Each recipe should have a total cost of around {total_cost}, be vegan: {is_vegan}, and serve {total_servings} people. Please provide a name, short description, and a list of ingredients with their costs for each recipe. Assume availability of basics like butter, milk, eggs, oil, rice, and seasonings. Output in JSON format."

# Request a completion from AI
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful recipe cook assistant."
        },
        {
            "role": "user",
            "content": message
        }
    ],
    temperature=1,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
)

# Extract recipes from response
recipes = response['choices'][0]['message']['content']

# Convert the recipes to JSON format
recipes_json = json.dumps(recipes)

file_path = f'data/requestedRecipes/metro/recipes_{date.today()}.json'
# Save recipes to a JSON file
with open(file_path, 'w') as file:
    file.write(recipes_json)
