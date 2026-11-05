# Smart University Timetable System

A multi-department, multi-branch smart university timetable scheduling and management system built with **Django**, **Django REST Framework**, **MySQL**, **Redis**, **Django Channels**, **Celery**, **Google OR-Tools CP-SAT**, and **React + TypeScript (Vite)**.

---

## Architecture & Technology Stack

- **Backend:** Python 3.11+, Django 5+, Django REST Framework
- **Database:** MySQL 8.x with InnoDB, strict mode, utf8mb4 (SQLite fallback supported for local dev/testing)
- **Real-Time WebSockets:** Django Channels, Channels-Redis
- **Task Queues & Background Work:** Celery 5.6+, Redis, django-celery-results
- **Automatic Scheduling Optimizer:** Google OR-Tools CP-SAT
- **API Documentation:** drf-spectacular (OpenAPI 3 / Swagger / Redoc)
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Lucide React

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Redis 6.x+** (running on port 6379)
- **MySQL 8.x** (optional for local SQLite testing)

---

## Backend Setup

### 1. Virtual Environment & Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Installed packages include:
- `ortools>=9.8.0` (Google OR-Tools CP-SAT)
- `celery>=5.3.0` & `django-celery-results>=2.5.0`
- `channels` & `channels-redis`
- `mysqlclient` & `pymysql`
- `djangorestframework` & `djangorestframework-simplejwt`

### 2. Environment Variables

Create `.env` in the `backend/` folder based on `.env.example`:

```env
SECRET_KEY=django-insecure-smart-university-timetable-secret-key-change-in-prod
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (mysql for MySQL 8.x, sqlite for local development)
DB_ENGINE=mysql
DB_NAME=smart_timetable
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Channels & Redis
USE_INMEMORY_CHANNELS=False
REDIS_URL=redis://127.0.0.1:6379/1

# Celery Configuration
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=django-db
CELERY_CACHE_BACKEND=django-cache
CELERY_TASK_ALWAYS_EAGER=False
```

### 3. Migrations & Database Initialization

```bash
python manage.py migrate
```

### 4. Seed Time Slots & Academic Data

```bash
python manage.py shell -c "from apps.timetable.models import *; print('Ready')"
```

---

## Background Services (Celery & Redis)

### Celery Queues

The system routes background tasks to dedicated queues:
- `scheduler`: OR-Tools CP-SAT auto-scheduling tasks
- `imports`: Curriculum & faculty CSV bulk import tasks
- `default`: General notifications & maintenance tasks

### 1. Start Redis

```bash
redis-server
```

### 2. Start Celery Worker

To start a worker processing all queues:

```bash
cd backend
source venv/bin/activate
celery -A config worker --loglevel=info -Q default,scheduler,imports
```

Or run dedicated scheduler workers:

```bash
celery -A config worker --loglevel=info -Q scheduler -c 4
```

### 3. Start Celery Beat (Periodic Tasks)

Celery Beat handles scheduled maintenance (e.g. daily cleanup of stale/discarded proposals):

```bash
cd backend
source venv/bin/activate
celery -A config beat --loglevel=info
```

### 4. Start Django Development Server (ASGI)

```bash
cd backend
source venv/bin/activate
python manage.py runserver 8000
```

---

## Frontend Setup

### 1. Install Node Dependencies

```bash
cd frontend
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

Frontend will run at `http://localhost:5173`. Vite proxies `/api/*` and `/ws/*` requests to Django at `http://127.0.0.1:8000`.

### 3. Production Build & Type Checking

```bash
cd frontend
npm run build
```

---

## Phase V — Smart Auto-Scheduling (OR-Tools CP-SAT)

### Overview

Phase V adds automated timetable generation using Google OR-Tools CP-SAT as an asynchronous Celery task. The engine respects all institutional hard constraints, evaluates soft constraints, and persists candidate proposals for coordinator/admin review before committing to the live timetable.

