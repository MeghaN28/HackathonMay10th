from dotenv import load_dotenv
import os
import pandas as pd
import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta
from difflib import get_close_matches
import time
import subprocess

# Load .env file for API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Load LeetCode CSV
def load_problems(csv_file):
    return pd.read_csv(csv_file)

def append_to_history(new_entry, filename="all_attempts.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(new_entry)

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_problem_link_by_title(title, df):
    titles = df["Title"].tolist()
    close = get_close_matches(title, titles, n=1, cutoff=0.6)
    if close:
        match = df[df["Title"] == close[0]].iloc[0]
        return match["Leetcode Question Link"], match["Title"], True
    return "https://leetcode.com", title, False

def check_revision_needed(attempts, df):
    today = datetime.now().date()
    for attempt in attempts:
        if attempt["Completed"] == "yes":
            try:
                date_solved = datetime.strptime(attempt["date_attempted"], "%Y-%m-%d").date()
                if (today - date_solved).days == 7:
                    # Ensure link exists, or try to find it
                    link = attempt.get("Leetcode Question Link", "").strip()
                    if not link:
                        link, matched_title, found = get_problem_link_by_title(attempt["Title"], df)
                        attempt["Title"] = matched_title
                        attempt["Leetcode Question Link"] = link
                    return attempt
            except:
                continue
    return None

def pick_problem_with_ai(df, prev_title, prev_difficulty, recent_tags, completed, date_attempted, all_attempts):
    # Check for revision priority
    revision_problem = check_revision_needed(all_attempts, df)
    if revision_problem:
        return json.dumps({
            "Title": revision_problem["Title"],
            "Difficulty": revision_problem["Difficulty"],
            "Link": revision_problem.get("Leetcode Question Link", "https://leetcode.com"),
            "Reason": "This problem is due for revision as it was solved exactly 7 days ago."
        }), True

    problems_data = df[["Title", "Difficulty", "Question Type", "Leetcode Question Link"]].to_dict(orient="records")[:30]

    prompt = f"""
You are an AI tutor designed to help a student practice Data Structures and Algorithms (DSA) on LeetCode.

The student recently attempted the LeetCode problem titled **"{prev_title}"** with difficulty **{prev_difficulty}**.
Completion status: **{completed}**.
Date: {date_attempted}.

### Guidelines for Selecting the Next Problem:
- If the last problem was **Easy** and **not completed**, suggest the **same or easier**.
- If **Medium** and **not completed**, suggest an **Easy or Medium** problem.
- If **Hard** and **not completed**, suggest a **Medium**.
- If completed, increase or maintain challenge level, staying within similar or varied topics.
- Avoid repeating tags: {recent_tags}

📚 Summary of Recent Attempts:
""" + "\n".join([
        f"- {a['Title']} ({a['Difficulty']}): {'Completed' if a['Completed'] == 'yes' else 'Skipped'} on {a['date_attempted']}"
        for a in all_attempts[-5:]
    ]) + """

🎯 Return result as:
{
    "Title": "<problem title>",
    "Difficulty": "<difficulty>",
    "Link": "<Leetcode link>",
    "Reason": "<1-sentence reason>"
}
ONLY return valid JSON.
"""

    response = model.generate_content(prompt)
    return response.text, False

def save_selected_problem(problem_title, problem_link, prev_difficulty, recent_tags, user_behavior, reason, is_revision=False, completed='no'):
    data = {
        "Title": problem_title,
        "Leetcode Question Link": problem_link,
        "Previous Difficulty": prev_difficulty,
        "Recent Tags": recent_tags,
        "User Behavior": user_behavior,
        "Reason": reason
    }
    if is_revision:
        data["Tag"] = "revision"
    if completed == 'no':
        data["Tag"] = data.get("Tag", "") + " not Complete"

    with open("selected_problem.json", "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    print("Did you solve Today's problem?")
    previous_title = input("Enter the problem you solved previously: ")
    prev_difficulty = input("Enter its difficulty (Easy/Medium/Hard): ")
    time_taken = input("How much time did you take (e.g., 30 mins): ")
    completed = input("Did you complete the problem? (yes/no): ").lower()
    recent_tags = input("Enter tags (comma-separated) for that problem: ").split(",")
    date_attempted = input("Enter the date (YYYY-MM-DD): ")

    previous_attempt = {
        "Title": previous_title,
        "Difficulty": prev_difficulty,
        "Time Taken": time_taken,
        "Completed": completed,
        "Tags": [tag.strip() for tag in recent_tags],
        "date_attempted": date_attempted
    }

    append_to_history(previous_attempt)
    print("📝 Saved previous attempt.")

    with open("all_attempts.json", "r") as f:
        all_attempts = json.load(f)

    df = load_problems("leetcode_question.csv")

    ai_response, is_revision = pick_problem_with_ai(
        df,
        prev_title=previous_attempt["Title"],
        prev_difficulty=previous_attempt["Difficulty"],
        recent_tags=previous_attempt["Tags"],
        completed=previous_attempt["Completed"],
        date_attempted=previous_attempt["date_attempted"],
        all_attempts=all_attempts
    )

    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            raise ValueError("No valid JSON found.")

        problem_title = parsed["Title"]
        problem_link = parsed["Link"]
        reason = parsed["Reason"]
        user_behavior = "skipped" if previous_attempt["Completed"] == "no" else "completed"

        save_selected_problem(
            problem_title,
            problem_link,
            previous_attempt["Difficulty"],
            previous_attempt["Tags"],
            user_behavior,
            reason,
            is_revision,
            completed
        )

        print("✅ Agent 1 saved problem to JSON")
        print(json.dumps(parsed, indent=4))

        print("⏳ Waiting 30 seconds before sending the email...")
        time.sleep(30)

        # Run the email-sending script
        print("📬 Triggering agent2_send_email.py...")
        subprocess.run(["python", "agent2_send_email.py"])

    except Exception as e:
        print("❌ Failed to parse AI response:", str(e))
        print("Raw response:\n", ai_response)
