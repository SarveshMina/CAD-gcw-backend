import azure.functions as func
from app.main import register, login, create_event, list_events

app = func.FunctionApp()

@app.route(route="register", methods=["POST"])
def register_function(req: func.HttpRequest) -> func.HttpResponse:
    return register(req)

@app.route(route="login", methods=["POST"])
def login_function(req: func.HttpRequest) -> func.HttpResponse:
    return login(req)

# Instead of doing 'def create_event_function(req, calendarId: str)', 
# retrieve 'calendarId' from req.route_params inside the function
@app.route(route="calendar/{calendarId}/event", methods=["POST"])
def create_event_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get('calendarId')
    return create_event(req, calendar_id)

@app.route(route="calendar/{calendarId}/events", methods=["GET"])
def list_events_function(req: func.HttpRequest) -> func.HttpResponse:
    calendar_id = req.route_params.get('calendarId')
    return list_events(req, calendar_id)
