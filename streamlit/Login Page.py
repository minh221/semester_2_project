import streamlit as st
import requests
import time

# API endpoint configuration
API_URL = "http://127.0.0.1:8000/check-user-exists"

# Check if user ID exists using FastAPI
def check_user_exists(user_id):
    try:
        response = requests.get(f'{API_URL}/{user_id}')
        if response.status_code == 200:
            data = response.json()
            return data.get("exists", False)
    except Exception as e:
        st.error(f"Error connecting to the FastAPI backend: {e}")
        return False

st.markdown(
        """
        <style>
            .title {
                font-size: 40px;
                color: black;
                font-weight: bold;
                text-align: center;
            }
            .subtitle {
                font-size: 25px;
                color: #555;
                text-align: center;
            }
            .description {
                font-size: 18px;
                color: #555;
                text-align: center;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Main app
def main():
    # Simple black title with emoji
    st.markdown('<div class="title">🐸 Welcome to the Meal Planner 🐸!</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">🥙🌮🥘🍨🍺🍹🍸🥃🥝🥭🥑🍏🍭🧁🥩</subtitle>', unsafe_allow_html=True)
    st.markdown('<div class="description">Please enter your User ID to get started.</div>', unsafe_allow_html=True)

    # Input field for User ID
    user_id = st.text_input("Enter your User ID:", placeholder="e.g., user123")

    if st.button("OK"):
        if user_id:
            # Check if the user ID exists in the database
            with st.spinner("Checking user details... We are taking you to the main app soon!"):
                time.sleep(2)  # Simulating the time delay for checking
                if check_user_exists(user_id):
                    # Set the session state user id
                    st.session_state.user_id = user_id
                    st.success(f"User ID {user_id} found. Redirecting to the main app...")

                    # Add a small spinner to simulate redirection
                    with st.spinner("Redirecting..."):
                        time.sleep(2)  

                else:
                    st.session_state.user_id = user_id
                    st.markdown(
                        "It looks like you're new to us. You will now enter your profile in the next step."
                    )
                    with st.spinner("Redirecting..."):
                        time.sleep(2)
            
            # Switch to the next page after validation
            st.switch_page("pages/Home Page.py")
        else:
            st.error("Please enter a User ID.")

if __name__ == "__main__":
    if "user_id" not in st.session_state:
        main()
    else:
        # Once the user is authenticated, show the main app content
        st.markdown(f'''<div class="title">🍹🍈 Welcome 🐸 {st.session_state.user_id}!</div>''', unsafe_allow_html=True)
        st.markdown('----')
        col1, col2 = st.columns([1,2])
        with col2:
            if st.button("✈ To Main App 🏍"):
                st.switch_page("pages/Home Page.py")
