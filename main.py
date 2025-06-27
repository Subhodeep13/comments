import streamlit as st
import datetime
import pandas as pd
from pymongo import MongoClient

# MongoDB setup
MONGO_URI = st.secrets["url"]
client = MongoClient(MONGO_URI)
db = client["comment_tracker"]
users_col = db["users"]

# Fetch usernames
usernames = [u["name"] for u in users_col.find({}, {"name": 1})]

st.title("🔥 Knowledge Streak Tracker")

# Login
st.header("🔑 Login / Register")
user_name = st.selectbox("Select your name", [""] + usernames)
custom_name = st.text_input("Or enter a new name")

if custom_name.strip():
    user_name = custom_name.strip()

submit = st.button("Login")

if submit and user_name:
    now = datetime.datetime.now()

    # Get or create user
    user_data = users_col.find_one({"name": user_name})
    if not user_data:
        user_data = {
            "name": user_name,
            "streak": 0,
            "last_commented": None,
            "total_days": 0
        }
        users_col.insert_one(user_data)

    # Convert date if needed
    last = user_data.get("last_commented")
    if last and isinstance(last, datetime.date) and not isinstance(last, datetime.datetime):
        last = datetime.datetime.combine(last, datetime.time.min)

    if last:
        elapsed = (now - last).total_seconds() / 3600
        if elapsed > 32:
            user_data["streak"] = 0
            st.warning("⛔️ Streak reset — more than 32 hours since last comment.")

    st.session_state.user_name = user_name
    st.session_state.user_data = user_data
    st.success(f"Jai Gurudev, {user_name}! 🙏")

# Show progress bar
def show_progress(user_data):
    st.subheader("🔥 Your Streak Progress")
    st.metric("Current Streak", f"{user_data['streak']} day(s)")

    # Next badge logic
    badge_days = [7, 21, 45, 60]
    next_badge = next((d for d in badge_days if d > user_data["streak"]), 60)
    days_done = user_data["streak"]
    days_to_next = max(next_badge - days_done, 0)
    progress = min(days_done / next_badge, 1.0)
    st.progress(progress, text=f"{days_done} days done, {days_to_next} to next badge 🎖️")

    if user_data["streak"] == 60:
        st.balloons()
        st.success("🎉 You are an Acharya now! Badge unlocked!")

# Show earned & upcoming badges
def show_badges(user_data):
    st.subheader("🏅 Your Badge Journey (Gen Z Edition)")

    badges = [
        {"label": "🧃 The Starter", "days": 7},
        {"label": "🔥 The Grinder", "days": 21},
        {"label": "🎧 The Viber", "days": 45},
        {"label": "🧘 The Acharya", "days": 60},
    ]

    earned = []
    upcoming = []

    for badge in badges:
        if user_data["streak"] >= badge["days"]:
            earned.append(f"✅ {badge['label']}")
        else:
            remaining = badge["days"] - user_data["streak"]
            upcoming.append(f"🔒 {badge['label']} — {remaining} day(s) left")

    if earned:
        st.markdown("### ✅ **Earned Badges**")
        for b in earned:
            st.markdown(f"- {b}")
    if upcoming:
        st.markdown("### 🔒 **Upcoming Badges**")
        for b in upcoming:
            st.markdown(f"- {b}")

# Logged in view
if "user_name" in st.session_state:
    user_name = st.session_state.user_name
    user_data = st.session_state.user_data
    now = datetime.datetime.now()

    st.header("📌 Log Today’s Comment")

    last = user_data.get("last_commented")
    if last and isinstance(last, datetime.date) and not isinstance(last, datetime.datetime):
        last = datetime.datetime.combine(last, datetime.time.min)

    # Logic to comment
    can_comment = True
    if last:
        elapsed = (now - last).total_seconds() / 3600
        if elapsed < 7:
            st.info("🕒 You already logged a comment in the last 7 hours!")
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
            show_badges(user_data)
    else:
        show_progress(user_data)
        show_badges(user_data)

    # Motivation
    st.subheader("🌱 Why Keep Commenting?")
    st.markdown("""
    - 🧘 Stay immersed in knowledge  
    - ✨ Show up daily to build your presence  
    - 🏅 Earn honours with every badge  
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
