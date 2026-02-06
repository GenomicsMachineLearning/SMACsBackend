from mangum import Mangum
from app.main import app

# Create the Mangum handler
handler = Mangum(app, lifespan="off")
