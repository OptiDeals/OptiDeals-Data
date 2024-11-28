import sqlite3
import subprocess
import json
import requests
import time
import random
from transformers import LlamaTokenizer
import datetime
import os

# Variables
db_path = 'data/optideals.db'  # Path to the SQLite database
store_name = os.getenv('STORE_NAME')  # Store name from environment variable
max_retries = 10  # Maximum number of retries for generating recipes
api_url = "http://172.30.1.6:11434/api/generate"  # API URL for recipe generation
model_name = "llama3.2:3b"  # Name of the AI model to use
prompt_file = "prompt.json"  # File to store the prompt
date_format = "%Y-%m-%d"  # Date format used for storing dates
sleep_time = 1  # Sleep time between retries (in seconds)
ingredient_limit = 75  # Maximum number of ingredients to fetch from the database
recipe_generation_amount = 1  # Number of recipes to generate per request

# Prompt template for recipe generation
prompt_template = f'''
Using the provided list of ingredients, create {recipe_generation_amount} dinner recipe(s) in the following JSON format without any extra text and do not do math include the whole prices for the whole ingredient:
{{
  "title": "Recipe Title",
  "description": "Creative Recipe Description",
  "serving_size": "Number of people",
  "ingredients": [
    {{"name": "ingredient1", "quantity": "amount1", "cost": "cost1"}},
    {{"name": "ingredient2", "quantity": "amount2", "cost": "cost2"}}
  ]
}}

Ingredients list: 
'''

# Functions
def fetch_latest_ingredients_from_db(db_path, store_name):
    """Fetch the latest ingredients for a given store from the database."""
    try:
        print("Connecting to the database...")
        conn = sqlite3.connect(db_path)  # Connect to the SQLite database
        cursor = conn.cursor()  # Create a cursor object
        print(f"Fetching the latest date for store: {store_name}")
        # Fetch the latest date for the given store
        cursor.execute(
            "SELECT date_scraped FROM grocery_ingredients WHERE grocery_store = ? ORDER BY date_scraped DESC LIMIT 1",
            (store_name,)
        )
        latest_date = cursor.fetchone()[0]  # Retrieve the latest date
        print(f"Latest date found: {latest_date}")

        print(f"Fetching ingredients for the latest date: {latest_date}")
        # Fetch ingredients for the latest date and limit the results to ingredient_limit
        cursor.execute(
            f"SELECT grocery_ingredient, grocery_amount, grocery_cost FROM grocery_ingredients WHERE grocery_store = ? AND date_scraped = ? ORDER BY RANDOM() LIMIT {ingredient_limit}",
            (store_name, latest_date)
        )
        ingredients = cursor.fetchall()  # Fetch all the ingredients
        conn.close()  # Close the database connection
        print("Ingredients fetched from the database.")
        # Format the ingredients list with ingredient names, amounts, and costs
        return [(ingredient, amount, f"${cost}") for ingredient, amount, cost in ingredients]
    except Exception as e:
        print(f"Error fetching ingredients from database: {e}")  # Handle any errors
        return None

def validate_recipe(recipe):
    """Validate that the generated recipe contains all required fields."""
    required_fields = ['title', 'description', 'serving_size', 'ingredients']
    # Check if all required fields are present in the recipe
    for field in required_fields:
        if not recipe.get(field):
            return False
    # Check if all ingredients have the necessary fields
    for ingredient in recipe['ingredients']:
        if not all([ingredient.get('name'), ingredient.get('quantity'), ingredient.get('cost')]):
            return False
    return True  # Return True if all validations pass

