
import os
from dotenv import load_dotenv
from flask import Flask
from routes import routes
from db import create_tables

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24)) 


app.register_blueprint(routes)

if os.getenv("FLASK_ENV") == "production":
    create_tables()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5001)))
