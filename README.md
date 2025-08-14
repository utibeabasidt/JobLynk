# JobLynk
A simple job listing website for freelancers and employers.

## Setup
1. Clone the repo: `git clone https://github.com/utibeabasidt/JobLynk.git`
2. Install PostgreSQL and create a `joblynk_db` database.
3. Create a `.env` file with credentials (see example).
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `python app.py`

## .env Example
POSTGRES_DATABASE=joblynk_db
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
SECRET_KEY=your-secret-key