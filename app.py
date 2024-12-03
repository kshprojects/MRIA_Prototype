from flask import Flask, render_template
from routes.users_routes import users_db
from routes.conversation_routes import conversation_blueprint
from routes.queries_routes import queries
from routes.response_routes import responses
from routes.qdrant_api import qdrant_blueprint  # Import the blueprint from qdrant_api

app = Flask(__name__)

# Register the blueprints
app.register_blueprint(users_db, url_prefix="/app")
app.register_blueprint(conversation_blueprint, url_prefix="/app")
app.register_blueprint(queries, url_prefix="/app")
app.register_blueprint(responses, url_prefix="/app")
app.register_blueprint(qdrant_blueprint, url_prefix="/app")  # Register the Qdrant blueprint

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register')
def register():
    return render_template("registration.html") 

@app.route('/login')
def login():
    return render_template("login.html")  

@app.route('/main1')
def main():
    return render_template("main1.html")

@app.route('/conversation')
def conversation():
    return render_template("conversation.html")

if __name__ == "__main__":
    app.run(debug=True)