### Hard Constraints Enforced:
1. **Three-credit theory:** Exactly 3 one-hour meetings per week on distinct days.
2. **Four-credit theory:** Exactly 4 one-hour meetings per week on distinct days.
3. **Two-credit lab:** Exactly 2 three-hour continuous meetings per week on distinct days.
4. **Allowed lab start slots:** Slots 1 (08:30), 2 (09:30), 5 (14:00), 6 (15:00).
5. **No lunch crossing:** No class crosses 12:30–14:00 (between slots 4 and 5).
6. **No end-of-day violation:** All classes finish by slot 8 (18:00).
7. **No professor overlapping:** University-wide cross-department conflict prevention.
8. **No room overlapping:** Room double-booking strictly prevented.
9. **No student group overlapping:** Same cohort or lab group cannot be in two places.
10. **Room type compatibility:** Labs placed only in compatible lab rooms (`COMPUTER_LAB`, `ELECTRONICS_LAB`, `CHEMISTRY_LAB`).
11. **Sufficient capacity:** Room capacity must satisfy cohort/group size.
12. **Unavailability respected:** Professor and room leaves/unavailability strictly avoided.

### Soft Constraints & Quality Scoring:
- Minimizing student timetable gaps (idle waiting hours between classes).
- Minimizing professor timetable gaps.
- Balancing daily contact hours across weekdays (Monday–Friday).
- Preventing faculty fatigue (avoiding > 3 consecutive teaching hours).
- Prioritizing prime mid-day slots (slots 2..7) over early slot 1 or late slot 8.
- Spreading repeated meetings evenly across the week (e.g. Mon-Wed-Fri).

### Auto-Scheduling Workflow

1. **Initiate Generation:**
   On the Timetable Planner, click the **Auto-Generate** button.
   Configure:
   - Target Branches (multi-select)
   - Solver Time Limit (slider from 10s to 300s, default 60s)
   - Replace-Existing toggle (replace selected branch meetings or schedule remaining)
   Click **Start Auto-Scheduling**.

2. **Track Progress:**
   The generation progress modal polls `/api/tasks/{task_id}/status` in real time with animated percentage and step updates.

3. **Preview Proposal:**
   Upon solver completion, review the read-only timetable proposal:
   - Weekly grid with course, professor, room, and lab indicators
   - Solver status (`OPTIMAL` / `FEASIBLE`)
   - Authoritative Quality Score (0–100) and Soft Constraint Breakdown
   - Table of unscheduled offerings with exact diagnostic reasons

4. **Commit or Discard:**
   - **Commit Proposal:** Atomically re-validates all placements against live database state. If concurrent manual changes conflict, rolls back and returns `409 Conflict`. Otherwise locks reservations and updates schedule revision.
   - **Discard Proposal:** Cleans up proposal without touching live timetable.

---

## API Endpoints (Phase 5)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/timetable/{version_id}/generate` | Dispatch Celery generation task | Coordinator / Admin |
| `GET` | `/api/tasks/{task_id}/status` | Poll generation progress and result | Authenticated |
| `GET` | `/api/timetable/{version_id}/proposals` | List candidate proposals | Authenticated |
| `GET` | `/api/timetable/{version_id}/proposals/{id}` | Retrieve proposal detail | Authenticated |
| `POST` | `/api/timetable/{version_id}/commit-proposal` | Atomically commit proposal to live timetable | Coordinator / Admin |
| `POST` | `/api/timetable/{version_id}/discard-proposal` | Discard candidate proposal | Coordinator / Admin |
| `GET` | `/api/timetable/{version_id}/score` | Evaluate quality score and breakdown | Authenticated |

---

## Testing

### Run Backend Tests

```bash
cd backend
source venv/bin/activate
DB_ENGINE=sqlite python manage.py test tests
```

To run Phase 5 auto-scheduling tests specifically:

```bash
DB_ENGINE=sqlite python manage.py test tests.test_phase5
```

### Run Frontend Tests

```bash
cd frontend
npm test
```

### Run Frontend Build Check

```bash
cd frontend
npm run build
```

