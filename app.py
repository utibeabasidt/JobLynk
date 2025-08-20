from flask import Flask
import os
from routes import routes
from db import create_tables

create_tables()  # Ensure tables are created at startup

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.getenv("SECRET_KEY")  

app.register_blueprint(routes)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)