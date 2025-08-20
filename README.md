# JobLynk
A simple job listing website for freelancers and employers.

## Setup
1. Clone the repo: `git clone https://github.com/utibeabasidt/JobLynk`
2. Install Python 3 and Git.
3. Create a virtual environment: `python -m venv venv` (Windows) or `python3 -m venv venv` (macOS/Linux).
4. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux).
5. Install dependencies: `pip install -r requirements.txt`.
6. Set up Render PostgreSQL: Create a database on Render and copy the DATABASE_URL.
7. Create .env with: `DATABASE_URL=<your_render_database_url> SECRET_KEY=<your-secret-key>`.
8. Initialize tables: `python -c "from db import create_tables; create_tables()"`.
9. Run the app: `python app.py` and visit http://127.0.0.1:5000/.

## Deployment
- Push to GitHub, deploy on Render, and set DATABASE_URL in Render's environment.