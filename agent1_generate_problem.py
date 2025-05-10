from dotenv import load_dotenv
import os
import pandas as pd
import google.generativeai as genai
import json

# Load .env file
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Load CSV file
def load_problems(csv_file):
    return pd.read_csv(csv_file)

# Select a problem with AI
def pick_problem_with_ai(df, prev_difficulty="Easy", recent_tags=["Array", "Math"]):
    problems_data = df[["Title", "Difficulty", "Question Type", "Leetcode Question Link"]].to_dict(orient="records")[:30]

    prompt = f"""
You are an AI tutor that helps learners practice DSA.

Here is a list of LeetCode problems:
{problems_data}

The student recently solved a {prev_difficulty} problem.
Don't pick another Easy if the last was Easy.
If the last problem was Hard and they failed, suggest Medium.
Try to vary topics if possible. Avoid repeating the same tag (e.g., 'Array') if seen recently: {recent_tags}

Pick one appropriate problem and provide:
- Problem title
- Difficulty
- Link
- 1-sentence reason for the choice
"""
    response = model.generate_content(prompt)
    return response.text

# Save structured info to JSON
def save_selected_problem(problem_title, problem_link, prev_difficulty, recent_tags, user_behavior, reason):
    data = {
        "Title": problem_title,
        "Leetcode Question Link": problem_link,
        "Previous Difficulty": prev_difficulty,
        "Recent Tags": recent_tags,
        "User Behavior": user_behavior,
        "Reason": reason
    }
    with open("selected_problem.json", "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    df = load_problems("leetcode_question.csv")
    ai_response = pick_problem_with_ai(df, prev_difficulty="Hard", recent_tags=["Array", "String"])

    # Example parse (you can improve this with regex/LLM parsing)
    problem_title = "Add Two Numbers"
    problem_link = "https://leetcode.com/problems/add-two-numbers"
    reason = "Varies topic and eases difficulty after a failed hard problem."
    user_behavior = "skipped"

    save_selected_problem(problem_title, problem_link, "Hard", ["Array", "String"], user_behavior, reason)
    print("✅ Agent 1 saved problem to JSON")