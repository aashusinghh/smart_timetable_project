# Smart University Timetable System — Architecture Specification

## 1. Purpose and scope

This document specifies a smart university timetable system for 8+ departments, each containing one or more branches. The system uses Python, Django, MySQL, and a web frontend to manage academic data, fixed professor-subject mappings, timetable creation, real-time conflict validation, timetable publication, and professor timetable viewing.

**Terminology note:** this design uses **Django with MySQL**. `Djongo` is a MongoDB adapter and is not appropriate for this relational scheduling system.

### Functional requirements covered

- Multiple departments, each with multiple branches.
- Different programme lengths: for example B.Tech (8 semesters), MCA (6 semesters), and M.Tech (4 semesters).
- A professor may teach multiple subjects across different branches.
- The professor mapped to a course offering is fixed; the system schedules time and room, not professor allocation.
- Super Admin, Branch Coordinator, and Professor roles.
- Eight daily one-hour slots: four from 08:30–12:30 and four from 14:00–18:00.
- Credit/contact rules:
  - 2-credit lab: two 3-hour continuous lab meetings per week.
  - 3-credit theory: three 1-hour meetings per week.
  - 4-credit theory: four 1-hour meetings per week.
- Real-time frontend feedback before placement and authoritative backend validation at save time.
- No professor can be scheduled in overlapping slots anywhere in the university.

## 2. Recommended architecture

```text
React / TypeScript frontend
        │ REST API + WebSocket updates
        ▼
Django + Django REST Framework
├── Authentication and role-based access control
├── Academic-data management
├── Timetable validation and reservation engine
├── Automated scheduling engine
├── Audit and reporting
└── WebSocket consumers
        │
        ├── MySQL 8.x (permanent data)
        ├── Redis (WebSocket channel layer, cache, queues)
        └── Celery workers (imports, reports, schedule generation)
```

### Technology choices

| Layer | Recommended technology | Purpose |
|---|---|---|
| Backend | Python 3.12+, Django | Main application framework and ORM |
| API | Django REST Framework | Secure REST endpoints |
| Database | MySQL 8.x with InnoDB | Relational, transactional persistent storage |
| MySQL driver | `mysqlclient` | Django database connectivity |
| Frontend | React, TypeScript, Vite | Interactive timetable UI |
| Realtime | Django Channels, Redis, WebSockets | Live timetable updates and conflict visibility |
| Background work | Celery, Redis | Imports, exports, automated scheduling |
| Optimizer | Google OR-Tools CP-SAT | Optional automatic timetable generation |
| Documentation | drf-spectacular / OpenAPI | API documentation |
| Deployment | Docker, Nginx, Uvicorn or Daphne | Production hosting |
| Monitoring | Sentry and structured logs | Error and operational monitoring |
| Tests | pytest, pytest-django, Playwright | Backend and browser testing |

Use MySQL with `InnoDB`, `utf8mb4`, strict SQL mode, foreign keys, and properly indexed lookup columns. Do not use MyISAM because timetable correctness depends on transactions and foreign-key integrity.

## 3. Academic domain model

```text
Department
 └── Branch
      └── Semester / Cohort
           └── Instruction Groups (lab groups)
                └── Course Offering
                     └── Fixed Teaching Assignment
                          └── Scheduled Meetings
```

Example:

```text
Department: Computer Science
Branch: B.Tech CSE
Semester: 5
Cohort: B.Tech CSE Sem 5, Section A
Instruction groups: A-L1, A-L2
Course: Database Management Systems
Professor: Dr. Sharma
Meetings: Monday 08:30, Wednesday 10:30, Friday 14:00
```

A branch owns its programme duration:

| Programme | `max_semesters` example |
|---|---:|
| B.Tech | 8 |
| MCA | 6 |
| M.Tech | 4 |

The system must validate that a cohort semester is between `1` and its branch's `max_semesters`.

## 4. Roles and access control

Use a custom Django `User` model plus scoped role assignments.

| Role | Permissions |
|---|---|
| Super Admin | All departments, branches, users, academic data, rooms, schedules, approvals, publishing, reports, and audit logs |
| Branch Coordinator | Manage cohorts, course offerings, teaching assignments, and draft timetable entries only for assigned branch(es) |
| Professor | Read-only access to personal timetable, assigned subjects, sections, rooms, and published schedule notices |
| Optional Department Admin | Manage all branches in an assigned department |

A person can have more than one role. For example, a professor may also be a branch coordinator.

Branch coordinators must not edit another branch's timetable. They still receive a conflict response if a professor is occupied by another branch; detailed cross-branch data can remain visible only to Super Admins.

