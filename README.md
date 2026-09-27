# ResumeCraft — Automatic Resume Builder (Premium Starter)

A Flask + SQLite + ReportLab starter for the final-year "Automatic Resume Builder" project,
with a premium UI: animated gradient auth screens, glassmorphism cards, and 3 polished
resume templates (Modern, Professional two-column, Minimal) matched between the live
preview and the downloaded PDF. Working end-to-end, but meant to be extended (validation,
extra fields, more templates, etc.) as you build out the full project.

Requires an internet connection when running (loads Google Fonts for the premium look).

## Tech Stack
- Frontend: HTML5, CSS3, JavaScript (Jinja2 templates)
- Backend: Python 3 + Flask
- Database: SQLite
- PDF generation: ReportLab

## Folder Structure
```
resumecraft/
├── app.py                  # Main Flask app (routes, auth, CRUD)
├── requirements.txt
├── database.db              # created automatically on first run
├── utils/
│   ├── __init__.py
│   └── pdf_generator.py    # ReportLab PDF building logic
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── landing.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── my_resumes.html
│   ├── create_resume.html
│   ├── preview.html
│   └── profile.html
└── static/
    ├── css/style.css
    └── js/script.js
```

## Setup on Windows

1. **Install Python 3** (3.10+) from https://www.python.org/downloads/ — during install,
   check "Add Python to PATH".

2. **Open the project folder in VS Code.**

3. **Create a virtual environment** (open VS Code terminal — PowerShell or cmd):
   ```
   python -m venv venv
   ```

4. **Activate it:**
   - PowerShell:
     ```
     venv\Scripts\Activate.ps1
     ```
   - cmd.exe:
     ```
     venv\Scripts\activate.bat
     ```
   If PowerShell blocks the script, run once as admin:
   `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

5. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

6. **Run the app:**
   ```
   python app.py
   ```

7. **Open in Chrome:** http://127.0.0.1:5000

The SQLite database file (`database.db`) is created automatically the first time
you run the app.

## Testing Checklist

- [ ] Landing page loads at `/`
- [ ] Register a new account (`/register`) — duplicate email is rejected
- [ ] Login with correct credentials succeeds; wrong password is rejected
- [ ] Dashboard shows after login, empty state message when no resumes
- [ ] Create a resume (`/resume/new`) with all fields + pick a template
- [ ] Resume appears on Dashboard and "My Resumes"
- [ ] Preview page renders correct template styling (modern/professional/minimal)
- [ ] Edit an existing resume — changes persist
- [ ] Download PDF — opens correctly and matches selected template
- [ ] Delete a resume — removed from list, confirm dialog appears
- [ ] Update profile name and password — new password works on next login
- [ ] Logout clears session; protected pages redirect to `/login`

## Notes / Next Steps to Extend
- `app.secret_key` in `app.py` is a placeholder — replace with an environment variable
  before any real deployment.
- Resume "template" currently controls color/typography in preview + PDF; you can add
  more layout differences (e.g. two-column) in `static/css/style.css` and
  `utils/pdf_generator.py`.
- Add server-side validation (email format, password strength) as needed.
- Consider adding a "duplicate resume" feature and resume search/filter on the My Resumes page.
