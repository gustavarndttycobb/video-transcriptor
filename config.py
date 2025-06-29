import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
SECRET_KEY = os.getenv(
	"SECRET_KEY", 
	"your-fallback-secret-key"  # Important: Change this!
)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")
TEST_DATABASE_URL = "sqlite:///:memory:"  # Always use in-memory for tests
