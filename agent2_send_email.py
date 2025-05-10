import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pickle
import base64
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json
import google.generativeai as genai
import os

# Load .env file
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CLIENT_SECRET_FILE = 'client_secret_573959129688-g8rsclts9c0d1c7pl562k0o3l1c93sku.apps.googleusercontent.com.json'

def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def send_email_via_gmail(subject, body, to_email):
    service = build('gmail', 'v1', credentials=authenticate_gmail())
    message = MIMEMultipart()
    message['to'] = to_email
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
    print("📤 Email sent successfully")

# Load problem from JSON
def load_problem_from_json(filepath="selected_problem.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def generate_email_content(problem_title, problem_link, prev_difficulty, day_of_week, user_behavior):
    # Define tone based on completion
    if user_behavior == "completed":
        tone = "boosting"
        intro = f"Great job! You've successfully completed a {prev_difficulty} problem!"
        encouragement = "You're on fire! Keep going and tackle this next challenge!"
    else:
        tone = "motivational"
        intro = f"Hey, it's {day_of_week}, and a fresh start awaits!"
        encouragement = "You’ve got this! Keep pushing forward!"

    prompt = f"""
You are an AI tutor sending a personalized email.
It's {day_of_week}. The student previously attempted a {prev_difficulty} problem.
Tone: {tone}
Problem: {problem_title}
Link: {problem_link}

Write a short, personalized, and motivational email:
- Friendly opening
- Reason for choosing the problem
- Encouragement to keep going
"""
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    return response.text

def create_selected_problem_json(problem_data):
    # Create and save selected_problem.json based on the selected problem
    with open("selected_problem.json", "w") as f:
        json.dump(problem_data, f, indent=4)

def create_and_send_email_from_json(to_email="n.megha82@gmail.com"):
    # Use the data (replace with dynamic generation logic as needed)
    data = {
        "Title": "Number of Islands",
        "Leetcode Question Link": "https://leetcode.com/problems/number-of-islands/",
        "Previous Difficulty": "easy",
        "Recent Tags": [
            "graphs"
        ],
        "User Behavior": "completed",
        "Reason": "This problem is a Medium-level graph problem, building upon your previous graph work."
    }
    
    # Create selected_problem.json
    create_selected_problem_json(data)

    # Generate email content based on the problem data
    email_body = generate_email_content(
        data["Title"],
        data["Leetcode Question Link"],
        data["Previous Difficulty"],
        day_of_week="Monday",  # You can dynamically set this based on the current day
        user_behavior=data["User Behavior"]
    )

    # Send email
    send_email_via_gmail(
        subject="Your Next DSA Problem - Let's Go!",
        body=email_body,
        to_email=to_email
    )

if __name__ == "__main__":
    create_and_send_email_from_json()
