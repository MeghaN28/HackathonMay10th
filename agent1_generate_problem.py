from dotenv import load_dotenv
import os
import pandas as pd
import google.generativeai as genai
import json
import re

# Load .env file for API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Load LeetCode CSV
def load_problems(csv_file):
    return pd.read_csv(csv_file)

# Ask Gemini for next problem based on previous attempt

def pick_problem_with_ai(df, prev_title, prev_difficulty, recent_tags, completed):
    print(completed)
    problems_data = df[["Title", "Difficulty", "Question Type", "Leetcode Question Link"]].to_dict(orient="records")[:30]

    prompt = f"""
    You are an AI tutor designed to help a student practice Data Structures and Algorithms (DSA) on LeetCode.

    The student has recently attempted the LeetCode problem titled **"{prev_title}"** with difficulty **{prev_difficulty}**. 

    The completion status of the problem is: **{completed}** (indicating whether the problem was solved successfully or not).

    ### Guidelines for Selecting the Next Problem:
    - If the last problem was **Easy** and the student **did not complete it**, recommend the **same problem again** or suggest an **easier** or **same difficulty** problem of the same type.
    - If the last problem was **Medium** and the student **did not complete it**, recommend an **Easy or Medium** problem of the same type (tag/topic) or a similar type.
    - If the last problem was **Hard** and the student **did not complete it**, suggest a **Medium** problem, preferably of a different type.

    - If the last problem was **Easy** and the student **completed it**, suggest a **new Medium** problem that belongs to the same topic or has a similar difficulty.
    - If the last problem was **Medium** and the student **completed it**, suggest a **Medium** problem from the same type (tag/topic) or choose a different type (tag/topic).
    - If the last problem was **Hard** and the student **completed it**, suggest a **Hard** problem, possibly from a related topic or a slightly different challenge within the same difficulty.

    ### Additional Instructions:
    - Avoid suggesting the **same problem** again unless explicitly required (e.g., when the previous problem was not completed).
    - **Vary topics** and avoid repeating tags (e.g., 'Array', 'String') from the previous problems the student has worked on recently: {recent_tags}
    - Gradually increase or decrease the difficulty level to maintain the challenge without overwhelming the student. This approach will help keep the student engaged without feeling bored or frustrated.

    ### Data for Context:
    - You have access to a list of problems from a CSV file containing the following columns: **Title**, **Difficulty**, **Question Type**, **Leetcode Question Link**. The list is limited to 30 problems for context purposes.

    ### Your Task:
    - Choose an appropriate problem based on the above logic, keeping in mind the student's history, the difficulty, and the tags of recently solved problems.
    - Provide a **1-sentence reason** for the choice to help the student understand why this problem was selected.

    🎯 Return the selected problem and reasoning in the following **JSON format**:

    {{
        "Title": "<problem title>",  # Title of the selected problem
        "Difficulty": "<problem difficulty>",  # Difficulty of the selected problem (Easy, Medium, Hard)
        "Link": "<Leetcode link>",  # Link to the problem on LeetCode
        "Reason": "<1-sentence reason for selecting this problem>"  # Why this problem was selected
    }}

    Please ensure that the response **ONLY** contains this JSON output, without any additional commentary or text. The goal is to provide a clear, structured, and easy-to-follow problem recommendation.
    """

    response = model.generate_content(prompt)
    return response.text


# Save selected problem to file
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
    # Step 1: Collect user input about previous attempt
    previous_title = input("Enter the problem you solved previously: ")
    prev_difficulty = input("Enter its difficulty (Easy/Medium/Hard): ")
    time_taken = input("How much time did you take (e.g., 30 mins): ")
    completed = input("Did you complete the problem? (yes/no): ").lower()
    recent_tags = input("Enter tags (comma-separated) for that problem: ").split(",")

    previous_attempt = {
        "Title": previous_title,
        "Difficulty": prev_difficulty,
        "Time Taken": time_taken,
        "Completed": completed,
        "Tags": [tag.strip() for tag in recent_tags]
    }

    # Save to JSON
    with open("previous_attempt.json", "w") as f:
        json.dump(previous_attempt, f, indent=4)

    print("📝 Saved previous attempt.")

    # Step 2: Read previous attempt
    with open("previous_attempt.json", "r") as f:
        prev_data = json.load(f)

    # Step 3: Load problem dataset
    df = load_problems("leetcode_question.csv")

    # Step 4: Ask Gemini to pick a problem
    ai_response = pick_problem_with_ai(
        df,
        prev_title=prev_data["Title"],
        prev_difficulty=prev_data["Difficulty"],
        recent_tags=prev_data["Tags"],
        completed=prev_data["Completed"]
    )

    # Step 5: Parse AI response
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            raise ValueError("No valid JSON found.")

        problem_title = parsed["Title"]
        problem_link = parsed["Link"]
        reason = parsed["Reason"]
        user_behavior = "skipped" if prev_data["Completed"] == "no" else "completed"

        # Step 6: Save selected problem
        save_selected_problem(
            problem_title,
            problem_link,
            prev_data["Difficulty"],
            prev_data["Tags"],
            user_behavior,
            reason
        )

        print("✅ Agent 1 saved problem to JSON")
        print(json.dumps(parsed, indent=4))

    except Exception as e:
        print("❌ Failed to parse AI response:", str(e))
        print("Raw response:\n", ai_response)
