# User Manual

| Field | Value |
|-------|-------|
| **Product Name** | api-rest |
| **Version** | 1.0.0 |
| **Document ID** | UM-API-REST-v1.0.0 |
| **Date** | 2026-05-08 |
| **Intended Audience** | Developers and System Administrators |
| **Classification** | Internal |

---

## Legal & Safety Notices

Copyright © 2026 David A. Mancilla. All rights reserved.

This documentation is provided "as is" without warranty of any kind.

For support: [GitHub Issues](https://github.com/dmancilla85/py-rest-server/issues)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Authentication](#3-authentication)
4. [Managing Categories](#4-managing-categories)
5. [Managing Products](#5-managing-products)
6. [Managing Users](#6-managing-users)
7. [Managing Roles](#7-managing-roles)
8. [Monitoring](#8-monitoring)
9. [Troubleshooting](#9-troubleshooting)
10. [Glossary](#10-glossary)

---

## 1. Introduction

### 1.1 What Is api-rest?

api-rest is a RESTful API server that lets you manage products, categories, users, and roles. It stores data in MongoDB and uses JWT tokens for secure access.

### 1.2 Who Should Use This Manual

This manual is for developers and system administrators who need to integrate with or operate the api-rest server.

### 1.3 What You Can Do With api-rest

- Authenticate users with email and password.
- Create, read, update, and delete product categories.
- Create, read, update, and delete products.
- Create, read, update, and delete users.
- Create, read, update, and delete roles.
- Monitor server health and view metrics.

### 1.4 How to Use This Manual

Each chapter covers one feature area. Follow the numbered steps to complete tasks. API endpoint details include the HTTP method, path, request body, and response format.

---

## 2. Getting Started

### 2.1 System Requirements

| Component | Requirement |
|-----------|-------------|
| Runtime | Python 3.14+ |
| Database | MongoDB 6.0+ |
| Operating System | Linux, macOS, or Windows |
| Network | Internet connection for MongoDB Atlas |
| Tools | `uv` package manager, curl or Postman |

### 2.2 Before You Begin

You need:
- A running MongoDB instance (local, Docker, or MongoDB Atlas).
- The MongoDB connection string.
- Python 3.14 installed on your machine.

### 2.3 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/dmancilla85/py-rest-server.git
   cd api-rest
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Create your configuration file:
   ```bash
   cp example.env .env
   ```

4. Edit `.env` and set your MongoDB connection string:
   ```
   MONGODB_CONN=mongodb+srv://user:password@cluster.mongodb.net
   MONGODB_DB=my_database
   ```

5. Start the server:
   ```bash
   uv run python main.py
   ```

   You should see output indicating the server is running on `http://0.0.0.0:5000`.

6. Verify the server is running:
   ```bash
   curl http://localhost:5000/api/health
   ```

   The system returns a JSON response with health status.

### 2.4 Using the Interactive Documentation

Open `http://localhost:5000/api/v1/ui` in your browser. The Swagger UI page shows all available endpoints. You can:
- Read endpoint descriptions and parameters.
- Click **Try it out** to send requests directly from the browser.
- View request and response examples.

---

## 3. Authentication

### 3.1 Overview

All CRUD operations require authentication. You get a JWT token by logging in with a valid email and password. Include this token in subsequent requests as a Bearer token in the `Authorization` header.

### 3.2 Logging In

**Before you begin:** You need a registered user in the system. You can create one via the API or directly in MongoDB.

1. Send a POST request to `/api/v1/auth/login`:
   ```bash
   curl -X POST http://localhost:5000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "your-password"}'
   ```

2. The system returns a response like this:
   ```json
   {
     "user": {
       "_id": "62032250fdca5ca1a170d977",
       "name": "John Smith",
       "email": "user@example.com",
       "role": "ADMIN_ROLE"
     },
     "token": "eyJhbGciOiJIUzI1NiIs..."
   }
   ```

3. Copy the `token` value.

**Result:** You are authenticated. Your token is valid for the duration specified in `JWT_LIFETIME_SECONDS` (default: 1 hour).

### 3.3 Using the Token in Requests

Include the token in every authenticated request:

```bash
curl -X GET http://localhost:5000/api/v1/categories \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

> 💡 **Tip:** Save the token in a variable to reuse it across requests:
> ```bash
> TOKEN="eyJhbGciOiJIUzI1NiIs..."
> curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/categories
> ```

---

## 4. Managing Categories

### 4.1 Overview

Categories organize your products. Each category has a name and can be active or inactive.

### 4.2 Listing All Categories

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/categories
```

To paginate:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/api/v1/categories?page=1&per_page=10"
```

The system returns a list of items and a count.

### 4.3 Creating a Category

1. Send a POST request with the category name:
   ```bash
   curl -X POST http://localhost:5000/api/v1/categories \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "PASTRIES"}'
   ```

2. The system returns HTTP 201 with the created category.

> ⚠️ **Important:** Category names must be unique. If you try to create a duplicate, the system returns HTTP 400.

### 4.4 Viewing a Single Category

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/categories/6208136134ffbeeabc4b1ead
```

Replace the ID with the actual category ID.

### 4.5 Updating a Category

```bash
curl -X PUT http://localhost:5000/api/v1/categories/6208136134ffbeeabc4b1ead \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

### 4.6 Deleting a Category

```bash
curl -X DELETE http://localhost:5000/api/v1/categories/6208136134ffbeeabc4b1ead \
  -H "Authorization: Bearer $TOKEN"
```

> 🚫 **Warning:** Deletion is permanent. There is no undo.

---

## 5. Managing Products

### 5.1 Overview

Products represent items in your catalog. Each product belongs to a category and has a name, price, and availability status.

### 5.2 Listing All Products

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/products
```

### 5.3 Creating a Product

```bash
curl -X POST http://localhost:5000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PASTRY ROLL",
    "categoryId": "62083fbdb5d9510f71cf6988",
    "price": 10.50,
    "available": true
  }'
```

### 5.4 Viewing, Updating, and Deleting Products

Use the same pattern as categories, replacing `/categories` with `/products`:

| Action | Method | Path |
|--------|--------|------|
| View | GET | `/api/v1/products/{item_id}` |
| Update | PUT | `/api/v1/products/{item_id}` |
| Delete | DELETE | `/api/v1/products/{item_id}` |

---

## 6. Managing Users

### 6.1 Overview

Users represent people who can authenticate and use the system. Each user has a name, email, password, and role.

### 6.2 Listing All Users

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/users
```

> 📝 **Note:** User list responses do not include a count field.

### 6.3 Creating a User

```bash
curl -X POST http://localhost:5000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "user@example.com",
    "password": "12345678",
    "role": "ADMIN_ROLE"
  }'
```

Valid roles: `ADMIN_ROLE`, `USER_ROLE`.

---

## 7. Managing Roles

### 7.1 Overview

Roles define access levels for users. Each role has a unique name.

### 7.2 Listing All Roles

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/roles
```

### 7.3 Creating a Role

```bash
curl -X POST http://localhost:5000/api/v1/roles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "MANAGER_ROLE"}'
```

> ⚠️ **Important:** Roles use the `role` field (not `name`) for uniqueness checks.

---

## 8. Monitoring

### 8.1 Health Check

Check if the server is running and MongoDB is connected:

```bash
curl http://localhost:5000/api/health
```

The system returns:
```json
{
  "status": "OK",
  "info": {
    "status": "OK",
    "info": "{'version': '7.0.0'}"
  }
}
```

If MongoDB is down, the status changes to ERROR.

### 8.2 Environment Information

View application metadata:

```bash
curl http://localhost:5000/api/environment
```

The system returns maintainer, repository URL, and version.

### 8.3 Prometheus Metrics

Prometheus metrics are available for scraping:

```bash
curl http://localhost:5000/api/metrics
```

---

## 9. Troubleshooting

### 9.1 Common Issues

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| Cannot connect to server | Server not running or wrong port | Check server output. Verify `PORT` setting. |
| "Email is not valid" | User does not exist | Check the email. Create the user first. |
| "The password is incorrect" | Wrong password | Verify the password. Reset if needed. |
| HTTP 401 on every request | Missing or expired token | Get a new token via `/auth/login`. |
| HTTP 400 "Item already exists" | Duplicate name | Use a different name. |
| HTTP 400 "Item ID is not valid" | Invalid ObjectId format | ObjectId must be 24 hex characters. |
| MongoDB connection error | Wrong connection string | Check `MONGODB_CONN` in `.env`. |
| No Swagger UI | Server not running | Start the server with `uv run python main.py`. |

### 9.2 Error Messages

**Error:** "Item ID is not valid."

**Meaning:** The ID you provided is not a valid MongoDB ObjectId. ObjectIds are exactly 24 hexadecimal characters.

**Solution:** Verify the ID string and try again.

**Error:** "Item not found"

**Meaning:** The resource with the given ID does not exist in the database.

**Solution:** Check the ID for typos. List all items to find the correct ID.

**Error:** "Request body is empty."

**Meaning:** The request did not include a JSON body.

**Solution:** Add `-H "Content-Type: application/json"` and include a JSON body with your request.

**Error:** "Login incorrect"

**Meaning:** Authentication failed due to missing, invalid, or incorrect credentials.

**Solution:** Ensure both `email` and `password` fields are provided and correct.

---

## 10. Glossary

| Term | Definition |
|------|------------|
| API | Application Programming Interface — a set of rules for interacting with the server |
| Bearer Token | A token included in the Authorization header to authenticate requests |
| bcrypt | A password hashing algorithm used to securely store passwords |
| CORS | Cross-Origin Resource Sharing — a security feature controlled by HTTP headers |
| CRUD | Create, Read, Update, Delete — the four basic operations for managing data |
| Endpoint | A specific URL path that accepts HTTP requests |
| JWT | JSON Web Token — a compact, URL-safe token used for authentication |
| MongoDB ObjectId | A 24-character hexadecimal string used as a unique identifier in MongoDB |
| REST | Representational State Transfer — an architectural style for designing APIs |
| Swagger UI | An interactive web interface for testing API endpoints |
| Singleton | A design pattern that ensures only one instance of a class exists |
