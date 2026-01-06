"""Generate test JWT token for development."""
from app.core.auth import create_access_token
import sys

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "test_user"
    token = create_access_token(user_id)
    print(token)
