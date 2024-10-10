import subprocess
import json

def generate_recipes(ingredients_list, prompt_template):
    # Construct the full prompt with ingredients list
    ingredients_text = "\n".join(f"{idx+1}. {name}, {quantity}, {cost}" for idx, (name, quantity, cost) in enumerate(ingredients_list))
    prompt = prompt_template.replace("Ingredients list:", f"Ingredients list:\n{ingredients_text}")

    # Use curl to call the AI endpoint with stream set to false
    command = [
        "curl", "http://172.30.1.6:11434/api/generate", "-d",
        json.dumps({
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        })
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        # Extract the "response" field from the JSON
        full_response = json.loads(result.stdout)
        response_json = full_response["response"]
        # Split the response into individual JSON objects and combine them into a list
        recipes = [json.loads(recipe) for recipe in response_json.split('\n\n') if recipe.strip()]
        return recipes
    else:
        return f"Error: {result.stderr}"

# Example ingredients list
ingredients_list = [
    ("Tomato", 5, "$2"),
    ("Onion", 3, "$1.5"),
    ("Garlic", 5, "$3"),
    ("Basil", 4, "$8"),
    ("Olive oil", 2, "$16"),
    ("Chicken breast", 12, "$36"),
    ("Pasta", 5, "$10"),
    ("Parmesan cheese", 3, "$15"),
    ("Bell pepper", 8, "$8"),
    ("Mushrooms", 6, "$12"),
    ("Ground beef", 10, "$30"),
    ("Carrots", 7, "$7"),
    ("Celery", 6, "$6"),
    ("Potatoes", 10, "$10"),
    ("Eggplant", 4, "$8"),
    ("Zucchini", 8, "$12"),
    ("Flour", 10, "$5"),
    ("Sugar", 5, "$4"),
    ("Eggs", 24, "$12"),
    ("Milk", 3, "$9"),
    ("Heavy cream", 2, "$8"),
    ("Butter", 4, "$8"),
    ("Salt", 2, "$3"),
    ("Black pepper", 1, "$5"),
    ("Cinnamon", 1, "$4"),
    ("Nutmeg", 1, "$5"),
    ("Vanilla extract", 2, "$10"),
    ("Honey", 2, "$14"),
    ("Yogurt", 10, "$10"),
    ("Blueberries", 5, "$20"),
    ("Strawberries", 5, "$15"),
    ("Bananas", 12, "$6"),
    ("Apples", 10, "$10"),
    ("Oranges", 10, "$10"),
    ("Spinach", 4, "$8"),
    ("Kale", 4, "$8"),
    ("Almonds", 2, "$12"),
    ("Walnuts", 2, "$14"),
    ("Chocolate chips", 3, "$9"),
    ("Bread", 5, "$20"),
    ("Pineapple", 3, "$12"),
    ("Broccoli", 5, "$7"),
    ("Cauliflower", 4, "$6"),
    ("Green beans", 6, "$8"),
    ("Lentils", 8, "$9"),
    ("Rice", 10, "$11"),
    ("Tuna", 4, "$16"),
    ("Shrimp", 2, "$18")
]

prompt_template = '''
Using the provided list of ingredients, create 3 different recipes in the following JSON format without any extra text:
{
  "title": "Recipe Title",
  "description": "Recipe Description",
  "ingredients": [
    {"name": "ingredient1", "quantity": "amount1", "cost": "cost1"},
    {"name": "ingredient2", "quantity": "amount2", "cost": "cost2"}
  ]
}

Ingredients list: 
'''

recipes_output = generate_recipes(ingredients_list, prompt_template)
print(json.dumps(recipes_output, indent=2))
