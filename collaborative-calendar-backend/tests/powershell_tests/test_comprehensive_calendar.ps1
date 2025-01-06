# ---------------------------
# Comprehensive Personal Calendar Testing WITHOUT JWT
# ---------------------------

# Function to register a user
function Register-User {
    param (
        [string]$Username,
        [string]$Password,
        [string]$Email
    )

    Write-Host "=== Registering $Username ==="
    $userBody = @{
        username = $Username
        password = $Password
        email    = $Email
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri "http://localhost:7071/api/register" `
            -Method POST `
            -ContentType 'application/json' `
            -Body $userBody

        Write-Host "$Username response:" $response
        return $response
    } catch {
        Write-Host "Failed to register $Username. Error: $_"
    }
    Write-Host "`n"
}

# Function to login a user (no JWT returned)
function Login-User {
    param (
        [string]$Username,
        [string]$Password
    )

    Write-Host "=== Logging in $Username ==="
    $loginBody = @{
        username = $Username
        password = $Password
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri "http://localhost:7071/api/login" `
            -Method POST `
            -ContentType 'application/json' `
            -Body $loginBody

        Write-Host "$Username login response:" $response
        return $response
    } catch {
        Write-Host "Failed to login $Username. Error: $_"
    }
    Write-Host "`n"
}

# Function to create a personal calendar (no token)
function Create-PersonalCalendar {
    param (
        [string]$UserId,
        [string]$CalendarName
    )

    Write-Host "=== Creating personal calendar '$CalendarName' for user '$UserId' ==="
    $calBody = @{
        userId = $UserId
        name   = $CalendarName
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri "http://localhost:7071/api/personal-calendar/create" `
            -Method POST `
            -ContentType 'application/json' `
            -Body $calBody

        Write-Host "Personal calendar creation response:" $response
        return $response
    } catch {
        Write-Host "Failed to create personal calendar. Error: $_"
    }
    Write-Host "`n"
}

# Function to add an event to a calendar (no token)
function Add-Event {
    param (
        [string]$CalendarId,
        [string]$UserId,
        [string]$Title,
        [datetime]$StartTime,
        [datetime]$EndTime,
        [string]$Description
    )

    Write-Host "=== Adding event '$Title' to calendar '$CalendarId' ==="
    
    # Truncate seconds and microseconds for minute-level precision
    $StartTimeTruncated = $StartTime.AddSeconds(- $StartTime.Second).AddMilliseconds(- $StartTime.Millisecond).AddTicks(- ($StartTime.Ticks % 10000))
    $EndTimeTruncated   = $EndTime.AddSeconds(- $EndTime.Second).AddMilliseconds(- $EndTime.Millisecond).AddTicks(- ($EndTime.Ticks % 10000))
    
    # Format datetime to ISO 8601 (no fractional seconds)
    $StartTimeFormatted = $StartTimeTruncated.ToString("yyyy-MM-ddTHH:mm:ssK")  
    $EndTimeFormatted   = $EndTimeTruncated.ToString("yyyy-MM-ddTHH:mm:ssK")

    # Optional: Validate the format (just for consistency)
    $iso8601Regex = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'
    if (-not ($StartTimeFormatted -match $iso8601Regex)) {
        Write-Host "Invalid startTime format: $StartTimeFormatted"
        return
    }
    if (-not ($EndTimeFormatted -match $iso8601Regex)) {
        Write-Host "Invalid endTime format: $EndTimeFormatted"
        return
    }

    # We pass userId in the body because there's no token
    $eventBody = @{
        userId      = $UserId
        title       = $Title
        startTime   = $StartTimeFormatted
        endTime     = $EndTimeFormatted
        description = $Description
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/calendar/" + $CalendarId + "/event") `
            -Method POST `
            -ContentType 'application/json' `
            -Body $eventBody

        Write-Host "Add event response:" $response
        return $response
    } catch {
        Write-Host "Failed to add event. Error: $_"
    }
    Write-Host "`n"
}

# Function to update an event
function Update-Event {
    param (
        [string]$CalendarId,
        [string]$EventId,
        [string]$UserId,
        [hashtable]$UpdatedData
    )

    Write-Host "=== Updating event '$EventId' in calendar '$CalendarId' ==="

    # Add userId to the body (no token)
    $bodyHash = $UpdatedData
    $bodyHash["userId"] = $UserId
    $updateBody = $bodyHash | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/calendar/" + $CalendarId + "/event/" + $EventId + "/update") `
            -Method PUT `
            -ContentType 'application/json' `
            -Body $updateBody

        Write-Host "Update event response:" $response
    } catch {
        Write-Host "Failed to update event. Error: $_"
    }
    Write-Host "`n"
}

# Function to delete an event
function Delete-Event {
    param (
        [string]$CalendarId,
        [string]$EventId,
        [string]$UserId
    )

    Write-Host "=== Deleting event '$EventId' from calendar '$CalendarId' ==="
    $deleteBody = @{
        userId = $UserId
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/calendar/" + $CalendarId + "/event/" + $EventId + "/delete") `
            -Method DELETE `
            -ContentType 'application/json' `
            -Body $deleteBody

        Write-Host "Delete event response:" $response
    } catch {
        Write-Host "Failed to delete event. Error: $_"
    }
    Write-Host "`n"
}

# Function to delete a personal calendar
function Delete-PersonalCalendar {
    param (
        [string]$UserId,
        [string]$CalendarId
    )

    Write-Host "=== Deleting personal calendar '$CalendarId' for user '$UserId' ==="
    $delBody = @{
        userId = $UserId
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/personal-calendar/" + $CalendarId + "/delete") `
            -Method POST `
            -ContentType 'application/json' `
            -Body $delBody

        Write-Host "Delete calendar response:" $response
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 400) {
            Write-Host "Expected failure: Cannot delete default home calendar. Error: $_"
        } else {
            Write-Host "Failed to delete personal calendar. Error: $_"
        }
    }
    Write-Host "`n"
}

# ---------------------------
# Execute Test Steps
# ---------------------------

# 1. Register user1
$user1 = Register-User -Username "user1" -Password "Password123" -Email "user1@example.com"

# 2. Login user1 (no token expected)
$login1 = Login-User -Username "user1" -Password "Password123"

# If login was successful, we have userId
if ($null -ne $login1 -and $null -ne $login1.userId) {
    $user1Id = $login1.userId
    Write-Host "user1 ID: $user1Id"
} else {
    Write-Host "Login failed for user1. Exiting test script."
    exit
}

# 3. Create a personal calendar for user1 (no token)
$personalCal = Create-PersonalCalendar -UserId $user1Id -CalendarName "User1 Personal Calendar"

# 4. Attempt to delete the default home calendar (should fail with status 400)
Write-Host "=== Attempting to delete default home calendar ==="
Delete-PersonalCalendar -UserId $user1Id -CalendarId $user1.homeCalendarId

# 5. Create another personal calendar for user1
$workCal = Create-PersonalCalendar -UserId $user1Id -CalendarName "User1 Work Calendar"

# 6. Add an event to the new personal calendar
# Notice we pass userId in -UserId parameter
$event = Add-Event `
    -CalendarId $workCal.calendarId `
    -UserId $user1Id `
    -Title "Team Meeting" `
    -StartTime (Get-Date).AddDays(1).Date.AddHours(10) `
    -EndTime (Get-Date).AddDays(1).Date.AddHours(11) `
    -Description "Discuss project milestones."

# 7. Update the event (if created)
if ($event -and $event.eventId) {
    Update-Event `
        -CalendarId $workCal.calendarId `
        -EventId $event.eventId `
        -UserId $user1Id `
        -UpdatedData @{
            title = "Updated Team Meeting"
            description = "Updated discussion points."
        }
} else {
    Write-Host "No event to update."
}

# # 8. Delete the event (optional)
# if ($event -and $event.eventId) {
#     Delete-Event `
#         -CalendarId $workCal.calendarId `
#         -EventId $event.eventId `
#         -UserId $user1Id
# } else {
#     Write-Host "No event to delete."
# }

# # 9. Finally, delete the personal work calendar (optional)
# Delete-PersonalCalendar -UserId $user1Id -CalendarId $workCal.calendarId

Write-Host "=== Personal Calendar Comprehensive Testing Completed ==="