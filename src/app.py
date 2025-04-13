from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from search_crew.search_crew import SearchCrew
from meal_plan_crew.meal_crew import MealPlanCrew
from typing import List
from dotenv import load_dotenv
import uvicorn
import warnings
import json
from datetime import datetime

warnings.filterwarnings("ignore")
load_dotenv()

app = FastAPI()

# --- Setup SQLite ---
DB_PATH = "db/meal_planner.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create 'info_path' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS info_path (
            condition TEXT PRIMARY KEY,
            path TEXT NOT NULL
        )
    ''')

    # Create 'user_profile' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (  
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            health_conditions TEXT,
            dietary_preferences TEXT,
            allergies TEXT,
            nutritional_goals TEXT,
            food_preferences TEXT
        )
    ''')

    # Create 'meal_plans' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_plans (
            meal_plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            meal_plan_json TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user_profile(id)
        )
    ''')

    # Create 'favorites' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            recipe_id INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profile(id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
    ''')

    # Create 'recipes' table (fixing structure and adding correct column types)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uri TEXT,
            title TEXT NOT NULL,
            type TEXT,
            diet TEXT,
            ingredients TEXT,
            instructions TEXT,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL
        )
    ''')

    conn.commit()
    conn.close()

# Call the function to initialize the database
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

# --- Pydantic Model ---
class UserProfile(BaseModel):
    user_id: int
    number_of_days: str
    health_conditions: str  # comma-separated string
    dietary_preferences: str
    allergies: str
    nutritional_goals: str
    food_preferences: str

class RecipeBase(BaseModel):
    id: int
    title: str
    type: str
    diet: str
    ingredients: str
    instructions: str
    calories: float
    protein: float
    fat: float
    carbs: float

class FavoriteBase(BaseModel):
    user_id: int
    recipe_id: int

class FavoriteOut(BaseModel):
    user_id: int
    recipe_id: int
    added_at: str


class MealPlanRequest(BaseModel):
    user_id: str
    meal_plan: str


@app.get("/check-user-exists/{user_id}")
async def check_user_exists(user_id: int):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM user_profile WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return {"exists": True}
    else:
        return {"exists": False}

@app.get("/get-user-data/{user_id}")
async def get_user_data(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM user_profile WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user = dict(user)
    # Return the user data as a dictionary
    return {
        "number_of_days": '1',
        "health_conditions": user['health_conditions'],
        "dietary_preferences": user['dietary_preferences'].split(","),
        "allergies": user['allergies'],
        "nutritional_goals": user['nutritional_goals'].split(","),
        "food_preferences": user['food_preferences'],
    }

@app.post("/save-user-data")
def save_user_data(user_profile: UserProfile):
    conn = get_db_connection()
    cursor = conn.cursor()
    print("user_profile..................", user_profile)
    # Check if user already exists
    cursor.execute('SELECT * FROM user_profile WHERE id = ?', (user_profile.user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # Update existing user
        cursor.execute('''
            UPDATE user_profile 
            SET health_conditions = ?, dietary_preferences = ?, allergies = ?, nutritional_goals = ?, food_preferences = ?
            WHERE id = ?
        ''', (user_profile.health_conditions, user_profile.dietary_preferences, user_profile.allergies, user_profile.nutritional_goals, user_profile.food_preferences, user_profile.user_id,))
    else:
        # Insert new user
        cursor.execute('''
            INSERT INTO user_profile (id, health_conditions, dietary_preferences, allergies, nutritional_goals, food_preferences) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_profile.user_id, user_profile.health_conditions, user_profile.dietary_preferences, user_profile.allergies, user_profile.nutritional_goals, user_profile.food_preferences,))

    conn.commit()
    conn.close()

    return {"message": "User data saved successfully!"}


@app.get("/recipes/latest", response_model=List[RecipeBase])
def get_latest_recipes(limit: int = 5):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, type, diet, ingredients, instructions,
                   calories, protein, fat, carbs
            FROM recipes
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        recipes = [dict(row) for row in cursor.fetchall()]
        return recipes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

# Get recipe by ID
@app.get("/recipes/{recipe_id}", response_model=RecipeBase)
def get_recipe(recipe_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, type, diet, ingredients, instructions,
                   calories, protein, fat, carbs
            FROM recipes
            WHERE id = ?
        """, (recipe_id,))
        
        recipe = cursor.fetchone()
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return dict(recipe)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

# Get all favorites for a user (just the IDs)
@app.get("/favorites/user/{user_id}", response_model=List[dict])
def get_user_favorites(user_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT recipe_id, added_at
            FROM favorites
            WHERE user_id = ?
            ORDER BY added_at DESC
        """, (user_id,))
        
        favorites = [{"recipe_id": row["recipe_id"], "added_at": row["added_at"]} 
                     for row in cursor.fetchall()]
        return favorites
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

