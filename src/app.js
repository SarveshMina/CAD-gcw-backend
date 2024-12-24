'use strict';

const { CosmosClient } = require('@azure/cosmos');

//Set up express
const express = require('express');
const app = express();

//Setup socket.io
const server = require('http').Server(app);

const COSMOS_ENDPOINT = "AccountEndpoint=https://cloud-app-coursework-he2g22-db.documents.azure.com:443/;AccountKey=jKkTeirD9ALomPw1nVJ2DwpxXxSLc9df5FO7wDYcJ0FOKTv4rYp8KgfZKaT5EaH48BNKxA8vFPoMACDbELGjTw==;";
const databaseName = "coursework";
const calendarInfoContainerName = "calendars-infos";
const calendarEventsContainerName = "calendars-events"

const cosmosClient = new CosmosClient(COSMOS_ENDPOINT);

let calendarInfoContainer;
let calendarEventsContainer;

// get the events in a calendar
// params: calendarId
app.get('/events/get', (req, res) => {
    if (!calendarEventsContainer || !calendarInfoContainer) {
        console.log(`request made when container is not initialised`);
        res.send({
            success: false,
            message: "server error"
        });
        return;
    }

    // validate params
    let calendarId;
    try {
        calendarId = req.query.calendarId;
    } catch (e) {
        console.log(`invalid params (${req.query})`);
        res.send({
            success: false,
            message: `invalid params`
        });
        return;
    }

    // check if the calendar exists in the info container
    calendarInfoContainer.items
    .query(`SELECT * FROM c WHERE c.id = "${calendarId}"`)
    .fetchAll().then((queryRes) => {
        let events = queryRes["resources"];
        if (events.length == 0) {
            console.log(`calendar does not exist (id: ${calendarId})`);
            res.send({
                success: false,
                message: "calendar does not exist",
            });
            return;
        }

        // if it does exist, get the associated events
        calendarEventsContainer.items
        .query(`SELECT * FROM c WHERE c.calendarId = "${calendarId}"`)
        .fetchAll().then((queryRes) => {
            let events = queryRes["resources"];
            // remove cosmos self-inserted data
            let filteredEvents = [];
            for (let i = 0; i < events.length; i++) {
                filteredEvents.push({
                    title: events[i]["title"],
                    desc: events[i]["desc"],
                    time: events[i]["time"],
                    id: events[i]["id"],
                })
            }

            res.send({
                success: true,
                events: filteredEvents,
            });
            return;
        })
    })
});

// add an event to a calendar
// params: calendarId, title, desc, time
app.get('/events/add', (req, res) => {
    if (!calendarEventsContainer) {
        console.log(`request made when container is not initialised`);
        res.send({
            success: false,
            message: "server error"
        });
        return;
    }

    // validate params
    let _calendarId;
    let _title;
    let _desc;
    let _time;
    try {
        _calendarId = req.query.calendarId;
        _title = req.query.title;
        _desc = req.query.desc;
        _time = Number(req.query.time);
    } catch (e) {
        console.log(`invalid params (${req.query})`);
        res.send({
            success: false,
            message: `invalid params`
        });
        return;
    }

    // check if calendar exists
    calendarInfoContainer.items
    .query(`SELECT * FROM c WHERE c.id = "${_calendarId}"`)
    .fetchAll().then((queryRes) => {
        let events = queryRes["resources"];
        if (events.length == 0) {
            console.log(`calendar does not exist (id: ${_calendarId})`);
            res.send({
                success: false,
                message: "calendar does not exist",
            });
            return;
        }

        // create the event
        let item = {
            calendarId: _calendarId,
            title: _title,
            desc: _desc,
            time: _time,
        }
        try {
            calendarEventsContainer.items.create(item).then((queryRes) => {
                res.send({
                    success: true,
                    eventId: queryRes.resource.id,
                });
            })
        } catch (e) {
            console.log(e);
            res.send({
                success: false,
                message: "server error",
            });
        }
    });
});

// remove an event from a calendar
app.get('/events/remove', (req, res) => {
    res.send({
        success: false,
        message: "not implemented"
    });
});

// create a new calendar
// params: name, members
// response: {
//      success: bool,
//      calendarId: string (if success true)
//      message: string (if success false)
// }
app.get('/calendar/create', (req, res) => {
    if (!checkContainersInitialised(res)) return;

    // validate params
    let _name;
    let _members;
    try {
        _name = req.query.name;
        _members = JSON.parse(req.query.members);
    } catch (e) {
        console.log(`invalid params (${req.query})`);
        res.send({
            success: false,
            message: `invalid params`
        });
        return;
    }

    let item = {
        name: _name,
        members: _members,
    }
    try {
        calendarInfoContainer.items.create(item).then((queryRes) => {
            console.log(queryRes);
            res.send({
                success: true,
                calendarId: queryRes.resource.id,
            });
        })
    } catch (e) {
        console.log(e);
        res.send({
            success: false,
            message: "server error",
        });
    }
});

// delete a calendar
app.get('/calendar/delete', (req, res) => {
    res.send({
        success: false,
        message: "not implemented"
    });
});

app.get('/calendar/info', (req, res) => {
    res.send({
        success: false,
        message: "not implemented"
    });
})

//Start the server
function startServer() {
    cosmosClient.databases.createIfNotExists({ id: databaseName }).then(({ database }) => {
        console.log(`connected to database ${database.id}`);
    
        database.containers.createIfNotExists({ id: calendarInfoContainerName }).then(({ container }) => {
            calendarInfoContainer = container;
            console.log(`loaded container ${container.id}`);
        });

        database.containers.createIfNotExists({ id: calendarEventsContainerName }).then(({ container }) => {
            calendarEventsContainer = container;
            console.log(`loaded container ${container.id}`);
        });
    })

    const PORT = process.env.PORT || 8080;
    server.listen(PORT, () => {
        console.log(`Server listening on port ${PORT}`);
    });
}

//Start server
if (module === require.main) {
    startServer();
}

function checkContainersInitialised(res) {
    if (!calendarEventsContainer || !calendarInfoContainer) {
        console.log(`request made when container is not initialised`);
        res.send({
            success: false,
            message: "server error"
        });
        return false;
    }
    return true;
}

module.exports = server;
