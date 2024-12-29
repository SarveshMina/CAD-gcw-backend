# ---------------------------
# Test Personal Calendar Functionality
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

# Function to create a personal calendar
function Create-PersonalCalendar {
    param (
        [string]$UserId,
        [string]$CalendarName
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
            -Body $calBody

        Write-Host "Personal calendar creation response:" $response
        return $response
    } catch {
        Write-Host "Failed to create personal calendar. Error: $_"
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
        Write-Host "Failed to delete personal calendar. Error: $_"
    }
    Write-Host "`n"
}

# Function to add an event to a calendar
function Add-Event {
    param (
        [string]$CalendarId,
        [string]$CreatorId,
        [string]$Title,
        [datetime]$StartTime,
        [datetime]$EndTime,
        [string]$Description
    )

    Write-Host "=== Adding event '$Title' to calendar '$CalendarId' ==="
    $eventBody = @{
        title = $Title
        startTime = $StartTime
        endTime = $EndTime
        description = $Description
        creatorId = $CreatorId
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod `
            -Uri ("http://localhost:7071/api/calendar/" + $CalendarId + "/event") `
            -Method POST `
            -ContentType 'application/json' `
            -Body $eventBody

        Write-Host "Add event response:" $response
    } catch {
        Write-Host "Failed to add event. Error: $_"
    }
    Write-Host "`n"
}

# ---------------------------
# Execute Test Steps
# ---------------------------

# 1. Register user1
$user1 = Register-User -Username "user1" -Password "Password123" -Email "user1@example.com"

# 2. Register user2
$user2 = Register-User -Username "user2-test" -Password "Password123" -Email "user2@example.com"

# 3. Create a personal calendar for user1
$personalCal = Create-PersonalCalendar -UserId $user1.userId -CalendarName "User1 Personal Calendar"

# 4. Attempt to delete the default home calendar (should fail)
Write-Host "=== Attempting to delete default home calendar ==="
Delete-PersonalCalendar -UserId $user1.userId -CalendarId $user1.homeCalendarId

# 5. Create another personal calendar for user1
$anotherCal = Create-PersonalCalendar -UserId $user1.userId -CalendarName "User1 Work Calendar"

# 6. Add an event to the new personal calendar
Add-Event `
    -CalendarId $anotherCal.calendarId `
    -CreatorId $user1.userId `
    -Title "Team Meeting" `
    -StartTime (Get-Date).AddDays(1).Date.AddHours(10) `
    -EndTime (Get-Date).AddDays(1).Date.AddHours(11) `
    -Description "Discuss project milestones."

# 7. Delete the new personal calendar
Delete-PersonalCalendar -UserId $user1.userId -CalendarId $anotherCal.calendarId

Write-Host "=== Personal Calendar Testing Completed ==="
