
---

# 🌐 Collaborative Calendar App – Backend  
**Cloud Application Development (Group M)**  

A serverless collaborative calendar backend built using **Azure Functions**, **Cosmos DB**, and **Python**.  
This app supports **user registration, login, event management, and notifications**.  

---

## 📁 Project Structure  

```
collaborative-calendar-backend/
├── app/
│   ├── __init__.py          # App package initialization
│   ├── database.py          # Cosmos DB connection setup
│   ├── models.py            # Pydantic models for Users and Events
│   ├── user_routes.py       # Logic for user registration and login
│   └── main.py              # Azure Function handlers for API routes
├── function_app.py          # Azure Functions entry point
├── tests/                   # Unit tests for registration and login
│   ├── test_register.py     # Tests for user registration
│   └── test_login.py        # Tests for user login
├── .env                     # Environment variables (Cosmos DB and Function URL)
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation (This file)
```

---

## 🚀 Quick Start  

### 1. Clone the Repository  

```bash
git clone https://github.com/SarveshMina/cloud-app-group-cw.git
cd collaborative-calendar-backend
```  

---

### 2. Activate Virtual Environment  

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```  

---

### 3. Install Dependencies  

```bash
pip install -r requirements.txt
```  

---

### 4. Start Azure Functions  

```bash
func start
```  

The app will run at:  
```
http://localhost:7071/
```  

---

## 🔑 Environment Variables  

Create a `.env` file in the root directory to store sensitive environment variables.  

```ini
COSMOS_CONNECTION_STRING=<Your-Cosmos-DB-Connection-String>
AZURE_FUNC_URL=http://localhost:7071/
```  

- **COSMOS_CONNECTION_STRING** – Connection string for Cosmos DB.  
- **AZURE_FUNC_URL** – Azure Function URL (for local or Azure deployment).  

---

## 📋 Cosmos DB Setup  

### 1. Create a Cosmos DB Account  

```bash
az cosmosdb create --name CalendarDBAccount --resource-group <YourResourceGroup>
```  

---

### 2. Create a Database  

```bash
az cosmosdb sql database create --account-name CalendarDBAccount --name CalendarDB
```  

---

### 3. Create Containers (with Partition Keys)  

```bash
az cosmosdb sql container create --account-name CalendarDBAccount \
  --database-name CalendarDB --name Users \
  --partition-key-path "/userId"

az cosmosdb sql container create --account-name CalendarDBAccount \
  --database-name CalendarDB --name UserEvents \
  --partition-key-path "/calendarId"

az cosmosdb sql container create --account-name CalendarDBAccount \
  --database-name CalendarDB --name Notifications \
  --partition-key-path "/recipientId"

az cosmosdb sql container create --account-name CalendarDBAccount \
  --database-name CalendarDB --name CollaborativeCalendars \
  --partition-key-path "/groupId"

az cosmosdb sql container create --account-name CalendarDBAccount \
  --database-name CalendarDB --name Availability \
  --partition-key-path "/userId"
```  

Alternatively, containers can be created directly from the **Azure Portal**.  

---

## 🧪 Running Unit Tests  

Unit tests are located in the `tests/` directory.  

- **`test_register.py`** – Tests user registration with boundary checks.  
- **`test_login.py`** – Tests login flow, including invalid credentials and non-existent users.  

---

### 1. Run All Tests  

```bash
python -m unittest discover tests
```  

---

### 2. Run Specific Tests  

```bash
python -m unittest tests/test_register.py
python -m unittest tests/test_login.py
```  

---

## 📄 API Endpoints  

### 1. **User Registration**  
**POST** `/register`  
Registers a new user.  

**Payload:**  
```json
{
  "username": "newUser",
  "password": "StrongPass123",
  "email": "user@example.com"
}
```  

**Responses:**  
- `201 Created` – User registered successfully  
- `400 Bad Request` – Username already exists or invalid username/password  

---

### 2. **User Login**  
**POST** `/login`  
Logs in an existing user.  

**Payload:**  
```json
{
  "username": "newUser",
  "password": "StrongPass123"
}
```  

**Responses:**  
- `200 OK` – Login successful  
- `401 Unauthorized` – Invalid credentials  
- `404 Not Found` – User not found  

---

## ✅ Testing Coverage  

### Registration Tests  
- ✅ Successful user registration  
- ❌ Duplicate username (expect `400`)  
- ❌ Short/long username validation  
- ❌ Short/long password validation  

---

### Login Tests  
- ✅ Successful login  
- ❌ Invalid password (expect `401`)  
- ❌ Non-existent user (expect `404`)  
- ❌ Missing credentials (expect `400`)  

---

## ⚙️ Troubleshooting  
---

**Q: How do I delete test users in Cosmos DB?**  
A:  

```bash
az cosmosdb sql container delete --account-name CalendarDBAccount \
  --database-name CalendarDB --name Users
```  

Alternatively, delete users manually using the **Azure Portal**.  

---
