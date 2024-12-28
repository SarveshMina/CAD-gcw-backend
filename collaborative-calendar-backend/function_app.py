# function_app.py

import azure.functions as func
from app.main import register, login, create_event, list_events

app = func.FunctionApp()

@app.route(route="register", methods=["POST"])
def register_function(req: func.HttpRequest) -> func.HttpResponse:
    return register(req)

@app.route(route="login", methods=["POST"])
def login_function(req: func.HttpRequest) -> func.HttpResponse:
    return login(req)

# New endpoints
@app.route(route="calendar/{calendarId}/event", methods=["POST"])
def create_event_function(req: func.HttpRequest, calendarId: str) -> func.HttpResponse:
    return create_event(req, calendarId)

@app.route(route="calendar/{calendarId}/events", methods=["GET"])
def list_events_function(req: func.HttpRequest, calendarId: str) -> func.HttpResponse:
    return list_events(req, calendarId)