## 5. Database design

All application tables should include, where relevant:

```text
id
created_at
updated_at
created_by
updated_by
is_active
```

Use `BIGINT` or UUID primary keys consistently. Use lowercase, snake_case table names.

### 5.1 Identity and access

| Table | Key columns | Purpose |
|---|---|---|
| `users` | id, email, full_name, password, employee_code | Login account |
| `roles` | id, code | `SUPER_ADMIN`, `BRANCH_COORDINATOR`, `PROFESSOR` |
| `user_role_assignments` | user_id, role_id, branch_id nullable | Role membership, optionally scoped to one branch |
| `professor_profiles` | user_id, designation, department_id, max_hours_per_day | Professor-specific data |

`branch_id` is null only for university-wide roles such as Super Admin.

### 5.2 Academic structure

| Table | Key columns | Important constraints |
|---|---|---|
| `departments` | code, name | `code` unique |
| `branches` | department_id, code, name, degree_name, max_semesters | unique `(department_id, code)` |
| `academic_years` | name, start_date, end_date | e.g. `2026-27` |
| `academic_terms` | academic_year_id, name, start_date, end_date | e.g. Odd Semester |
| `cohorts` | branch_id, term_id, semester_no, section_code, student_count | unique `(branch_id, term_id, semester_no, section_code)` |
| `instruction_groups` | cohort_id, code, size | Lab batches such as `A-L1`, `A-L2` |

`instruction_groups` represent the smallest student units for collision detection. For a cohort with no lab divisions, create one group such as `ALL`.

For a class with two lab groups:

```text
CSE Sem 3, Section A
├── A-L1: 30 students
└── A-L2: 30 students
```

A theory class targets both groups. A lab targets only its assigned group. This prevents a theory class from colliding with either lab group, but permits separate lab groups to use different rooms at the same time.

### 5.3 Courses, curriculum, and fixed teaching assignments

| Table | Key columns | Purpose |
|---|---|---|
| `courses` | code, name, credit, course_type | University course catalog |
| `course_delivery_rules` | course_id, weekly_meetings, duration_slots | Weekly scheduling rule |
| `curriculum_items` | branch_id, semester_no, course_id | Course included in a branch semester |
| `course_offerings` | term_id, cohort_id, curriculum_item_id | Course taught to a cohort in a particular term |
| `teaching_assignments` | course_offering_id, professor_id, instruction_group_id nullable | Fixed professor allocation |

Recommended course types:

```text
THEORY
LAB
PROJECT
SEMINAR
```

Required delivery rules:

| Course pattern | `weekly_meetings` | `duration_slots` | Weekly contact hours |
|---|---:|---:|---:|
| 2-credit lab | 2 | 3 | 6 |
| 3-credit theory | 3 | 1 | 3 |
| 4-credit theory | 4 | 1 | 4 |

Store contact rules separately from credits. The requirement defines a 2-credit lab as six scheduled contact hours, so validation must use the configured delivery rule rather than infer duration from credits.

### 5.4 Facilities

| Table | Key columns |
|---|---|
| `campuses` | name, code |
| `buildings` | campus_id, name |
| `rooms` | building_id, room_no, room_type, capacity |
| `room_unavailability` | room_id, date or weekday, start_slot, end_slot, reason |

Room types may include:

```text
CLASSROOM
COMPUTER_LAB
ELECTRONICS_LAB
CHEMISTRY_LAB
SEMINAR_HALL
```

Each course can optionally have allowed room types. A lab must be scheduled only in a compatible room with sufficient capacity.

### 5.5 Timetable, versioning, and audit data

| Table | Key columns | Purpose |
|---|---|---|
| `time_slots` | slot_no, start_time, end_time, session | Fixed university daily slots |
| `schedule_versions` | term_id, version_no, status, revision | Draft and published schedules |
| `scheduled_meetings` | schedule_version_id, teaching_assignment_id, weekday, start_slot, duration_slots, room_id | A recurring weekly lecture/lab |
| `meeting_instruction_groups` | scheduled_meeting_id, instruction_group_id | Student groups that attend a meeting |
| `holiday_calendar` | term_id, date, reason | No-teaching dates |
| `date_overrides` | scheduled_meeting_id, original_date, new_date, new_slot, status | One-time cancel/reschedule records |
| `schedule_change_audits` | meeting_id, action, before_json, after_json, user_id | Full audit history |

Schedule version statuses:

```text
DRAFT
UNDER_REVIEW
PUBLISHED
ARCHIVED
```

### 5.6 Conflict-reservation tables

