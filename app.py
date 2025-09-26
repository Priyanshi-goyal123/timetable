# from flask import Flask, render_template, request, redirect, url_for
# import json
# import os
# import datetime

# app = Flask(__name__)
# DATA_FILE = "userdata.json"

# # Load all users from JSON
# def load_users():
#     if os.path.exists(DATA_FILE):
#         try:
#             with open(DATA_FILE, "r") as f:
#                 return json.load(f)
#         except json.JSONDecodeError:
#             # If JSON is empty or corrupted, reset it
#             with open(DATA_FILE, "w") as f:
#                 f.write("{}")
#             return {}
#     return {}


# # Save all users to JSON
# def save_users(users):
#     with open(DATA_FILE, "w") as f:
#         json.dump(users, f, indent=4)

# # Generate timetable logic (6 hours, alternate study/hobbies)
# def generate_timetable(college_time, hobbies, day):
#     start_time = college_time[day]["start"]
#     end_time = college_time[day]["end"]

#     start = datetime.datetime.strptime(start_time, "%H:%M")
#     end = datetime.datetime.strptime(end_time, "%H:%M")
    
#     timetable = []
#     total_hours = 6  # Fixed 6 hours per day

#     for i in range(total_hours):
#         if i % 2 == 0 and hobbies:
#             activity = hobbies[i % len(hobbies)]
#         else:
#             activity = "Study"
#         hour_label = (start + datetime.timedelta(hours=i)).strftime("%H:%M")
#         timetable.append(f"{hour_label} - {activity}")
#     return timetable

# # Home route -> Login / Registration
# @app.route("/", methods=["GET", "POST"])
# def login():
#     message = ""
#     if request.method == "POST":
#         username = request.form["username"].strip()
#         password = request.form["password"].strip()
#         users = load_users()

#         if username in users:
#             # Existing user -> check password
#             if users[username]["password"] == password:
#                 return redirect(url_for("hobbies", username=username))
#             else:
#                 message = "Incorrect password!"
#         else:
#             # New user -> register
#             users[username] = {"password": password}
#             save_users(users)
#             return redirect(url_for("hobbies", username=username))
#     return render_template("login.html", message=message)

# # Hobbies input page
# @app.route("/hobbies/<username>", methods=["GET", "POST"])
# def hobbies(username):
#     users = load_users()
#     if request.method == "POST":
#         hobbies = request.form["hobbies"].split(",")
#         hobbies = [h.strip().title() for h in hobbies if h.strip()]
#         users[username]["hobbies"] = hobbies
#         save_users(users)
#         return redirect(url_for("college_time", username=username))
#     existing_hobbies = users[username].get("hobbies", [])
#     return render_template("hobbies.html", username=username, existing_hobbies=existing_hobbies)

# # College timings input page
# @app.route("/college_time/<username>", methods=["GET", "POST"])
# def college_time(username):
#     users = load_users()
#     days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

#     if request.method == "POST":
#         college_time = {}
#         for day in days:
#             start = request.form[f"{day}_start"]
#             end = request.form[f"{day}_end"]
#             college_time[day] = {"start": start, "end": end}
#         users[username]["college_time"] = college_time
#         save_users(users)
#         return redirect(url_for("timetable", username=username))

#     existing_times = users[username].get("college_time", {})
#     return render_template("college_time.html", username=username, days=days, existing_times=existing_times)

# # Timetable display page
# @app.route("/timetable/<username>", methods=["GET", "POST"])
# def timetable(username):
#     users = load_users()
#     days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#     selected_day = request.form.get("day") if request.method == "POST" else "Monday"

#     timetable_data = generate_timetable(users[username]["college_time"], users[username]["hobbies"], selected_day)
#     return render_template("timetable.html", username=username, days=days, selected_day=selected_day, timetable=timetable_data)

# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "replace_this_with_a_real_secret")

# Use the same filename you mentioned (userdata.json)
USERS_FILE = "userdata.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _stored_password_for(users, username):
    """Handle two possible storage shapes:
       - users[username] == {"password": "<b64>"} (preferred)
       - users[username] == "<b64>" (older/simple)
    """
    val = users.get(username)
    if isinstance(val, dict):
        return val.get("password", "")
    if isinstance(val, str):
        return val
    return ""


