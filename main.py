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

# Login with dropdown + text input
st.header("🔑 Login / Register")
user_name = st.selectbox("Select your name", [""] + usernames)
custom_name = st.text_input("Or enter a new name")

# Use new name if typed
if custom_name.strip():
    user_name = custom_name.strip()

submit = st.button("Login")

if submit and user_name:
    now = datetime.datetime.now()

    user_data = users_col.find_one({"name": user_name})
    if not user_data:
        user_data = {
            "name": user_name,
            "streak": 0,
            "last_commented": None,
            "total_days": 0
        }
        users_col.insert_one(user_data)

    # Fix datetime
    last = user_data.get('last_commented')
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

# Logged-in view
if "user_name" in st.session_state:
    user_name = st.session_state.user_name
    user_data = st.session_state.user_data
    now = datetime.datetime.now()

    st.header("📌 Log Today’s Comment")

    last = user_data.get("last_commented")
    if last and isinstance(last, datetime.date) and not isinstance(last, datetime.datetime):
        last = datetime.datetime.combine(last, datetime.time.min)

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

    if can_comment and st.button("✅ Yes, I commented now!"):
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

    # Progress Display
    st.subheader("🔥 Your Streak Progress")
    streak = user_data.get("streak", 0)
    st.metric("Current Streak", f"{streak} day(s)")

    # Tiers
    milestones = [
        (1, "🔰 Seeker"),
        (7, "🔥 Sadhak"),
        (21, "🌟 Yogi"),
        (45, "🧘‍♂️ Sevak"),
        (90, "🏅 Acharya"),
    ]

    next_tier = next(((days, label) for days, label in milestones if streak < days), None)

    if next_tier:
        next_days, next_label = next_tier
        days_remaining = next_days - streak
        progress = streak / next_days
        st.progress(progress, text=f"{streak}/{next_days} — {days_remaining} day(s) to {next_label}")

        if next_label == "🏅 Acharya":
            st.info("🎁 A surprise awaits you when you reach the Acharya level! 30 days Stay consistent 🙌")
    else:
        st.balloons()
        st.success("💥 You've reached the final tier — Acharya! Keep shining!")
        st.markdown("🎉 **You’ve unlocked the surprise! Check your inbox or await a special message soon!** ✨")

    # Motivation
    st.subheader("🌱 Why Keep Commenting?")
    st.markdown("""
    - 🧘 Stay immersed in knowledge  
    - ✨ Show up daily to build your presence  
    - 🏅 Earn honours every 3 months  
    - 🎁 Surprise awaits at Acharya level  
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
