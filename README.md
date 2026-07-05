# Resume Screening System

A full-stack final year project that helps users upload resumes, analyze them with AI, and compare them against job descriptions. The system provides authentication, resume history, scoring, and an interactive dashboard.

# Features

- User registration and login
- Resume upload and analysis
- AI-powered extraction of skills, experience, and profile details
- Job matching and scoring
- Resume history and reports
- Modern frontend dashboard and onboarding pages

# Tech Stack

- Backend: Flask, Flask JWT Extended, Flask CORS, Flask Limiter
- Database: MongoDB
- AI: Groq API
- Frontend: HTML, CSS, JavaScript
- Testing: Pytest

# Project Structure

text
Resume-Screening/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── setup_db.py
│   ├── api/
│   ├── db/
│   ├── middleware/
│   ├── models/
│   ├── routes/
│   └── services/
├── frontend/
│   ├── css/
│   ├── js/
│   └── *.html
└── tests/

## Prerequisites

Make sure you have installed:

- Python 3.10+
- MongoDB
- Git
- A Groq API key

## Setup Instructions (Windows)

1. Open the project folder

bash
cd "c:/Users/abdul/Desktop/Final year project/Resume-Screening"


2. Create and activate a virtual environment

bash
cd backend
python -m venv venv
venv\Scripts\activate

3. Install dependencies

bash
pip install -r requirements.txt


4. Create a `.env` file inside the backend folder

env
MONGO_URI=mongodb://localhost:27017/resume_checker
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_generated_encryption_key
PORT=5000

5. Generate an encryption key (optional but recommended)

bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"


6. Start MongoDB locally

bash
mongod --dbpath C:\data\db

7. Initialize the database once

bash
python setup_db.py

8. Start the application

bash
python app.py

Then open:

text
http://localhost:5000

## Run the Tests

bash
pytest
```

## API Overview

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/refresh
- GET /api/auth/me

### Resume
- POST /api/resume/analyze
- GET /api/resume/history

### Chat
- POST /api/chat
- GET /api/chat
- DELETE /api/chat

### Health Check
- GET /api/health

## GitHub Commands

If you want to upload this project to GitHub, run:

```bash
git init
git add .
git commit -m "feat: complete resume screening project with AI-powered analysis"
git branch -M main
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

If the repository already exists and is connected, use:

bash
git add .
git commit -m "feat: complete resume screening project with AI-powered analysis"
git push origin main

## Notes

- Do not commit your `.env` file.
- Keep your API keys private.
- If you face activation issues in PowerShell, run:

powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned


## License

This project is intended for educational and academic use.