def generate_recipes(db_path, store_name, prompt_template, max_retries):
    """Generate recipes using the latest ingredients from the database and the AI model."""
    ingredients_list = fetch_latest_ingredients_from_db(db_path, store_name)  # Fetch ingredients from the database
    if not ingredients_list:
        print("Failed to fetch ingredients from database. Aborting recipe generation.")  # Abort if no ingredients are fetched
        return None

    tokenizer = LlamaTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer")  # Load the Llama tokenizer
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1} to generate recipes...")

        print("Constructing the full prompt with ingredients list...")
        # Construct the ingredients list text
        ingredients_text = "\n".join(f"{idx+1}. {name}, {quantity}, {cost}" for idx, (name, quantity, cost) in enumerate(ingredients_list))
        # Replace the placeholder in the prompt template with the actual ingredients list
        prompt = prompt_template.replace("Ingredients list:", f"Ingredients list:\n{ingredients_text}")

        # Tokenize and count tokens using LLaMA tokenizer (commented out)
        # tokens = tokenizer(prompt)["input_ids"]
        # print(f"Token size of the prompt: {len(tokens)}")

        print("Writing prompt to a temporary file...")
        with open(prompt_file, "w") as f:
            # Write the prompt to a temporary file for the AI model
            json.dump({
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "keep_alive": 0
            }, f)

        # Call the AI endpoint using the subprocess module
        command = ["curl", api_url, "-d", f"@{prompt_file}"]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print("AI endpoint called successfully.")
            full_response = result.stdout  # Retrieve the response from the AI endpoint
            try:
                full_response_json = json.loads(full_response)  # Parse the JSON response
                response_json = full_response_json["response"]
                print("Parsing the response...")
                # Split the response into individual recipes and parse them as JSON
                recipes = [json.loads(recipe) for recipe in response_json.split('\n\n') if recipe.strip()]
                # Validate the parsed recipes
                validated_recipes = [recipe for recipe in recipes if validate_recipe(recipe)]
                if validated_recipes:
                    print("Recipes parsed successfully.")
                    return validated_recipes  # Return the validated recipes
                else:
                    print("No valid recipes found, retrying...")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")  # Handle JSON parsing errors
        else:
            print(f"Error calling AI endpoint: {result.stderr}")  # Handle errors from the AI endpoint

        print("Retrying...")  # Retry the recipe generation
        time.sleep(sleep_time)  # Optionally add a delay between retries

    print("Failed to generate recipes after max retries.")  # Fail after maximum retries
    return None

def insert_recipe_data(recipes, db_path, store_name):
    """Insert the generated recipes into the database."""
    try:
        print("Connecting to the database...")
        conn = sqlite3.connect(db_path)  # Connect to the SQLite database
        cursor = conn.cursor()  # Create a cursor object

        current_date = datetime.date.today().strftime(date_format)  # Get the current date

        for recipe in recipes:
            # Insert the recipe data into the recipes table
            cursor.execute(
                "INSERT INTO recipes (recipe_title, recipe_description, recipe_serving_size, recipe_total_cost, recipe_date, recipe_store) VALUES (?, ?, ?, ?, ?, ?)",
                (recipe['title'], recipe['description'], recipe['serving_size'], sum(float(ingredient['cost'].replace('$', '')) for ingredient in recipe['ingredients']), current_date, store_name)
            )
            recipe_id = cursor.lastrowid  # Retrieve the last inserted recipe ID
            # Insert each ingredient of the recipe into the recipe_ingredients table
            for ingredient in recipe['ingredients']:
                cursor.execute(
                    "INSERT INTO recipe_ingredients (recipe_id, recipe_ingredient, recipe_ingredient_amount, recipe_ingredient_cost) VALUES (?, ?, ?, ?)",
                    (recipe_id, ingredient['name'], ingredient['quantity'], float(ingredient['cost'].replace('$', '')))
                )

        conn.commit()  # Commit the changes
        conn.close()  # Close the database connection
        print("Data inserted into the database.")
    except Exception as e:
        print(f"Error inserting data into the database: {e}")  # Handle any errors

# Running Code
print("Generating recipes...")
recipes_output = generate_recipes(db_path, store_name, prompt_template, max_retries)
if recipes_output:
    print("Recipes generated successfully.")
    print(json.dumps(recipes_output, indent=2))  # Print the generated recipes
    # Insert the generated recipes into the database
    insert_recipe_data(recipes_output, db_path, store_name)
else:
    print("Failed to generate recipes.")  # Handle recipe generation failure
