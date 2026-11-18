# 🛒 E-Commerce Backend API

A high-performance, production-ready e-commerce backend built with **FastAPI**, **PostgreSQL**, **Redis**, **Elasticsearch**, and **Khalti Payment Gateway** integration.

## ✨ Features

* **Multi-Token Authentication & RBAC:** Secure JWT-based authentication featuring short-lived access tokens (`15m`), HTTP-only refresh token cookies (`7d`), token blacklisting on logout, and role-based access control (`user` vs. `admin`).
* **High-Speed Product Catalog:** Read-heavy product listing endpoints cached with **Redis** (`5-minute` TTL) with automatic cache invalidation upon product creation, updates, or deletion.
* **Fuzzy Product Search:** Powered by **Elasticsearch** (`multi_match` with `AUTO` fuzziness) for fast, typo-tolerant product discovery.
* **Khalti Payment Integration:** Asynchronous payment initiation (converting NPR to Paisa) and server-side callback verification with automated inventory deduction upon transaction completion.
* **Containerized Infrastructure:** Ready-to-run `docker-compose` configuration for PostgreSQL, Redis, and Elasticsearch.

## 🛠️ Tech Stack

* **Framework:** FastAPI (Python)
* **Database & ORM:** PostgreSQL 16, SQLAlchemy
* **Caching & Session Blacklisting:** Redis 7
* **Search Engine:** Elasticsearch 8.15
* **Payment Gateway:** Khalti API (`httpx` async client)
* **Containerization:** Docker & Docker Compose

## 📁 Project Structure

```text
├── main.py             # FastAPI app initialization and lifespan events (Redis & ES)
├── router.py           # API routes for Auth, Products, Search, and Khalti Checkout
├── models.py           # SQLAlchemy database models (User, Product, Order)
├── databases.py        # PostgreSQL engine and session management
├── confige.py          # Environment variables and application settings
├── payment.py          # Asynchronous Khalti payment gateway client
├── redis_client.py     # Async Redis connection pool setup
├── elastic_client.py   # Async Elasticsearch client and index mapping
├── securitye.py        # Password hashing, JWT generation, and token blacklisting
├── schemass.py         # Pydantic request/response schemas
└── docker-compose.yml  # Infrastructure services (Postgres, Redis, Elasticsearch)
```

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* Docker & Docker Compose

### 1. Clone the Repository

```bash
git clone https://github.com
cd your-repo-name
```

### 2. Start Infrastructure Services

Spin up PostgreSQL (port `5433`), Redis (port `6379`), and Elasticsearch (port `9200`) using Docker Compose:

```bash
docker-compose up -d
```

### 3. Install Python Dependencies

Create a virtual environment and install the required packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis elasticsearch httpx python-jose passlib[bcrypt] python-multipart
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory (or export them in your shell) to override the defaults in `confige.py`:

```env
SECRET_KEY=your-production-jwt-secret-key
DATABASE_URL=postgresql://admin:secret@localhost:5433/ecommerce
REDIS_URL=redis://localhost:6379/0
KHALTI_SECRET_KEY=Key your_live_or_test_khalti_secret_key
```

### 5. Run the Application

Start the FastAPI server with Uvicorn:

```bash
uvicorn main:app --reload
```

Once running, access the interactive Swagger API documentation at:
* **Swagger UI:** `http://127.0.0`
* **ReDoc:** `http://127.0.0`

## 📡 API Endpoints Overview

### 👤 Authentication

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Register a new user account | No |
| `POST` | `/login` | Authenticate user, return access token & set HTTP-only refresh cookie | No |
| `POST` | `/refresh` | Issue a new access token using the refresh cookie | Cookie |
| `GET` | `/me` | Retrieve current authenticated user's profile | Bearer Token |
| `POST` | `/logout` | Blacklist refresh token and clear session cookie | Cookie |

### 📦 Products & Search

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/products` | List all products (cached in Redis for 5 minutes) | No |
| `GET` | `/api/products/search?q=` | Fuzzy search products by name via Elasticsearch | No |
| `POST` | `/products` | Create a new product and index in Elasticsearch | Admin |
| `PUT` | `/products/update` | Update product details and sync with Elasticsearch | Admin |
| `DELETE` | `/product/delete` | Delete a product from DB, Redis cache, and Elasticsearch | Admin |

### 💳 Checkout & Payments (Khalti)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/checkout` | Validate stock, create a `PENDING` order, and generate a Khalti payment URL | Bearer Token |
| `GET` | `/api/payment/verify-callback` | Verify Khalti `pidx` status, deduct stock, and mark order `COMPLETED` | No (Callback) |

## ⚠️ Notes for Production Deployment

* Update `KHALTI_INITIATE_URL` and `KHALTI_VERIFY_URL` in `confige.py` to Khalti's official API endpoints (`https://khalti.com` and `/lookup/` for sandbox, or `https://khalti.com...` for live).
* Update `return_url` and `website_url` in `payment.py` to match your deployed frontend domain.
* Set `secure=True` on the `refresh_token` cookie in `router.py` when serving over HTTPS.

## 📄 License

This project is licensed under the MIT License.
