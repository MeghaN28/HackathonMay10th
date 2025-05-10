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
import datetime

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


def generate_email_content(problem_title, problem_link, prev_difficulty, day_of_week, user_behavior, is_revision=False):
    if is_revision:
        prompt = f"""
You are an AI tutor sending a short motivational revision email.
Today is {day_of_week}.
The student is revisiting: "{problem_title}" (link: {problem_link}).

Write:
- A friendly greeting
- Mention it's a revision task and why it's helpful
- Encourage them to recall the key idea
- End with a motivational boost
        """
        subject = "🧠 Time to Revise a DSA Problem!"
    elif user_behavior.lower() == "skipped":
        prompt = f"""
You are an AI tutor reaching out to a student who skipped their last DSA problem.
Today is {day_of_week}.
Here’s the new opportunity: "{problem_title}" ({prev_difficulty}) - {problem_link}

Write:
- A kind, empathetic message
- Normalize skipping (everyone does it!)
- Emphasize progress over perfection
- Encourage giving this new problem a try
- Keep it short, warm, and motivational
        """
        subject = "💪 It's Okay to Skip — Let's Tackle a New DSA Problem!"
    elif user_behavior.lower() == "completed":
        prompt = f"""
You are an AI tutor congratulating a student for solving a previous DSA problem.
Today is {day_of_week}.
The next challenge is: "{problem_title}" ({prev_difficulty}) - {problem_link}

Write:
- A big congratulations
- Acknowledge their consistency
- Encourage them to keep the streak going
- Add a link to the new problem
        """
        subject = "🎉 Great Work! Ready for the Next DSA Challenge?"
    else:
        prompt = f"""
You are an AI tutor encouraging a student to continue DSA practice.
Today is {day_of_week}.
The problem for today is: "{problem_title}" ({prev_difficulty}) - {problem_link}

Write:
- A warm greeting
- Explain how today's problem fits their journey
- Motivate and guide them to keep practicing
        """
        subject = "🚀 Your Daily DSA Problem Awaits!"

    try:
        response = model.generate_content(prompt)
        return subject, response.text.strip()
    except Exception as e:
        print("⚠️ Gemini API failed:", str(e))
        fallback = f"Here's your problem of the day: {problem_title}\n{problem_link}"
        return subject, fallback


def create_and_send_email_from_json():
    try:
        with open("selected_problem.json", "r") as f:
            data = json.load(f)

        problem_title = data["Title"]
        problem_link = data["Leetcode Question Link"]
        prev_difficulty = data.get("Previous Difficulty", "Medium")
        user_behavior = data.get("User Behavior", "skipped")
        is_revision = "revision" in data.get("Tag", "").lower()
        day_of_week = datetime.datetime.now().strftime("%A")

        to_email = os.getenv("TO_EMAIL")
        if not to_email:
            raise ValueError("❌ Missing TO_EMAIL in .env")

        subject, email_body = generate_email_content(
            problem_title=problem_title,
            problem_link=problem_link,
            prev_difficulty=prev_difficulty,
            day_of_week=day_of_week,
            user_behavior=user_behavior,
            is_revision=is_revision
        )

        send_email_via_gmail(subject=subject, body=email_body, to_email=to_email)

    except FileNotFoundError:
        print("❌ selected_problem.json not found.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    create_and_send_email_from_json()
