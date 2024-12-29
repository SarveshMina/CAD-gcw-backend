# ---------------------------
# 1) Register user1
# ---------------------------
Write-Host "=== Registering user1 ==="
$user1Body = @{
    username = "user1"
    password = "Pass12345"
    email = "user1@example.com"
} | ConvertTo-Json

$user1Response = Invoke-RestMethod `
    -Uri "http://localhost:7071/api/register" `
    -Method POST `
    -ContentType 'application/json' `
    -Body $user1Body

Write-Host "user1 response:" $user1Response

# Extract user1's userId (needed for group ownership)
$user1Id = $user1Response.userId
Write-Host "user1Id =" $user1Id
Write-Host "`n"


# ---------------------------
# 2) Register user2
# ---------------------------
Write-Host "=== Registering user2 ==="
$user2Body = @{
    username = "user2"
    password = "Pass12345"
    email = "user2@example.com"
} | ConvertTo-Json

$user2Response = Invoke-RestMethod `
    -Uri "http://localhost:7071/api/register" `
    -Method POST `
    -ContentType 'application/json' `
    -Body $user2Body

Write-Host "user2 response:" $user2Response

# Extract user2's userId
$user2Id = $user2Response.userId
Write-Host "user2Id =" $user2Id
Write-Host "`n"


# ---------------------------
# 3) Register user3
# ---------------------------
Write-Host "=== Registering user3 ==="
$user3Body = @{
    username = "user3"
    password = "Pass12345"
    email = "user3@example.com"
} | ConvertTo-Json

$user3Response = Invoke-RestMethod `
    -Uri "http://localhost:7071/api/register" `
    -Method POST `
    -ContentType 'application/json' `
    -Body $user3Body

Write-Host "user3 response:" $user3Response

# Extract user3's userId
$user3Id = $user3Response.userId
Write-Host "user3Id =" $user3Id
Write-Host "`n"


# ---------------------------
# 4) Create a group calendar owned by user1
# ---------------------------
Write-Host "=== Creating a group calendar with owner user1 ==="
$groupBody = @{
    ownerId = $user1Id
    name = "CAD Project Group"
    members = @()   # optional: initially empty or add other IDs
} | ConvertTo-Json

$groupResponse = Invoke-RestMethod `
    -Uri "http://localhost:7071/api/group-calendar/create" `
    -Method POST `
    -ContentType 'application/json' `
    -Body $groupBody

Write-Host "Group creation response:" $groupResponse

# Extract the new group calendar's ID
$calendarId = $groupResponse.calendarId
Write-Host "group calendarId =" $calendarId
Write-Host "`n"


# ---------------------------
# 5) Add user2 to the group
# ---------------------------
Write-Host "=== Adding user2 to group ==="
$addUser2Body = @{
    adminId = $user1Id  # must be the owner's userId
    userId = $user2Id
} | ConvertTo-Json

$addUser2Response = Invoke-RestMethod `
    -Uri ("http://localhost:7071/api/group-calendar/" + $calendarId + "/add-user") `
    -Method POST `
    -ContentType 'application/json' `
    -Body $addUser2Body

Write-Host "Add user2 to group response:" $addUser2Response
Write-Host "`n"


# ---------------------------
# 6) Remove user2 from the group
# ---------------------------
Write-Host "=== Removing user2 from group ==="
$removeUser2Body = @{
    adminId = $user1Id
    userId = $user2Id
} | ConvertTo-Json

$removeUser2Response = Invoke-RestMethod `
    -Uri ("http://localhost:7071/api/group-calendar/" + $calendarId + "/remove-user") `
    -Method POST `
    -ContentType 'application/json' `
    -Body $removeUser2Body

Write-Host "Remove user2 from group response:" $removeUser2Response
Write-Host "`n"


# ---------------------------
# 7) Add user3 to the group
# ---------------------------
Write-Host "=== Adding user3 to group ==="
$addUser3Body = @{
    adminId = $user1Id
    userId = $user3Id
} | ConvertTo-Json

$addUser3Response = Invoke-RestMethod `
    -Uri ("http://localhost:7071/api/group-calendar/" + $calendarId + "/add-user") `
    -Method POST `
    -ContentType 'application/json' `
    -Body $addUser3Body

Write-Host "Add user3 to group response:" $addUser3Response
Write-Host "`n"

Write-Host "=== Done! ==="
