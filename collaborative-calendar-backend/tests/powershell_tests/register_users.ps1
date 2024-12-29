# ---------------------------
# Register user1
# ---------------------------
Write-Host "=== Registering user1 ==="
$user1Body = @{
    username = "user1"
    password = "Password123"
    email = "user1@example.com"
} | ConvertTo-Json -Depth 3

$user1Response = Invoke-RestMethod `
    -Uri "http://localhost:7071/api/register" `
    -Method POST `
    -ContentType 'application/json' `
    -Body $user1Body

Write-Host "user1 response:" $user1Response
Write-Host "`n"


# ---------------------------
# Register user2
# ---------------------------
# ---------------------------
Write-Host "=== Registering user2 ==="
$user2Body = @{
    username = "user2-test"  # Modified username
    password = "Password123"
    email = "user2@example.com"
} | ConvertTo-Json -Depth 3

$user2Response = Invoke-RestMethod `
    -Uri "http://localhost:7071/api/register" `
    -Method POST `
    -ContentType 'application/json' `
    -Body $user2Body

Write-Host "user2 response:" $user2Response
Write-Host "`n"


Write-Host "=== Done! ==="
