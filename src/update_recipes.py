import os
import sqlite3
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API credentials
load_dotenv()
app_id = os.getenv("EDAMAM_APP_ID")
app_key = os.getenv("EDAMAM_APP_KEY")

if not app_id or not app_key:
    raise ValueError("Missing EDAMAM API credentials in .env file")

# Connect to existing SQLite database
DB_PATH = "db/meal_planner.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Load all existing URIs to avoid duplicates
cursor.execute("SELECT uri FROM recipes")
existing_uris = set([row[0] for row in cursor.fetchall()])

# API request setup
url = "https://api.edamam.com/api/recipes/v2?type=public"
params = {
    "q": "food",
    "app_id": app_id,
    "app_key": app_key
}

recipes = []
seen_uris = set()

# Fetch recipes until 10 new unique ones are found
while len(recipes) < 10:
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(" API error:", response.status_code)
        break

    data = response.json()
    hits = data.get("hits", [])
    print(f"→ Received {len(hits)} recipes")

    for hit in hits:
        recipe = hit["recipe"]
        uri = recipe["uri"]

        if uri in existing_uris or uri in seen_uris:
            continue
        seen_uris.add(uri)

        nutrients = recipe.get("totalNutrients", {})
        recipes.append({
            "uri": uri,
            "title": recipe["label"],
            "type": ", ".join(recipe.get("mealType", [])),
            "diet": ", ".join(recipe.get("dietLabels", [])),
            "ingredients": "; ".join(recipe.get("ingredientLines", [])),
            "instructions": recipe["url"],
            "calories": round(recipe.get("calories", 0), 2),
            "protein": round(nutrients.get("PROCNT", {}).get("quantity", 0), 2),
            "fat": round(nutrients.get("FAT", {}).get("quantity", 0), 2),
            "carbs": round(nutrients.get("CHOCDF", {}).get("quantity", 0), 2)
        })

        if len(recipes) >= 10:
            break

    # Go to next page (pagination)
    next_url = data.get("_links", {}).get("next", {}).get("href")
    if not next_url:
        print(" No more pages available from API")
        break
    url = next_url
    params = {}  # next_url already includes all params

# Save to database
df = pd.DataFrame(recipes)

for _, row in df.iterrows():
    cursor.execute('''
                INSERT OR IGNORE INTO recipes (uri, title, type, diet, ingredients, instructions, calories, protein, fat, carbs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row['uri'], row['title'], row['type'], row['diet'], row['ingredients'], row['instructions'],
                  row['calories'], row['protein'], row['fat'], row['carbs']))

conn.commit()
conn.close()

print(f"Added {len(df)} new recipes to the database.")
