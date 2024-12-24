# cloud-app-group-cw
Cloud Application Development (Group M)

## API
### /events/get
get events in a calendar

**Params**

* calendarId : string

**Response**

```
{
    "success": bool,
    "message": string, (if success == false)
    "events": event[] (if success == true)
}
```

#### event:

```
{
    "title": string,
    "desc": string,
    "time": int,
    "id": string
}
```

### /events/add
add an event to a calendar

**Params**

* calendarId : string

* title : string

* desc : string

* time : int - epoch time

**Response**

```
{
    "success": bool,
    "message": string, (if success == false)
    "eventId": string (if success == true)
}
```

### /events/remove
remove an event from a calendar

### /calendar/create
create a new calendar

**Params**

* name : string

* members : string[] | array of user ids

**Response**

```
{
    "success": bool,
    "message": string, (if success == false)
    "calendarId": string (if success == true)
}
```

### /calendar/delete
delete a calendar

### /calendar/info
get info about a calendar