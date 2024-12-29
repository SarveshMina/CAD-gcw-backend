# app/auth.py

import jwt
from azure.functions import HttpRequest, HttpResponse
from functools import wraps
import json
import logging
from dotenv import load_dotenv
import os

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def token_required(func):
    @wraps(func)
    def wrapper(req: HttpRequest, *args, **kwargs):
        auth_header = req.headers.get("Authorization")
        if not auth_header:
            logger.warning("Authorization header missing")
            return HttpResponse(
                json.dumps({"error": "Authorization header missing"}),
                status_code=401,
                mimetype="application/json"
            )
        
        try:
            token_type, token = auth_header.split(" ")
            if token_type.lower() != "bearer":
                logger.warning("Invalid token type")
                raise ValueError("Invalid token type")
        except ValueError:
            logger.warning("Invalid Authorization header format")
            return HttpResponse(
                json.dumps({"error": "Invalid Authorization header format"}),
                status_code=401,
                mimetype="application/json"
            )

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("userId")
            if not user_id:
                raise jwt.InvalidTokenError("userId missing in token")
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return HttpResponse(
                json.dumps({"error": "Token has expired"}),
                status_code=401,
                mimetype="application/json"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return HttpResponse(
                json.dumps({"error": "Invalid token"}),
                status_code=401,
                mimetype="application/json"
            )
        
        # Pass user_id as a keyword argument
        return func(req, *args, user_id=user_id, **kwargs)
    return wrapper
