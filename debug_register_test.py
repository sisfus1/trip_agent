import logging
import traceback
from backend.auth import register_user
from backend.schemas import UserCreate
from backend.database import SessionLocal

class DummyRequest:
    def __init__(self):
        self.headers = {"X-Test-Captcha": "8888"}

def debug_register():
    db = SessionLocal()
    user_data = UserCreate(username="local_debug_user", password="secure_password_123")
    req = DummyRequest()
    
    try:
        res = register_user(user=user_data, request=req, db=db)
        print("Success:", res)
    except Exception as e:
        print("Caught Exception:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_register()