def generate_timetable(college_start="09:00", college_end="15:00", study_start="16:00", subjects=None, hobby="Hobby"):
    """
    Create hourly slots from study_start (inclusive) up to 22:00.
    First slot = hobby (all days). Next slots assign subjects in order; if subjects run out,
    remaining slots labelled "Self-study / Revision".
    Returns list of tuples: (time_label, [activity_for_Mon,...Sun])
    """
    if subjects is None or len(subjects) == 0:
        subjects = ["Subject1", "Subject2", "Subject3"]

    fmt = "%H:%M"
    try:
        start = datetime.strptime(study_start, fmt)
    except Exception:
        start = datetime.strptime("16:00", fmt)

    end_of_day = datetime.strptime("22:00", fmt)
    if start >= end_of_day:
        # fallback to 16:00 if study_start is invalid
        start = datetime.strptime("16:00", fmt)

    slots = []
    cursor = start
    while cursor < end_of_day:
        slot_end = cursor + timedelta(hours=1)
        time_label = f"{cursor.strftime(fmt)} - {slot_end.strftime(fmt)}"
        slots.append(time_label)
        cursor = slot_end

    timetable = []
    for idx, slot in enumerate(slots):
        if idx == 0:
            activity = f"Hobby: {hobby}"
        else:
            subj_index = idx - 1
            if subj_index < len(subjects):
                activity = subjects[subj_index]
            else:
                activity = "Self-study / Revision"
        # Same activity across all 7 days (can be extended later)
        timetable.append((slot, [activity] * 7))

    return timetable


@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("timetable_page"))
    return redirect(url_for("login_page"))


# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login_page():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        users = load_users()
        if username in users:
            stored_b64 = _stored_password_for(users, username)
            try:
                stored_pass = base64.b64decode(stored_b64).decode()
            except Exception:
                stored_pass = ""
            if stored_pass == password:
                session["user"] = username
                return redirect(url_for("timetable_page"))
            else:
                message = "Incorrect password!"
        else:
            message = "User not found!"
    return render_template("login.html", message=message)


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register_page():
    message = ""
    if request.method == "POST":
        username = request.form.get("regUsername", "").strip()
        password = request.form.get("regPassword", "").strip()
        if not username or not password:
            message = "Provide both username and password."
        else:
            users = load_users()
            if username in users:
                message = "User already exists!"
            else:
                # Save as a dict with a 'password' key for future fields
                users[username] = {"password": base64.b64encode(password.encode()).decode()}
                save_users(users)
                return redirect(url_for("login_page"))
    return render_template("register.html", message=message)


# ---------- TIMETABLE ----------
@app.route("/timetable", methods=["GET", "POST"])
def timetable_page():
    if "user" not in session:
        return redirect(url_for("login_page"))
    username = session["user"]
    users = load_users()
    user_data = users.get(username, {})
    # if user_data is a string (old style), convert to dict so we can store fields
    if isinstance(user_data, str):
        user_data = {}

    # Defaults
    college_start = user_data.get("college_start", "09:00")
    college_end = user_data.get("college_end", "15:00")
    study_start = user_data.get("study_start", "16:00")
    hobby = user_data.get("hobby", "Hobby")
    subjects = user_data.get("subjects", ["Subject1", "Subject2", "Subject3"])

    if request.method == "POST":
        college_start = request.form.get("collegeStart", college_start)
        college_end = request.form.get("collegeEnd", college_end)
        study_start = request.form.get("studyStart", study_start)
        hobby = request.form.get("hobby", hobby)
        subjects_input = request.form.get("subjects", "")
        subjects = [s.strip() for s in subjects_input.split(",") if s.strip()]

        users.setdefault(username, {})
        users[username]["college_start"] = college_start
        users[username]["college_end"] = college_end
        users[username]["study_start"] = study_start
        users[username]["hobby"] = hobby
        users[username]["subjects"] = subjects
        save_users(users)

    timetable_data = generate_timetable(college_start, college_end, study_start, subjects, hobby)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return render_template(
        "timetable.html",
        username=username,
        timetable=timetable_data,
        college_start=college_start,
        college_end=college_end,
        study_start=study_start,
        hobby=hobby,
        subjects=subjects,
        days=days
    )


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login_page"))


# ------------------ RUN ------------------ #
if __name__ == "__main__":
    app.run(debug=True)
