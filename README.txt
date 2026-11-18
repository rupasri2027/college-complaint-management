CAMPUSCARE - COLLEGE COMPLAINT MANAGEMENT SYSTEM
================================================

WHAT IS INCLUDED
- Student registration and login
- Submit complaints with categories
- Student complaint tracking
- Admin dashboard
- Admin can update status and send a response
- SQLite database (created automatically)

REQUIREMENTS
- Python 3.9 or newer
- Internet connection for the Bootstrap styling CDN (optional; app logic works locally)

HOW TO RUN ON WINDOWS
1. Extract the ZIP file.
2. Open the extracted folder.
3. Click the folder address bar, type cmd, and press Enter.
4. Run these commands:

   py -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   py app.py

5. Open this address in your browser:
   http://127.0.0.1:5000

DEFAULT ADMIN LOGIN
Email: admin@college.com
Password: Admin@123

IMPORTANT:
- Change the default admin password before using this for real users.
- This is a college demonstration starter project. Before public deployment,
  set a strong SECRET_KEY environment variable, use HTTPS, change default
  credentials, and review security/privacy requirements.
- The local address works only on the computer running the app. To share a
  public live website, deploy it to a hosting service (such as Render) and
  configure its environment variables and persistent database storage.
