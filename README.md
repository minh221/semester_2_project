Awesome, thanks for the detailed info! Here's a clean and comprehensive `README.md` for your GitHub repo:

---

# 🥗 AI-Powered Meal Planner App

A personalized meal planning app built with **Streamlit** (front end) and **FastAPI** (back end), designed to generate customized meal plans based on user health profiles and trending recipes. The system leverages AI agents and a dynamic knowledge base to continuously improve its suggestions.

---

## 🚀 Features

### 🔐 Login & Profile Management
- Users enter their **User ID** to log in.
- The app checks for existing profiles in the database.
  - If found: displays and allows editing.
  - If not found: prompts users to create and save a profile.

### 🧠 AI Meal Planner
- Users can generate a meal plan tailored to their **health conditions**.
- AI agents handle:
  - **Condition Analysis**: Check if condition-related nutrition info exists in the knowledge base.
  - **Knowledge Enrichment**: If not found, an agent searches the web, generates a Markdown file, and stores it in the knowledge base and DB.
  - **Plan Generation**: Another agent uses the gathered info to generate a structured meal plan.
- Future roadmap: feedback-based regeneration of plans.

### 🔥 Trending Recipes
- View trending recipes scraped from the web.
- Save favorite recipes to a personalized list or remove them.
- Connected to `recipes` and `favourites` tables in the database.

---

## 🗂️ Project Structure

```
src/
├── app.py                 # FastAPI app entry
├── meal_plan_crew/        # Agent for meal plan generation
├── search_crew/           # Agent for health condition info crawling
├── streamlit/              # Streamlit
│   └── pages    # SQLite database
│         └── Home Page.py       # Home page
│         └── Trending.py        # Trending page
│   └── Login Page.py    # SQLite database
├── update_recipes.py      # Trending recipes fetcher
├── db/
│   └── meal_planner.db    # SQLite database
├── knowledge/             # Markdown-based knowledge base
└── requirements.txt       # Python dependencies
```

---

## ⚙️ Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/meal-planner-app.git
   cd meal-planner-app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Usage

1. **Run the backend**
   ```bash
   uvicorn src.app:app --reload
   ```

2. **Launch the Streamlit UI**
   ```bash
   streamlit run src/streamlit/Login Page.py
   ```

---

## 🧠 Technologies Used

- **Streamlit** – Frontend framework
- **FastAPI** – API server
- **SQLite** – Lightweight database
- **Python Agents** – For knowledge enrichment & meal generation
- **Web scraping** – For trending recipe detection

---

## 📌 To-Do (Coming Soon)
- Allow feedback-based regeneration of meal plans.
- Add user authentication system.
- Improve UI/UX with more personalization options.

---

Let me know if you'd like to add badges, screenshots, or a deployment guide!
