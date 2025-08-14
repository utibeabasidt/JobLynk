from dotenv import load_dotenv
from flask import Flask
import os
from routes import routes

load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.getenv("SECRET_KEY")  # For flash messages

app.register_blueprint(routes)

# Run the app
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)