from quart import Quart

# Import your setup tools and the blueprint
from database import init_db
from handlers import bp

app = Quart(__name__)

# Register the routes from handlers.py
app.register_blueprint(bp)

@app.before_serving
async def startup():
    """Initialize the database before the app starts serving."""
    await init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)