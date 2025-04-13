import streamlit as st
import requests
import json
import pandas as pd
from typing import List, Dict, Any
import time

# API endpoint configuration
API_URL = "http://127.0.0.1:8000"

# Initialize session state for storing generated meal plan
if "meal_plan_data" not in st.session_state:
    st.session_state.meal_plan_data = None

# if "user_id" not in st.session_state:
#     st.session_state.user_id = 1  # Default user ID

#
def display_meal_plan(meal_plan_data):
    """Display the meal plan based on the provided data structure"""
    
    try:
        if not isinstance(meal_plan_data, dict):
            # Try to convert from string if needed
            if isinstance(meal_plan_data, str):
                if meal_plan_data.startswith("```json"):
                    json_string = meal_plan_data[7:-3]
                else:
                    json_string = meal_plan_data
                
                meal_plan_data = json.loads(json_string)
            else:
                st.error("Invalid meal plan data format")
                return
        
        # Display header
        st.subheader("🧑‍🍳 Your Personalized Meal Plan")
        
        # Display general advice if available
        if "general_advice" in meal_plan_data:
            st.info(meal_plan_data["general_advice"])
        
        # Display dietary accommodations if available
        if "dietary_accommodations" in meal_plan_data and meal_plan_data["dietary_accommodations"]:
            st.markdown("<h4><b>🥗 Dietary Accommodations</b></h4>", unsafe_allow_html=True)
            with st.expander("View advices", expanded=True):
                for diet_type, description in meal_plan_data["dietary_accommodations"].items():
                    st.markdown(f"**{diet_type}**: {description}")
        
        # Display health considerations if available
        if "health_condition_considerations" in meal_plan_data and meal_plan_data["health_condition_considerations"]:
            st.markdown("<h4><b>❤️ Health Considerations</b></h4>", unsafe_allow_html=True)
            with st.expander("View advices", expanded=True):
                for condition, details in meal_plan_data["health_condition_considerations"].items():
                    st.markdown(f"**{condition}**: {details}")
        
        # Display daily meal plans
        daily_plans = meal_plan_data.get("meal_plan", [])
        
        for day_plan in daily_plans:
            day_num = day_plan.get("day", 0)
            meals = day_plan.get("meals", [])
            daily_advice = day_plan.get("daily_advice", "")
            
            st.markdown(f"<h4><b>📅 Day {day_num}</b></h4>", unsafe_allow_html=True)
            with st.expander(f"View meals", expanded=day_num == 1):
                
                
                # Display daily advice if available
                if daily_advice:
                    st.info(daily_advice)
                
                # Display each meal
                for meal in meals:
                    meal_name = meal.get("name", "")
                    foods = meal.get("foods", [])
                    
                    st.markdown(f"#### {meal_name}")
                    
                    # Process each food item
                    for food in foods:
                        if isinstance(food, dict):
                            food_name = food.get("name", "")
                            portion = food.get("portion_size", "")
                            preparation = food.get("preparation", "")
                            
                            with st.container():
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.markdown(f"**{food_name}**")
                                
                                with col2:
                                    st.markdown(f"*{portion}*")
                                
                                if preparation:
                                    st.markdown(f"*Preparation:* {preparation}")
                                
                                
                        else:
                            st.markdown(f"- {food}")
                    
                    st.markdown("---")
        
        # Divider at the end
        st.markdown("---")
    
    except Exception as e:
        st.error(f"Error displaying meal plan: {str(e)}")
        st.write("Raw meal plan data:")
        st.write(meal_plan_data)


