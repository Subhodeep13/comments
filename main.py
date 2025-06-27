import streamlit as st
import datetime
import pandas as pd
from pymongo import MongoClient

# MongoDB setup
MONGO_URI = st.secrets["url"]
client = MongoClient(MONGO_URI)
db = client["comment_tracker"]
users_col = db["users"]

# Fetch all usernames
usernames = [u["name"] for u in users_col.find({}, {"name": 1})]

st.title("🔥 Knowledge Streak Tracker")

# Login / Register
st.header("🔑 Login / Register")
user_name = st.selectbox("Select your name", [""] + usernames)
custom_name = st.text_input("Or enter a new name")

# Prefer custom name if provided
if custom_name.strip():
    user_name = custom_name.strip()

submit = st.button("Login")

if submit and user_name:
    now = datetime.datetime.now()

    # Fetch or create user
    user_data = users_col.find_one({"name": user_name})
    if not user_data:
        user_data = {
            "name": user_name,
            "streak": 0,
            "last_commented": None,
            "total_days": 0
        }
        users_col.insert_one(user_data)

    # Handle datetime conversion
    last = user_data.get("last_commented")
    if last and isinstance(last, datetime.date) and not isinstance(last, datetime.datetime):
        last = datetime.datetime.combine(last, datetime.time.min)

    if last:
        elapsed = (now - last).total_seconds() / 3600
        if elapsed > 32:
            user_data["streak"] = 0
            st.warning("⛔️ Streak reset — more than 32 hours since last comment.")

    # Save session
    st.session_state.user_name = user_name
    st.session_state.user_data = user_data
    st.success(f"Jai Gurudev, {user_name}! 🙏")

# Helper: Progress Bar Display
def show_progress(user_data):
    st.subheader("🔥 Your Streak Progress")
    st.metric("Current Streak", f"{user_data['streak']} day(s)")

    next_reward = 90
    current_in_cycle = user_data['streak'] % next_reward
    days_to_next = next_reward - current_in_cycle if current_in_cycle != 0 else 0
    progress = current_in_cycle / next_reward
    st.progress(progress, text=f"{current_in_cycle} days done, {days_to_next} days to next Honour 🎖️")

    if days_to_next == 0 and user_data['streak'] != 0:
        st.balloons()
        st.success("💥 3-Month Honour Achieved! Keep it going!")

# Logged-in Section
if "user_name" in st.session_state:
    user_name = st.session_state.user_name
    user_data = st.session_state.user_data
    now = datetime.datetime.now()

    st.header("📌 Log Today’s Comment")

    last = user_data.get("last_commented")
    if last and isinstance(last, datetime.date) and not isinstance(last, datetime.datetime):
        last = datetime.datetime.combine(last, datetime.time.min)

    # Comment rules
    can_comment = True
    if last:
        elapsed = (now - last).total_seconds() / 3600
        if elapsed < 7:
            st.info("🕒 You've already logged a comment in the last 7 hours!")
            can_comment = False
        elif elapsed > 32:
            st.warning("⛔️ Streak broken after 32 hours.")
            user_data['streak'] = 0
            can_comment = True

    if can_comment:
        if st.button("✅ Yes, I commented now!"):
            user_data['streak'] = user_data['streak'] + 1 if last and elapsed <= 32 else 1
            user_data['total_days'] += 1
            user_data['last_commented'] = now

            # Save to MongoDB
            users_col.update_one(
                {"name": user_name},
                {"$set": {
                    "streak": user_data['streak'],
                    "total_days": user_data['total_days'],
                    "last_commented": user_data['last_commented']
                }}
            )

            st.success("🎉 Comment logged successfully!")
            show_progress(user_data)
    else:
        show_progress(user_data)

    # Extra badges (coming soon)
    if user_data["streak"] >= 60:
        st.info("🌟 You're approaching Acharya level! A surprise awaits at 90! 🎁")

    # Motivation
    st.subheader("🌱 Why Keep Commenting?")
    st.markdown("""
    - 🧘 Stay immersed in knowledge  
    - ✨ Show up daily to build your presence  
    - 🏅 Earn honours every 3 months  
    - 🔥 Ride the adrenaline rush of a burning streak  
    """)
    st.info("“As Gurudev always says — Be busy in spreading knowledge. Day and night think of how you can reach out to people, and do some good work in life.”")

    # Leaderboard
    st.subheader("🏆 Top Streaks")
    leaderboard = list(users_col.find({}, {"_id": 0}))
    leaderboard = sorted(leaderboard, key=lambda x: x['streak'], reverse=True)
    df = pd.DataFrame(leaderboard)[["name", "streak", "total_days"]]
    df.columns = ["Name", "Streak", "Total Days"]
    st.table(df.head(5))
