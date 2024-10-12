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
db_path = 'data/optideals.db'
store_name = os.getenv('STORE_NAME')
max_retries = 10
api_url = "http://172.30.1.6:11434/api/generate"
model_name = "llama3.1:8b"
prompt_file = "prompt.json"
date_format = "%Y-%m-%d"
sleep_time = 1
ingredient_limit = 75
recipe_generation_amount = 1

prompt_template = f'''
Using the provided list of ingredients, create {recipe_generation_amount} dinner recipe(s) in the following JSON format without any extra text:
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
    print("Connecting to the database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"Fetching the latest date for store: {store_name}")
    cursor.execute(
        "SELECT date_scraped FROM grocery_ingredients WHERE grocery_store = ? ORDER BY date_scraped DESC LIMIT 1",
        (store_name,)
    )
    latest_date = cursor.fetchone()[0]
    print(f"Latest date found: {latest_date}")

    print(f"Fetching ingredients for the latest date: {latest_date}")
    cursor.execute(
        f"SELECT grocery_ingredient, grocery_amount, grocery_cost FROM grocery_ingredients WHERE grocery_store = ? AND date_scraped = ? ORDER BY RANDOM() LIMIT {ingredient_limit}",
        (store_name, latest_date)
    )
    ingredients = cursor.fetchall()
    conn.close()
    print("Ingredients fetched from the database.")
    return [(ingredient, amount, f"${cost}") for ingredient, amount, cost in ingredients]

def validate_recipe(recipe):
    required_fields = ['title', 'description', 'serving_size', 'ingredients']
    for field in required_fields:
        if not recipe.get(field):
            return False
    for ingredient in recipe['ingredients']:
        if not all([ingredient.get('name'), ingredient.get('quantity'), ingredient.get('cost')]):
            return False
    return True

def generate_recipes(db_path, store_name, prompt_template, max_retries):
    tokenizer = LlamaTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer")
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1} to generate recipes...")

        # Fetch and randomize the ingredients for each attempt
        ingredients_list = fetch_latest_ingredients_from_db(db_path, store_name)

        print("Constructing the full prompt with ingredients list...")
        ingredients_text = "\n".join(f"{idx+1}. {name}, {quantity}, {cost}" for idx, (name, quantity, cost) in enumerate(ingredients_list))
        prompt = prompt_template.replace("Ingredients list:", f"Ingredients list:\n{ingredients_text}")

        # Tokenize and count tokens using LLaMA tokenizer
        # tokens = tokenizer(prompt)["input_ids"]
        # print(f"Token size of the prompt: {len(tokens)}")

        print("Writing prompt to a temporary file...")
        with open(prompt_file, "w") as f:
            json.dump({
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "keep_alive": 0
            }, f)

        command = ["curl", api_url, "-d", f"@{prompt_file}"]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print("AI endpoint called successfully.")
            full_response = result.stdout
            try:
                full_response_json = json.loads(full_response)
                response_json = full_response_json["response"]
                print("Parsing the response...")
                recipes = [json.loads(recipe) for recipe in response_json.split('\n\n') if recipe.strip()]
                validated_recipes = [recipe for recipe in recipes if validate_recipe(recipe)]
                if validated_recipes:
                    print("Recipes parsed successfully.")
                    return validated_recipes
                else:
                    print("No valid recipes found, retrying...")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        else:
            print(f"Error calling AI endpoint: {result.stderr}")

        print("Retrying...")
        time.sleep(sleep_time)  # Optionally add a delay between retries

    print("Failed to generate recipes after max retries.")
    return None

def insert_recipe_data(recipes, db_path, store_name):
    print("Connecting to the database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    current_date = datetime.date.today().strftime(date_format)

    for recipe in recipes:
        cursor.execute(
            "INSERT INTO recipes (recipe_title, recipe_description, recipe_serving_size, recipe_total_cost, recipe_date, recipe_store) VALUES (?, ?, ?, ?, ?, ?)",
            (recipe['title'], recipe['description'], recipe['serving_size'], sum(float(ingredient['cost'].replace('$', '')) for ingredient in recipe['ingredients']), current_date, store_name)
        )
        recipe_id = cursor.lastrowid
        for ingredient in recipe['ingredients']:
            cursor.execute(
                "INSERT INTO recipe_ingredients (recipe_id, recipe_ingredient, recipe_ingredient_amount, recipe_ingredient_cost) VALUES (?, ?, ?, ?)",
                (recipe_id, ingredient['name'], ingredient['quantity'], float(ingredient['cost'].replace('$', '')))
            )

    conn.commit()
    conn.close()
    print("Data inserted into the database.")

# Running Code
print("Generating recipes...")
recipes_output = generate_recipes(db_path, store_name, prompt_template, max_retries)
if recipes_output:
    print("Recipes generated successfully.")
    print(json.dumps(recipes_output, indent=2))
    # Insert the generated recipes into the database
    insert_recipe_data(recipes_output, db_path, store_name)
else:
    print("Failed to generate recipes.")