def save_meal_plan():
    """Save the meal plan to the database through FastAPI"""
    if not st.session_state.meal_plan_data:
        st.error("No meal plan to save")
        return
    
    with st.spinner("Saving your meal plan..."):
        try:
            payload = {
                "user_id": st.session_state.user_id,
                "meal_plan": str(st.session_state.meal_plan_data)
            }
            
            response = requests.post(f"{API_URL}/save-meal-plan", json=payload)
            
            if response.status_code == 200:
                st.success("✅ Meal plan saved successfully!")
                st.balloons()
            else:
                st.error(f"❌ Error saving meal plan: {response.json().get('detail', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"⚠️ Error connecting to server: {str(e)}")


# Main app
st.set_page_config(page_title="Personalized Meal Planner", layout="wide")
st.title("🍽️ Personalized Meal Planner")
st.markdown("<h1 style='font-size:30px'>🌮🌯🥗🍣🍜🍝🍱🥝🥑🥥🍳</h1>", unsafe_allow_html=True)

if "user_id" in st.session_state:
    user_id = st.session_state["user_id"]


        
    # Function to fetch user data
    def fetch_user_data(user_id):
        response = requests.get(f"{API_URL}/get-user-data/{user_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None

    # Assuming `st.session_state.user_id` is already set
    user_id = st.session_state.user_id

    # Initialize session state for editable mode if it doesn't exist
    if 'editable' not in st.session_state:
        st.session_state.editable = False

    # Fetch user data from the backend (if available)
    user_data = fetch_user_data(user_id)
    print("User_data............................", user_data)

    # If no user data is returned, display a friendly message and allow the user to fill in their profile
    if not user_data:
        st.session_state.editable = True
        st.warning("It seems like you're using the app for the first time! Please fill out your profile.")
        user_data = {
            "number_of_days": '1',  # default value
            "health_conditions": "",
            "dietary_preferences": [],
            "allergies": "",
            "nutritional_goals": [],
            "food_preferences": "",
        }

    # Function to toggle edit mode
    def toggle_edit_mode():
        st.session_state.editable = not st.session_state.editable
        
    # Input form
    with st.form("meal_plan_form"):
        st.subheader("🩺 Your Health Profile")
        with st.expander("View details", expanded=st.session_state.editable):

            col1, col2 = st.columns(2)
            
            with col1:
                # Pre-fill form fields with either the existing data or default values
                number_of_days = st.selectbox(
                    "How many days of meals do you want?", 
                    options=["1", "3", "5", "7"], 
                    index=["1", "3", "5", "7"].index(user_data['number_of_days']) if user_data['number_of_days'] else 0,
                    disabled=not st.session_state.editable  # Make it editable based on session state
                )
                
                health_conditions = st.text_input(
                    "Health conditions (comma-separated)", 
                    placeholder="Do you have any special condition? e.g., diabetes, heart disease", 
                    value=user_data['health_conditions'] if user_data['health_conditions'] else "",
                    disabled=not st.session_state.editable  # Make it editable based on session state
                )
                
                dietary_preferences = st.multiselect(
                    "Dietary Preferences",
                    options=["Vegetarian", "Vegan", "Pescatarian", "Keto", "Paleo", "Mediterranean", "None"],
                    default=user_data['dietary_preferences'] if user_data['dietary_preferences'] else ["None"],
                    disabled=not st.session_state.editable  # Make it editable based on session state
                )
            
            with col2:
                allergies = st.text_input(
                    "Allergies", 
                    placeholder="e.g., shellfish, peanuts", 
                    value=user_data['allergies'] if user_data['allergies'] else "",
                    disabled=not st.session_state.editable  # Make it editable based on session state
                )
                
                nutritional_goals = st.multiselect(
                    "Nutritional Goals",
                    options=["Weight Loss", "Weight Gain", "Muscle Building", "Low Sodium", "Low Sugar", "None"],
                    default=user_data['nutritional_goals'] if user_data['nutritional_goals'] else ["None"],
                    disabled=not st.session_state.editable  # Make it editable based on session state
                )
                
                food_preferences = st.text_area(
                    "Food Preferences", 
                    value=user_data['food_preferences'] if user_data['food_preferences'] else "",
                    disabled=not st.session_state.editable  # Make it editable based on session state
                )

            # Create a row of buttons at the bottom
            button_col1, button_col2 = st.columns(2)
            
            with button_col1:
                # Show the Save button (enabled only in edit mode)
                save_button = st.form_submit_button("Save Changes", disabled=not st.session_state.editable)
            
            with button_col2:
                # Show the Edit button (with different text based on edit mode)
                edit_button = st.form_submit_button(
                    "Cancel Edit" if st.session_state.editable else "Edit Profile",
                    type="secondary"
                )
            
            # Handle button clicks
            if save_button and st.session_state.editable:
                # Save the data to the backend (FastAPI)
                data_to_save = {
                    "user_id": user_id,
                    "number_of_days": number_of_days,
                    "health_conditions": health_conditions,
                    "dietary_preferences": ",".join(dietary_preferences),
                    "allergies": allergies,
                    "nutritional_goals": ",".join(nutritional_goals),
                    "food_preferences": food_preferences
                }

                print(data_to_save)
                
                # Send POST request to save the data
                try:
                    save_response = requests.post(f"{API_URL}/save-user-data", json=data_to_save)
                    save_response.raise_for_status()
                    st.success("Your information has been saved!")
                    # Reset editable mode after saving
                    st.session_state.editable = False
                    # Force a rerun to update the UI
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Error saving data: {e}")
                    
            if edit_button:
                # Toggle edit mode
                toggle_edit_mode()
                # Force a rerun to update the UI
                st.rerun()

    col1, col2 = st.columns([1, 1])
    with col1:
        generate_button = st.button("Generate Meal Plan")
    with col2:
        to_trending_button = st.button("View Trending Recipes")

    if to_trending_button:
        st.switch_page("pages/Trending.py")


    # Process form submission
    if generate_button:
        with st.spinner("Generating your personalized meal plan..."):
            # Clean up inputs
            health_conditions_list = [item.strip().lower() for item in health_conditions.split(",") if item.strip()]
            
            # Prepare payload
            payload = {
                "user_id": user_id,
                "number_of_days": number_of_days,
                "health_conditions": health_conditions,
                "dietary_preferences": str(dietary_preferences),
                "allergies": allergies,
                "nutritional_goals": str(nutritional_goals),
                "food_preferences": food_preferences
            }
            
            try:
                response = requests.post(f"{API_URL}/generate-meal-plan", json=payload)
                
                if response.status_code == 200:
                    response = response.json()
                    st.session_state.meal_plan_data = response.get("raw", response)
                    st.success("✅ Meal plan generated successfully!")
                else:
                    st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"⚠️ Could not connect to backend: {str(e)}")

    # Display meal plan section
    if st.session_state.meal_plan_data:
        st.markdown("---")
        display_meal_plan(st.session_state.meal_plan_data)
        
        # Save button
        col1, col2 = st.columns([1, 3])
        with col2:
            # User feedback section
            st.markdown("#### 😒 Not happy with the meal?")
            feedback = st.text_input("Give us your feedback and we will generate a new meal plan for you!",
                                    placeholder="e.g., 'less carbs', 'no meat', 'more spicy'")

            if st.button("Make new meal plan"):
                # # Send feedback to API and get new meal plan
                # st.session_state.meal = st.session_state.meal_plan_data
                # payload = {
                #     "feedback": feedback,
                #     "previous_meal": st.session_state.meal
                # }
                # response = requests.post(API_URL, json=payload)
                # st.session_state.meal = response.json()["meal"]
                # st.experimental_rerun()
                st.popover("This feature is not yet implemented. Please check back later!")

        with col1:
            if st.button("💾 Save Meal Plan"):
                save_meal_plan()

else:
    st.info("Log in or create an account to start your meal planner.")