# ---------------------------
# Comprehensive Personal Calendar Testing with JWT Authentication
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
        email = $Email
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

# Function to login a user and retrieve JWT token
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

# Function to create a personal calendar
function Create-PersonalCalendar {
    param (
        [string]$UserId,
        [string]$CalendarName,
        [string]$Token
    )

    Write-Host "=== Creating personal calendar '$CalendarName' for user '$UserId' ==="
    $calBody = @{
        userId = $UserId
        name = $CalendarName
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri "http://localhost:7071/api/personal-calendar/create" `
            -Method POST `
            -ContentType 'application/json' `
            -Body $calBody `
            -Headers @{ Authorization = "Bearer $Token" }

        Write-Host "Personal calendar creation response:" $response
        return $response
    } catch {
        Write-Host "Failed to create personal calendar. Error: $_"
    }
    Write-Host "`n"
}

# Function to add an event to a calendar
function Add-Event {
    param (
        [string]$CalendarId,
        [string]$Title,
        [datetime]$StartTime,
        [datetime]$EndTime,
        [string]$Description,
        [string]$Token
    )

    Write-Host "=== Adding event '$Title' to calendar '$CalendarId' ==="
    
    # Truncate seconds and microseconds for minute-level precision
    $StartTimeTruncated = $StartTime.AddSeconds(- $StartTime.Second).AddMilliseconds(- $StartTime.Millisecond).AddTicks(- ($StartTime.Ticks % 10000))
    $EndTimeTruncated = $EndTime.AddSeconds(- $EndTime.Second).AddMilliseconds(- $EndTime.Millisecond).AddTicks(- ($EndTime.Ticks % 10000))
    
    # Format datetime to ISO 8601 without fractional seconds and include timezone
    $StartTimeFormatted = $StartTimeTruncated.ToString("yyyy-MM-ddTHH:mm:ssK")  # No fractional seconds
    $EndTimeFormatted = $EndTimeTruncated.ToString("yyyy-MM-ddTHH:mm:ssK")      # No fractional seconds

    # Validate the format (optional but recommended)
    $iso8601Regex = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'  # Removed fractional seconds
    if (-not ($StartTimeFormatted -match $iso8601Regex)) {
        Write-Host "Invalid startTime format: $StartTimeFormatted"
        return
    }
    if (-not ($EndTimeFormatted -match $iso8601Regex)) {
        Write-Host "Invalid endTime format: $EndTimeFormatted"
        return
    }

    $eventBody = @{
        title = $Title
        startTime = $StartTimeFormatted
        endTime = $EndTimeFormatted
        description = $Description
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/calendar/" + $CalendarId + "/event") `
            -Method POST `
            -ContentType 'application/json' `
            -Body $eventBody `
            -Headers @{ Authorization = "Bearer $Token" }

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
        [hashtable]$UpdatedData,
        [string]$Token
    )

    Write-Host "=== Updating event '$EventId' in calendar '$CalendarId' ==="
    $updateBody = $UpdatedData | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/calendar/" + $CalendarId + "/event/" + $EventId + "/update") `
            -Method PUT `
            -ContentType 'application/json' `
            -Body $updateBody `
            -Headers @{ Authorization = "Bearer $Token" }

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
        [string]$Token
    )

    Write-Host "=== Deleting event '$EventId' from calendar '$CalendarId' ==="
    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/calendar/" + $CalendarId + "/event/" + $EventId + "/delete") `
            -Method DELETE `
            -ContentType 'application/json' `
            -Headers @{ Authorization = "Bearer $Token" }

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
        [string]$CalendarId,
        [string]$Token
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
            -Body $delBody `
            -Headers @{ Authorization = "Bearer $Token" }

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

# 2. Login user1 to get JWT token
$login1 = Login-User -Username "user1" -Password "Password123"

# Check if login was successful and token is received
if ($login1 -and $login1.token) {
    $token1 = $login1.token
    Write-Host "user1 JWT Token: $token1"
} else {
    Write-Host "Login failed for user1. Exiting test script."
    exit
}

# 3. Create a personal calendar for user1
$personalCal = Create-PersonalCalendar -UserId $user1.userId -CalendarName "User1 Personal Calendar" -Token $token1

# 4. Attempt to delete the default home calendar (should fail)
Write-Host "=== Attempting to delete default home calendar ==="
Delete-PersonalCalendar -UserId $user1.userId -CalendarId $user1.homeCalendarId -Token $token1

# 5. Create another personal calendar for user1
$workCal = Create-PersonalCalendar -UserId $user1.userId -CalendarName "User1 Work Calendar" -Token $token1

# 6. Add an event to the personal calendar
$event = Add-Event `
    -CalendarId $workCal.calendarId `
    -Title "Team Meeting" `
    -StartTime (Get-Date).AddDays(1).Date.AddHours(10) `
    -EndTime (Get-Date).AddDays(1).Date.AddHours(11) `
    -Description "Discuss project milestones." `
    -Token $token1

# 7. Update the event
if ($event -and $event.eventId) {
    Update-Event `
        -CalendarId $workCal.calendarId `
        -EventId $event.eventId `
        -UpdatedData @{
            title = "Updated Team Meeting"
            description = "Updated discussion points."
        } `
        -Token $token1
} else {
    Write-Host "No event to update."
}

# 8. Delete the event
if ($event -and $event.eventId) {
    Delete-Event `
        -CalendarId $workCal.calendarId `
        -EventId $event.eventId `
        -Token $token1
} else {
    Write-Host "No event to delete."
}

# 9. Delete the personal work calendar
Delete-PersonalCalendar -UserId $user1.userId -CalendarId $workCal.calendarId -Token $token1

Write-Host "=== Personal Calendar Comprehensive Testing Completed ==="