# Get all favorite recipes for a user (complete recipe details)
@app.get("/favorites/user/{user_id}/recipes", response_model=List[dict])
def get_user_favorite_recipes(user_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.title, r.type, r.diet, r.ingredients, r.instructions,
                   r.calories, r.protein, r.fat, r.carbs, f.added_at
            FROM favorites f
            JOIN recipes r ON f.recipe_id = r.id
            WHERE f.user_id = ?
            ORDER BY f.added_at DESC
        """, (user_id,))
        
        recipes = [dict(row) for row in cursor.fetchall()]
        return recipes
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

# Add a recipe to favorites
@app.post("/favorites/add")
def add_to_favorites(favorite: FavoriteBase):
    conn = get_db_connection()
    try:
        # Check if recipe exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (favorite.recipe_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Check if user exists
        cursor.execute("SELECT id FROM user_profile WHERE id = ?", (favorite.user_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already in favorites
        cursor.execute("""
            SELECT 1 FROM favorites 
            WHERE user_id = ? AND recipe_id = ?
        """, (favorite.user_id, favorite.recipe_id))
        
        if cursor.fetchone() is not None:
            return {"message": "Recipe already in favorites"}
        
        # Add to favorites
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO favorites (user_id, recipe_id, added_at)
            VALUES (?, ?, ?)
        """, (favorite.user_id, favorite.recipe_id, now))
        
        conn.commit()
        return {"message": "Added to favorites successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

# Remove a recipe from favorites
@app.delete("/favorites/remove")
def remove_from_favorites(favorite: FavoriteBase):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM favorites
            WHERE user_id = ? AND recipe_id = ?
        """, (favorite.user_id, favorite.recipe_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404, 
                detail="Favorite not found. Either it doesn't exist or was already removed."
            )
        
        conn.commit()
        return {"message": "Removed from favorites successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

# Search recipes by keyword
@app.get("/recipes/search/{keyword}", response_model=List[RecipeBase])
def search_recipes(keyword: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        search_term = f"%{keyword}%"
        cursor.execute("""
            SELECT id, title, type, diet, ingredients, instructions,
                   calories, protein, fat, carbs
            FROM recipes
            WHERE title LIKE ? OR ingredients LIKE ? OR diet LIKE ? OR type LIKE ?
            ORDER BY id DESC
        """, (search_term, search_term, search_term, search_term))
        
        recipes = [dict(row) for row in cursor.fetchall()]
        return recipes
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()



## ============================= CREWs ENDPOINT ============================= ##

# --- Retrieve or update knowledge source---
def get_or_create_knowledge_path(condition: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM info_path WHERE condition = ?", (condition,))
    row = cursor.fetchone()

    if row:
        path = row[0]
    else:
        # Run SearchCrew and assume it outputs a .md file
        SearchCrew().crew().kickoff(inputs={'health_condition': condition})
        path = f"/{condition}.md"
        cursor.execute("INSERT INTO info_path (condition, path) VALUES (?, ?)", (condition, path))
        conn.commit()

    conn.close()
    return path

# --- API Route ---
@app.post("/generate-meal-plan")
def generate_meal_plan(user_profile: UserProfile):
    try:
        # Step 1: Extract health conditions
        if not user_profile.health_conditions or user_profile.health_conditions == "none" or user_profile.health_conditions == "":
            health_conditions = 'none'
            knowledge_paths = None
        else:
            health_conditions = [hc.strip().lower() for hc in user_profile.health_conditions.split(',')]
            knowledge_paths = [get_or_create_knowledge_path(cond) for cond in health_conditions]

        # Step 3: Prepare input dict for MealPlanCrew
        input_dict = {
            "number_of_days": user_profile.number_of_days,
            "health_conditions": str(health_conditions),
            "dietary_preferences": user_profile.dietary_preferences,
            "allergies": user_profile.allergies,
            "nutritional_goals": user_profile.nutritional_goals,
            "food_preferences": user_profile.food_preferences,
        }

        # Step 4: Run MealPlanCrew and capture the result
        result = MealPlanCrew(knowledge_paths=knowledge_paths).crew().kickoff(inputs=input_dict)
        print(type(result))
        print(result)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# --- Save meal plan endpoint ---
@app.post("/save-meal-plan")
def save_meal_plan(data: MealPlanRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        meal_plan_json = json.dumps(data.meal_plan)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO meal_plans (user_id, created_at, meal_plan_json)
            VALUES (?, ?, ?)
        """, (data.user_id, created_at, meal_plan_json))
        
        conn.commit()
        conn.close()
        
        return {"message": "Meal plan saved successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)