These tables are the correctness mechanism for timetable conflict prevention.

| Table | Key columns | Required unique constraint |
|---|---|---|
| `professor_slot_reservations` | schedule_version_id, professor_id, weekday, slot_no, scheduled_meeting_id | `(schedule_version_id, professor_id, weekday, slot_no)` |
| `room_slot_reservations` | schedule_version_id, room_id, weekday, slot_no, scheduled_meeting_id | `(schedule_version_id, room_id, weekday, slot_no)` |
| `group_slot_reservations` | schedule_version_id, instruction_group_id, weekday, slot_no, scheduled_meeting_id | `(schedule_version_id, instruction_group_id, weekday, slot_no)` |

Every one-hour portion of a meeting creates reservation records. A three-hour lab creates three professor, three room, and three group reservation rows.

Example for a Monday 08:30–11:30 lab:

```text
Professor P12 + Monday + Slot 1
Professor P12 + Monday + Slot 2
Professor P12 + Monday + Slot 3
```

The unique constraint prevents a professor, room, or student group from being double-booked even when two coordinators save simultaneously.

## 6. Daily time-slot configuration

Seed these slots:

| Slot | Time | Session |
|---:|---|---|
| 1 | 08:30–09:30 | Morning |
| 2 | 09:30–10:30 | Morning |
| 3 | 10:30–11:30 | Morning |
| 4 | 11:30–12:30 | Morning |
| 5 | 14:00–15:00 | Afternoon |
| 6 | 15:00–16:00 | Afternoon |
| 7 | 16:00–17:00 | Afternoon |
| 8 | 17:00–18:00 | Afternoon |

The 12:30–14:00 lunch period is intentionally absent from `time_slots`.

Allowed three-hour lab starts:

```text
08:30 → 11:30
09:30 → 12:30
14:00 → 17:00
15:00 → 18:00
```

The validation service rejects a meeting that crosses lunch or extends past 18:00. Monday–Friday can be seeded initially, while teaching days remain configurable for a future Saturday schedule.

## 7. Timetable workflow and versioning

Never modify a published timetable in place.

```text
Published schedule
        │
        ▼
Create term-level draft version
        │
        ▼
Branch coordinators edit only their branch data
        │
        ▼
Global conflict and coverage validation
        │
        ▼
Super Admin review
        │
        ▼
Publish
```

All branches must exist within the same term-level draft version. This permits professor collision checks across the whole institution.

Professors see the most recent published schedule by default. Draft viewing can be enabled later if desired.

## 8. Real-time timetable validation

### User interaction flow

1. A coordinator selects an offering; the professor mapping is prefilled and not editable during placement.
2. The coordinator drags the lecture or lab onto the timetable grid.
3. The frontend performs an immediate local check using the currently loaded schedule matrix.
4. The frontend calls the backend validation endpoint, debounced during drag/hover.
5. The backend returns allowed/conflict/warning information.
6. The frontend shows a green, red, or yellow placement state.
7. On drop/save, the backend validates again and writes reservations in one transaction.
8. A WebSocket message updates all other users viewing that schedule version.

The frontend is only an experience improvement. Backend validation and database reservations are authoritative.

### Validation endpoint

```text
POST /api/timetable/validate
```

Example request:

```json
{
  "schedule_version_id": 14,
  "teaching_assignment_id": 201,
  "weekday": "MONDAY",
  "start_slot": 2,
  "duration_slots": 3,
  "room_id": 35,
  "instruction_group_ids": [71]
}
```

Example response:

```json
{
  "allowed": false,
  "conflicts": [
    {
      "type": "PROFESSOR_BUSY",
      "slot": 3,
      "message": "Professor is already assigned at 10:30–11:30."
    },
    {
      "type": "ROOM_BUSY",
      "slot": 4,
      "message": "Computer Lab 2 is occupied."
    }
  ]
}
```

### Validation rules

The backend must verify:

- The user has permission for the relevant branch.
- The offering belongs to the selected cohort and academic term.
- The professor assignment is fixed and valid.
- The meeting duration matches the configured course rule.
- A lab is exactly three continuous slots.
- A meeting does not cross lunch or the end of day.
- The professor is free across every branch and department.
- All target instruction groups are free.
- The room is free and compatible with the course.
- Room capacity is enough for target group sizes.
- Professor and room unavailability is respected.
- A course is not scheduled more than its required weekly meetings/hours.
- The course still has enough unscheduled required meetings.

### Safe save implementation

In `reservation_service.py`:

