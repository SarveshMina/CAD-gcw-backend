# app/main.py

from azure.functions import HttpRequest, HttpResponse
import json
import logging

from app.user_routes import register_user, login_user
from app.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def register(req: HttpRequest) -> HttpResponse:
    logger.info("Register endpoint hit")
    try:
        req_body = req.get_json()
        user = User(**req_body)
        response, status_code = register_user(user)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in register endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)

def login(req: HttpRequest) -> HttpResponse:
    logger.info("Login endpoint hit")
    try:
        req_body = req.get_json()
        username = req_body.get("username")
        password = req_body.get("password")

        if not username or not password:
            return HttpResponse(json.dumps({"error": "Missing credentials"}), status_code=400)

        response, status_code = login_user(username, password)
        return HttpResponse(json.dumps(response), status_code=status_code)
    except Exception as e:
        logger.exception("Error in login endpoint: %s", str(e))
        return HttpResponse(str(e), status_code=500)
