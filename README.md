This project is a smart DSA (Data Structures & Algorithms) learning assistant powered by AI. It tracks your problem-solving progress and suggests new LeetCode problems based on your performance. Built for a hackathon, the system aims to help learners build consistency, revisit difficult problems, and grow their problem-solving skills through tailored recommendations.

🚀 Features
✅ Submit LeetCode problems with completion status, tags, and time taken

🤖 AI suggests the next best problem using context from your previous attempts

🔁 Revision scheduling based on your performance (especially for skipped/incomplete problems)

📬 (Planned) Email or calendar reminder integration for scheduled revisions


📊 All data saved locally in CSV/JSON for easy tracking

🛠️ Tech Stack

Backend: Python

AI Model: Google Gemini (gemini-1.5-flash)

Data Storage: JSON (all_attempts.json), CSV (leetcode_question.csv)

Others: CORS, dotenv, Pandas