1. Start `transaction.atomic()`.
2. Revalidate request permissions and schedule status.
3. Build every affected `(weekday, slot_no)` pair.
4. Check existing reservations, excluding the meeting being edited.
5. Insert/update the `scheduled_meetings` row.
6. Insert professor, room, and group reservation rows.
7. If a unique constraint fails, roll back and return HTTP `409 Conflict`.
8. Create `schedule_change_audits` record.
9. Increment `schedule_versions.revision`.
10. Broadcast a WebSocket `meeting.created` or `meeting.updated` event after commit.

For multi-meeting moves or swaps, use a batch endpoint that validates all proposed changes as one transaction.

## 9. Global professor collision prevention

Professor collisions are prevented by `professor_slot_reservations`.

When a coordinator schedules a class, Django tries to create one reservation for each occupied slot. If another department has already scheduled that professor in an identical schedule version, weekday, and slot, MySQL rejects the duplicate unique key.

This works across:

- Departments
- Branches
- Semesters
- Sections
- Theory lectures
- Labs
- Manual edits
- Auto-generated schedules

The API should return `409 Conflict` with a clear message. Branch coordinators can be told that the professor is busy without exposing another branch's private course details.

## 10. Smart automatic scheduling

Manual drag-and-drop scheduling should be delivered first. Automatic generation should create a draft proposal, never publish automatically.

Use Google OR-Tools CP-SAT.

### Hard constraints

- Every 3-credit theory offering gets exactly three 1-hour meetings per week on distinct days.
- Every 4-credit theory offering gets exactly four 1-hour meetings per week on distinct days.
- Every 2-credit lab gets exactly two three-hour continuous meetings per week.
- A professor cannot overlap with another meeting.
- A room cannot overlap with another meeting.
- An instruction group cannot overlap with another meeting.
- No meeting can cross lunch or daily bounds.
- Labs require compatible lab rooms.
- Room capacity must be sufficient.
- The fixed professor assignment must be used.
- Only allowed teaching days and slots may be used.

### Soft constraints and scoring

- Minimize student timetable gaps.
- Minimize professor timetable gaps.
- Balance class load between weekdays.
- Avoid too many continuous teaching hours for one professor.
- Prefer professor availability and room preferences.
- Avoid undesirable first/last slots if configured.
- Spread repeated sessions across the week.

The generator returns a candidate schedule. The user reviews it, and the normal reservation-based batch-save process validates and persists it.

## 11. Backend project structure

```text
backend/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── accounts/
│   ├── academics/
│   ├── faculty/
│   ├── facilities/
│   ├── timetable/
│   ├── scheduler/
│   ├── notifications/
│   ├── imports/
│   └── reports/
├── tests/
└── manage.py
```

Important backend services:

```text
timetable/services/validator.py
timetable/services/reservation_service.py
timetable/services/publish_service.py
scheduler/services/generator.py
scheduler/services/scoring.py
imports/services/csv_import_service.py
reports/services/export_service.py
```

Keep scheduling rules in service classes, not inside views, serializers, or frontend code.

## 12. API design

### Authentication

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### Master data

```text
GET, POST, PATCH /api/departments
GET, POST, PATCH /api/branches
GET, POST, PATCH /api/professors
GET, POST, PATCH /api/courses
GET, POST, PATCH /api/rooms
GET, POST, PATCH /api/academic-terms
```

### Curriculum and fixed assignments

```text
POST /api/curriculum/import
GET  /api/cohorts
POST /api/course-offerings
POST /api/teaching-assignments
```

### Timetable management

```text
GET    /api/timetable/{version_id}/grid
POST   /api/timetable/validate
POST   /api/timetable/meetings
PATCH  /api/timetable/meetings/{id}
DELETE /api/timetable/meetings/{id}
POST   /api/timetable/batch-update
POST   /api/timetable/{version_id}/generate
POST   /api/timetable/{version_id}/submit-review
POST   /api/timetable/{version_id}/publish
```

### Read-only timetable access

```text
GET /api/my-timetable
GET /api/professors/{id}/timetable
GET /api/branches/{id}/timetable
```

### WebSockets

```text
/ws/timetable/{schedule_version_id}/
/ws/notifications/
```

Event types:

```text
meeting.created
meeting.updated
meeting.deleted
validation.conflict
schedule.revision.changed
schedule.published
```

## 13. Frontend architecture

Recommended frontend stack:

```text
React
TypeScript
Vite
TanStack Query
React Hook Form
Zod
FullCalendar or a custom CSS-grid timetable
Native WebSocket client
Tailwind CSS or Material UI
```

### Required screens

