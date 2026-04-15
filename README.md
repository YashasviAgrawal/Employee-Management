# 🏢 Employee Management System

A full-featured **REST API** backend for managing employees, projects, tasks, attendance, and time tracking — built with **Django 6** and **Django REST Framework**.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Roles & Permissions](#roles--permissions)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Running Tests](#running-tests)
- [Seed Data](#seed-data)

---

## ✨ Features

- 🔐 **JWT Authentication** — Secure login, logout, token refresh & password change
- 👥 **Role-Based Access Control (RBAC)** — Admin, Employee, and Client roles with fine-grained permissions
- 🗂️ **Project Management** — Create projects, assign employees, and track progress
- ✅ **Task Management** — Create tasks, self-assign, comment, and track status history
- ⏱️ **Time Logging** — Log hours against tasks with per-employee scoping
- 🗓️ **Attendance Tracking** — Sign-in, sign-out, away/return status, and daily reports
- 📊 **Role-specific Dashboards** — Tailored views for Admin, Employee, and Client
- 💬 **Task Comments** — Collaborative discussion threads on tasks
- 🧠 **Skills & Profiles** — Employee skill tags, designation, and department management
- 📦 **Supabase-ready** — Configured for PostgreSQL via Supabase (falls back to SQLite locally)
- 🐳 **Docker Support** — One-command containerized setup

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 6.0 |
| REST API | Django REST Framework 3.16 |
| Auth | SimpleJWT 5.5 |
| API Docs | drf-spectacular (OpenAPI 3) |
| Database | SQLite (dev) / PostgreSQL via Supabase (prod) |
| CORS | django-cors-headers |
| Containerization | Docker |

---

## 📁 Project Structure

```
project1/
├── app1/                   # Main application
│   ├── models.py           # Database models
│   ├── views.py            # API views (class-based)
│   ├── serializers.py      # DRF serializers
│   ├── urls.py             # URL routing
│   ├── permissions.py      # Custom RBAC permissions
│   ├── admin.py            # Django admin config
│   └── migrations/         # Database migrations
├── project1/               # Django project settings
│   ├── settings.py
│   └── urls.py
├── seed_data.py            # Script to populate demo data
├── manage.py
├── requirements.txt
├── dockerfile
└── .env.example
```

---

## 🔐 Roles & Permissions

| Action | Admin | Employee | Client |
|---|:---:|:---:|:---:|
| Register users | ✅ | ❌ | ❌ |
| Manage all users | ✅ | ❌ | ❌ |
| Create / delete projects | ✅ | ❌ | ❌ |
| View assigned projects | ✅ | ✅ | ✅ |
| Assign employees to projects | ✅ | ❌ | ❌ |
| Create / delete tasks | ✅ | ✅ | ❌ |
| Self-assign tasks | ✅ | ✅ | ❌ |
| Log time | ✅ | ✅ | ❌ |
| View task summary | ✅ | ✅ | ✅ |
| Attendance management | ✅ | ✅ | ❌ |
| Admin daily reports | ✅ | ❌ | ❌ |
| Give feedback | ✅ | ❌ | ❌ |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- pip
- (Optional) Docker

### Local Setup

**1. Clone the repository**

```bash
git clone https://github.com/YashasviAgrawal/Employee-Management.git
cd Employee-Management
```

**2. Create and activate a virtual environment**

```bash
python -m venv env

# Windows
env\Scripts\activate

# macOS / Linux
source env/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your values
```

**5. Apply migrations**

```bash
python manage.py migrate
```

**6. Create a superuser (Admin)**

```bash
python manage.py createsuperuser
```

**7. Run the development server**

```bash
python manage.py runserver
```

API is now available at `http://127.0.0.1:8000/`

---

### Docker Setup

```bash
# Build and run the container
docker build -t employee-management .
docker run -p 8000:8000 --env-file .env employee-management
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Django
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase PostgreSQL (leave empty to use SQLite)
SUPABASE_DB_HOST=your-project.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.xxxx
SUPABASE_DB_PASSWORD=your-supabase-password

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

> **Note:** Leave `SUPABASE_DB_HOST` empty to use SQLite for local development.

---

## 📡 API Endpoints

All endpoints are prefixed with `/api/`.

### 🔑 Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register a new user (Admin only) |
| POST | `/api/auth/login/` | Obtain JWT access & refresh tokens |
| POST | `/api/auth/logout/` | Blacklist refresh token |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET/PUT | `/api/auth/profile/` | View / update own profile |
| POST | `/api/auth/change-password/` | Change own password |

### 🛡️ Admin — User Management
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/users/` | List all users |
| GET/PUT/DELETE | `/api/admin/users/<id>/` | Manage a specific user |
| GET | `/api/admin/dashboard/` | Admin summary dashboard |

### 🗂️ Projects
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/projects/` | List / create projects |
| GET/PUT/DELETE | `/api/projects/<id>/` | Manage a project |
| GET | `/api/projects/<id>/tasks/` | All tasks in a project |
| GET | `/api/projects/<id>/employees/` | All employees on a project |

### 📋 Project Assignments
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/project-assignments/` | List / create assignments |
| GET/PUT/DELETE | `/api/project-assignments/<id>/` | Manage an assignment |

### ✅ Tasks
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/tasks/` | List / create tasks |
| GET/PUT/DELETE | `/api/tasks/<id>/` | Manage a task |
| GET | `/api/tasks/unassigned/` | View unassigned tasks |
| POST | `/api/tasks/<id>/self-assign/` | Self-assign a task |
| GET | `/api/tasks/<id>/history/` | Task status history |

### 💬 Task Comments
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/tasks/<id>/comments/` | List / add comments |
| GET/PUT/DELETE | `/api/comments/<id>/` | Manage a comment |

### ⏱️ Time Logs
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/timelogs/` | List / create time logs |
| GET/PUT/DELETE | `/api/timelogs/<id>/` | Manage a time log |

### 🗓️ Attendance
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/attendance/sign-in/` | Clock in |
| POST | `/api/attendance/sign-out/` | Clock out |
| POST | `/api/attendance/away/` | Mark as away |
| POST | `/api/attendance/return/` | Return from away |
| GET | `/api/attendance/today/` | Today's record |
| GET | `/api/attendance/history/` | Personal history |
| GET | `/api/admin/attendance/` | All attendance (Admin) |
| GET | `/api/admin/attendance/daily-report/` | Daily summary (Admin) |
| GET | `/api/admin/attendance/<user_id>/` | Per-user history (Admin) |

### 👤 Employee & Skills
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/skills/` | List / create skills |
| GET/PUT/DELETE | `/api/skills/<id>/` | Manage a skill |
| GET | `/api/employee-profiles/` | All employee profiles |
| GET/PUT | `/api/employee/profile/` | Own employee profile |

### 🏢 Clients & Feedback
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/clients/` | List / create clients |
| GET/PUT/DELETE | `/api/clients/<id>/` | Manage a client |
| GET/POST | `/api/feedbacks/` | List / create feedback |
| GET/PUT/DELETE | `/api/feedbacks/<id>/` | Manage feedback |

### 📊 Reports & Dashboards
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/employee/dashboard/` | Employee dashboard |
| GET | `/api/client/dashboard/` | Client dashboard |
| GET | `/api/reports/tasks/daily/` | Day-wise task report |
| GET | `/api/client/projects/<id>/task-summary/` | Client task summary |

---

## 🧪 Running Tests

```bash
python manage.py test app1
```

To run RBAC-specific tests:

```bash
python test_rbac.py
```

---

## 🌱 Seed Data

Populate the database with sample users, projects, tasks, and time logs for development/testing:

```bash
python seed_data.py
```

This creates demo Admin, Employee, and Client accounts with realistic data.

---

## 📄 License

This project is proprietary — © Revenuelogy. All rights reserved.
