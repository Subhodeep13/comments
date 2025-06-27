
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
    user_data = users_col.find_one({"name": user_name})

    if not user_data:
        user_data = {
            "name": user_name,
            "streak": 0,
            "last_commented": None,
            "total_days": 0
        }
        users_col.insert_one(user_data)

    last = user_data["last_commented"]
    if last and isinstance(last, datetime.date) and not isinstance(last, datetime.datetime):
        last = datetime.datetime.combine(last, datetime.time.min)

    if last:
        elapsed = (now - last).total_seconds() / 3600
        if elapsed > 32:
            user_data["streak"] = 0
            st.warning("⚠️ Streak broken! More than 32 hours since last comment.")

    st.session_state.user_name = user_name
    st.session_state.user_data = user_data
    st.success(f"Jai Gurudev, {user_name}! 🙏")

# Logged in UI
if "user_name" in st.session_state:
    user_name = st.session_state.user_name
    user_data = st.session_state.user_data
    now = datetime.datetime.now()

    st.header("📌 Log Today’s Comment")

    last = user_data["last_commented"]
    if last and isinstance(last, datetime.date) and not isinstance(last, datetime.datetime):
        last = datetime.datetime.combine(last, datetime.time.min)

    can_comment = True
    if last:
        elapsed = (now - last).total_seconds() / 3600
        if elapsed < 7:
            st.info("🕒 You already logged a comment in the last 7 hours!")
            can_comment = False
        elif elapsed > 32:
            st.warning("⛔️ Streak broken after 32 hours.")
            user_data["streak"] = 0

    if can_comment:
        if st.button("✅ Yes, I commented now!"):
            user_data["streak"] = user_data["streak"] + 1 if last and elapsed <= 32 else 1
            user_data["total_days"] += 1
            user_data["last_commented"] = now

            users_col.update_one(
                {"name": user_name},
                {"$set": {
                    "streak": user_data["streak"],
                    "total_days": user_data["total_days"],
                    "last_commented": user_data["last_commented"]
                }}
            )

            st.success("🎉 Comment logged successfully!")

    # Progress
    streak = user_data["streak"]
    st.subheader("🔥 Your Streak Progress")
    st.metric("Current Streak", f"{streak} day(s)")

    # Milestones
    milestones = [
        (1, "🔰 Seeker"),
        (5, "💪 Consistent"),
        (15, "⚔️ Warrior"),
        (30, "🙏 Devotee"),
        (45, "🕯️ Light Bearer"),
        (60, "🏆 Acharya 🎁 Surprise!")
    ]

    # Next milestone
    next_milestone = None
    for m in milestones:
        if streak < m[0]:
            next_milestone = m
            break

    if next_milestone:
        target, badge_name = next_milestone
        prev = 0
        for m in reversed(milestones):
            if m[0] < target and streak >= m[0]:
                prev = m[0]
                break
        steps_done = streak - prev
        steps_total = target - prev
        progress = steps_done / steps_total
        st.progress(progress, text=f"{steps_done}/{steps_total} Days to {badge_name}")
    else:
        st.success("🏆 You’ve unlocked all badges!")
        st.balloons()

    # Badges
    st.subheader("🎖️ Your Badges")
    badge_display = ""
    for day, title in milestones:
        if streak >= day:
            badge_display += f"✅ **{title}** — Unlocked\n\n"
        else:
            badge_display += f"🔒 {title} — {day - streak} day(s) to go\n\n"
    st.markdown(badge_display)

    if streak >= 60:
        st.success("🎊 You've reached the **Acharya Badge**! Surprise coming soon!")

    # Motivation
    st.subheader("🌱 Why Keep Commenting?")
    st.markdown("""
    - 💡 Keep learning fresh every day  
    - 🔥 Ride the thrill of a growing streak  
    - 🏅 Earn visual rewards as you grow  
    - 🎯 Acharya badge unlocks a special surprise  
    """)
    st.info("“As Gurudev always says — Be busy in spreading knowledge. Day and night think of how you can reach out to people, and do some good work in life.”")

    # Leaderboard
    st.subheader("🏆 Top 5 Streak Holders")
    leaderboard = list(users_col.find({}, {"_id": 0}))
    leaderboard = sorted(leaderboard, key=lambda x: x['streak'], reverse=True)
    df = pd.DataFrame(leaderboard)[["name", "streak", "total_days"]]
    df.columns = ["Name", "Streak", "Total Days"]
    st.table(df.head(5))