- Login
- Super Admin dashboard
- Department and branch management
- Professor management
- Course and curriculum management
- Fixed professor-course mapping
- Cohort and lab-group setup
- Room management
- Timetable planner
- Conflict panel
- Automatic generator preview
- Schedule review and publish page
- Professor personal timetable
- Branch timetable
- Printable timetable
- CSV/PDF export
- Audit-log viewer

### Timetable interface

```text
                Monday   Tuesday   Wednesday   Thursday   Friday
08:30–09:30       ■         ■          ■           ■         ■
09:30–10:30       ■         ■          ■           ■         ■
10:30–11:30       ■         ■          ■           ■         ■
11:30–12:30       ■         ■          ■           ■         ■
14:00–15:00       ■         ■          ■           ■         ■
15:00–16:00       ■         ■          ■           ■         ■
16:00–17:00       ■         ■          ■           ■         ■
17:00–18:00       ■         ■          ■           ■         ■
```

Placement states:

| Colour | Meaning |
|---|---|
| Green | Valid placement |
| Red | Hard conflict; saving is prohibited |
| Yellow | Valid but violates a soft preference, such as an undesirable professor gap |

Tooltips should explain the exact reason, such as "Professor is occupied at 10:30–11:30." Super Admins may see the conflicting timetable record; branch coordinators should normally see only a privacy-safe reason.

## 14. Initial university data required

Collect and validate these through CSV/Excel templates:

- Departments and branch names
- Degree name and semester count for each branch
- Academic-year and term dates
- Semester-wise curriculum
- Subject code, name, credits, course type, and contact pattern
- Professor details
- Fixed professor-subject-branch mappings
- Cohorts, sections, and student counts
- Lab group divisions and group sizes
- Rooms, room types, and capacity
- Professor unavailable slots, if applicable
- Room unavailable slots, if applicable
- Holidays, examinations, and university events
- Teaching-load policies and preferences
- Existing timetable data, if migration is required

Import workflow:

```text
Upload CSV/Excel
→ validate headers and rows
→ display errors and warnings
→ user corrects or confirms
→ import in one transaction
→ write audit records
```

## 15. Security and production operations

- Use Django password hashing; never store plain-text passwords.
- Enforce HTTPS.
- Use secure session cookies, CSRF protection, and server-side authorization.
- Scope every write/query by role and branch.
- Audit every timetable mutation and publication action.
- Rate-limit login and sensitive API routes.
- Store secrets in environment variables or a secret manager.
- Use separate development, staging, and production environments.
- Take encrypted daily database backups and test restoration each term.
- Do not allow direct production database edits.
- Use Sentry/logging for application errors and suspicious activity.
- Protect exported files and reports with role permissions.

Recommended deployment layout:

```text
Nginx
 ├── React static assets
 └── Django ASGI application
      ├── HTTP/API workers
      └── WebSocket workers

MySQL
Redis
Celery worker
Celery beat scheduler
```

## 16. Testing strategy

Automated tests must cover:

- Authentication and role permissions
- Branch-scoped coordinator access
- Course delivery rules for 2-, 3-, and 4-credit subjects
- Three-hour lab continuity
- Lunch-break and end-of-day rejection
- Professor conflict across branches
- Room conflict
- Instruction-group conflict
- Room capacity/type validation
- Concurrent timetable-save attempts
- Draft/review/publish workflow
- CSV import validation and rollback
- WebSocket updates
- Automatic-scheduling output validity
- Browser drag-and-drop and conflict messaging

Critical acceptance scenario:

```text
Coordinator A schedules Professor X in B.Tech CSE at Monday 09:30.
Coordinator B attempts to schedule Professor X in MCA at Monday 09:30.
Expected result: the second save is rejected with HTTP 409 Conflict,
even if both actions occur at nearly the same time.
```

## 17. Delivery phases

1. **Foundation** — Django project, MySQL, authentication, roles, departments, branches, professors, rooms.
2. **Academic setup** — semesters, cohorts, lab groups, courses, curriculum, fixed teaching assignments.
3. **Manual scheduler** — timetable grid, validation service, reservation tables, real-time conflict display.
4. **Publication** — draft versions, approval, publishing, professor views, reports, audit logs.
5. **Smart scheduling** — OR-Tools generation, optimization scores, preview, and batch commit.
6. **Production hardening** — security review, backups, monitoring, load testing, deployment, and staff training.

## 18. Primary architectural decision

The reservation tables are the core of the design. They enforce professor, room, and student-group non-overlap at the database level instead of trusting browser validation. This protects the timetable from race conditions, simultaneous coordinator actions, and cross-branch professor clashes.

