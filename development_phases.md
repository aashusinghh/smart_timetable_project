# Smart University Timetable System — Development Phases

> **How to read this document**
> Each phase is split into two parallel tracks:
> - 🔧 **Backend** — Django/MySQL/Redis work
> - 🖥️ **Frontend** — React/TypeScript/Vite work
>
> Both tracks run simultaneously. At the end of every phase there is a
> **✅ Manual Test Checklist** — complete all items before starting the next phase.

---

## Phase 1 — Foundation & Authentication

**Goal:** Working Django project, MySQL database, custom user model,
role-based auth, and a React shell that can log in and display role-specific
dashboards.

**Estimated duration:** 1 – 1.5 weeks

---

### 🔧 Backend — Phase 1

#### 1.1  Project Scaffold
- [x] Create Django project under `backend/` with the folder structure from §11 of the architecture spec.
- [x] Install and configure packages:
  `django`, `djangorestframework`, `mysqlclient`, `django-cors-headers`,
  `djangochannels`, `channels-redis`, `drf-spectacular`, `python-decouple`.
- [x] Create `.env` / `settings/` split for `development.py` and `production.py`.
- [x] Connect to MySQL 8.x with `utf8mb4`, strict mode, and InnoDB.

#### 1.2  Custom User Model (`accounts` app)
- [x] `User` model inheriting `AbstractBaseUser`: fields `email`, `full_name`,
  `employee_code`, `is_active`, `is_staff`, `created_at`, `updated_at`.
- [x] `Role` model: codes `SUPER_ADMIN`, `BRANCH_COORDINATOR`, `PROFESSOR`.
- [x] `UserRoleAssignment` model: `user_id`, `role_id`, `branch_id (nullable)`.
- [x] `ProfessorProfile` model: `user_id`, `designation`, `department_id`,
  `max_hours_per_day`.

#### 1.3  Authentication API
- [x] `POST /api/auth/login` — returns JWT or session token.
- [x] `POST /api/auth/logout` — invalidates token.
- [x] `GET  /api/auth/me` — returns current user + roles.
- [x] Permission classes: `IsSuperAdmin`, `IsBranchCoordinator`, `IsProfessor`.

#### 1.4  Department & Branch API (basic, no curriculum yet)
- [x] `Department` model: `code (unique)`, `name`.
- [x] `Branch` model: `department_id`, `code`, `name`, `degree_name`,
  `max_semesters`.
- [x] CRUD endpoints: `GET/POST/PATCH /api/departments` and `/api/branches`.
- [x] Super Admin only for write operations.

#### 1.5  Django Admin
- [x] Register all Phase 1 models in `admin.py` for quick superuser management.
- [x] Create initial superuser via management command.

#### 1.6  API Documentation
- [x] Integrate `drf-spectacular` and expose `/api/schema/` and `/api/docs/`.

---

### 🖥️ Frontend — Phase 1

#### 1.1  Project Scaffold
- [x] Create Vite + React + TypeScript project under `frontend/`.
- [x] Install packages: `axios`, `react-router-dom`, `@tanstack/react-query`,
  `react-hook-form`, `zod`, `tailwindcss` (or Material UI — pick one).
- [x] Set up folder structure: `pages/`, `components/`, `services/`, `hooks/`,
  `store/`, `types/`.
- [x] Configure Vite proxy to forward `/api/*` to Django dev server.

#### 1.2  Auth Flow
- [x] **Login page** — email + password form, Zod validation, error messages.
- [x] Store JWT/token in `httpOnly` cookie or `localStorage`.
- [x] `useAuth` hook — reads current user, exposes `login()` / `logout()`.
- [x] Protected route HOC — redirects unauthenticated users to `/login`.

#### 1.3  Role-Based Dashboards (shells only)
- [x] `/dashboard/admin` — Super Admin home (placeholder cards for stats).
- [x] `/dashboard/coordinator` — Branch Coordinator home (placeholder).
- [x] `/dashboard/professor` — Professor home (placeholder).
- [x] Redirect after login to the correct dashboard based on role.

#### 1.4  Navigation Shell
- [x] Sidebar with role-conditional menu items.
- [x] Top bar showing logged-in user name + logout button.
- [x] Dark-mode toggle (persist in `localStorage`).

#### 1.5  Department & Branch Management UI (Admin only)
- [x] **Department list page** — table, add button, edit modal.
- [x] **Branch list page** — filtered by department, add/edit modal.
- [x] Use TanStack Query for data fetching and cache invalidation.

---

### ✅ Manual Test Checklist — Phase 1

| # | What to test | Expected result |
|---|---|---|
| 1 | `POST /api/auth/login` with valid credentials | 200 OK + token |
| 2 | `POST /api/auth/login` with wrong password | 401 Unauthorized |
| 3 | `GET /api/auth/me` without token | 403 Forbidden |
| 4 | `GET /api/auth/me` with token | Returns user + roles JSON |
| 5 | Create a department via `POST /api/departments` as Super Admin | 201 Created |
| 6 | Try to create a department as Professor role | 403 Forbidden |
| 7 | Login in browser → redirected to correct dashboard | ✓ |
| 8 | Logout → redirected to `/login` | ✓ |
| 9 | Add a department via UI form | Appears in list without page reload |
| 10 | Add a branch tied to the department | Appears in branch list |
| 11 | Visit `/api/docs/` | OpenAPI UI loads |

---

## Phase 2 — Academic Data Setup

**Goal:** Full academic structure — academic years/terms, professors, courses,
curriculum, cohorts, lab groups, rooms, and fixed teaching assignments — all
manageable via API and UI.

**Estimated duration:** 1.5 – 2 weeks

---

### 🔧 Backend — Phase 2

#### 2.1  Facilities (`facilities` app)
- [x] Models: `Campus`, `Building`, `Room` (room_type, capacity),
  `RoomUnavailability`.
- [x] CRUD endpoints under `/api/rooms`, `/api/buildings`, `/api/campuses`.
- [x] Seed room types: `CLASSROOM`, `COMPUTER_LAB`, `ELECTRONICS_LAB`,
  `CHEMISTRY_LAB`, `SEMINAR_HALL`.

#### 2.2  Academic Time Structure (`academics` app)
- [x] Models: `AcademicYear`, `AcademicTerm`.
- [x] `TimeSlot` model — seed all 8 daily slots (§6 of architecture spec).
- [x] CRUD endpoints under `/api/academic-years` and `/api/academic-terms`.

#### 2.3  Cohorts & Lab Groups
- [x] `Cohort` model: `branch_id`, `term_id`, `semester_no`, `section_code`,
  `student_count` — unique `(branch_id, term_id, semester_no, section_code)`.
- [x] `InstructionGroup` model: `cohort_id`, `code`, `size`.
- [x] Validate `semester_no` ≤ `branch.max_semesters`.
- [x] Endpoints: `GET/POST /api/cohorts`, `/api/instruction-groups`.

#### 2.4  Courses & Curriculum
- [x] `Course` model: `code`, `name`, `credit`, `course_type`
  (`THEORY`, `LAB`, `PROJECT`, `SEMINAR`).
- [x] `CourseDeliveryRule` model: `course_id`, `weekly_meetings`,
  `duration_slots`.
- [x] Seed required delivery rules (2-credit lab → 2x3; 3-credit → 3x1; 4-credit → 4x1).
- [x] `CurriculumItem` model: `branch_id`, `semester_no`, `course_id`.
- [x] Endpoints: `/api/courses`, `/api/curriculum`.

#### 2.5  Course Offerings & Teaching Assignments
- [x] `CourseOffering` model: `term_id`, `cohort_id`, `curriculum_item_id`.
- [x] `TeachingAssignment` model: `course_offering_id`, `professor_id`,
  `instruction_group_id (nullable)`.
- [x] Validate professor belongs to the same department (configurable).
- [x] Endpoints: `/api/course-offerings`, `/api/teaching-assignments`.

#### 2.6  Professor Management (`faculty` app)
- [x] Professor user creation flow (creates `User` + `ProfessorProfile`).
- [x] `ProfessorUnavailability` model: weekday + slot ranges.
- [x] Endpoints: `GET/POST/PATCH /api/professors`,
  `/api/professors/{id}/unavailability`.

#### 2.7  CSV Import (basic)
- [x] Import service for professors and curriculum via CSV upload.
- [x] Endpoint: `POST /api/curriculum/import`.
- [x] Validate headers, report row-level errors, import in one transaction.

---

### 🖥️ Frontend — Phase 2

#### 2.1  Professor Management (Admin UI)
- [x] **Professor list** — searchable table with department filter.
- [x] **Add/Edit professor** modal — user fields + profile fields.
- [x] Show role badge (Coordinator / Professor).

#### 2.2  Room Management UI
- [x] **Room list** — grouped by building, filterable by room type.
- [x] **Add/Edit room** modal — type selector, capacity, building picker.

#### 2.3  Academic Year & Term UI
- [x] **Academic terms list** with date range display.
- [x] **Add term** form with date pickers.

#### 2.4  Course & Curriculum UI
- [x] **Course catalog** — searchable list, add course with delivery rule form.
- [x] **Curriculum builder** — pick branch + semester, add/remove courses.
- [x] Show credit, course type, weekly meeting pattern inline.

#### 2.5  Cohort & Lab Group UI
- [x] **Cohort list** — filter by branch + term.
- [x] **Add cohort** form with semester validation against `max_semesters`.
- [x] **Lab groups panel** — expandable below each cohort, add group button.

#### 2.6  Course Offering & Teaching Assignment UI
- [x] **Offerings list** — for a selected cohort/term.
- [x] **Assign professor** form — professor picker, optional lab group.
- [x] Show current assignment inline with change option.

#### 2.7  CSV Import UI
- [x] **Import page** — drag-and-drop CSV upload, template download links.
- [x] Show parse errors per row before confirming import.
- [x] Progress indicator for large files.

---

### ✅ Manual Test Checklist — Phase 2

| # | What to test | Expected result |
|---|---|---|
| 1 | Create campus → building → room via API | Nested records created |
| 2 | Create `AcademicYear` and `AcademicTerm` | Returns with date range |
| 3 | Seed 8 time slots via management command | All 8 slots visible in DB |
| 4 | Create cohort with `semester_no` > `max_semesters` | 400 Bad Request |
| 5 | Create cohort with valid `semester_no` | 201 Created |
| 6 | Add course with `course_type = LAB`, assign delivery rule | Rule persisted |
| 7 | Add curriculum item to branch/semester | Course appears in curriculum |
| 8 | Create a course offering and assign a professor | Assignment persisted |
| 9 | Upload a valid professor CSV | Professors created, success message |
| 10 | Upload a CSV with a bad row | Error report shown per row, nothing saved |
| 11 | Open Cohort UI → add cohort with invalid semester | Inline form error shown |
| 12 | Assign professor to offering in UI | Assignment visible without reload |
| 13 | Room list groups rooms by building | Buildings act as accordion groups |

---

## Phase 3 — Timetable Grid & Conflict Validation

**Goal:** Core timetable planner — the drag-and-drop grid, real-time frontend
conflict hints, authoritative backend validation endpoint, and atomic
reservation saving.

**Estimated duration:** 2 – 2.5 weeks (most complex phase)

---

### 🔧 Backend — Phase 3

#### 3.1  Schedule Version
- [x] `ScheduleVersion` model: `term_id`, `version_no`, `status`
  (`DRAFT`, `UNDER_REVIEW`, `PUBLISHED`, `ARCHIVED`), `revision`.
- [x] Endpoint: `POST /api/timetable/versions` — create a draft for a term.
- [x] Endpoint: `GET  /api/timetable/versions` — list versions.

#### 3.2  Reservation Tables
- [x] `ProfessorSlotReservation` — unique `(version_id, professor_id, weekday, slot_no)`.
- [x] `RoomSlotReservation`      — unique `(version_id, room_id, weekday, slot_no)`.
- [x] `GroupSlotReservation`     — unique `(version_id, group_id, weekday, slot_no)`.
- [x] Run migrations; verify MySQL enforces unique constraints.

#### 3.3  Scheduled Meetings
- [x] `ScheduledMeeting` model: `schedule_version_id`, `teaching_assignment_id`,
  `weekday`, `start_slot`, `duration_slots`, `room_id`.
- [x] `MeetingInstructionGroup` model: `scheduled_meeting_id`,
  `instruction_group_id`.

#### 3.4  Validation Service (`timetable/services/validator.py`)
- [x] Implement all rules listed in §8 of the architecture spec:
  - Permission check.
  - Offering belongs to correct cohort/term.
  - Duration matches delivery rule.
  - Lab = exactly 3 continuous slots.
  - No crossing lunch or end-of-day.
  - Professor free across ALL branches.
  - Instruction groups free.
  - Room free and compatible type.
  - Room capacity sufficient.
  - Professor/room unavailability respected.
  - Weekly meeting quota not exceeded.
- [x] Endpoint: `POST /api/timetable/validate` — returns `allowed`, `conflicts[]`.

#### 3.5  Reservation Service (`timetable/services/reservation_service.py`)
- [x] Implement the 10-step atomic save described in §8:
  1. `transaction.atomic()`
  2. Re-validate permissions + version status
  3. Build `(weekday, slot_no)` pairs
  4. Check existing reservations
  5. Insert/update `scheduled_meetings`
  6. Insert reservation rows (3 tables)
  7. Catch unique-constraint violation → HTTP 409
  8. Write `ScheduleChangeAudit` record
  9. Increment `schedule_versions.revision`
  10. Trigger WebSocket broadcast (stubbed; implemented in Phase 4)
- [x] Endpoints: `POST /api/timetable/meetings`,
  `PATCH /api/timetable/meetings/{id}`,
  `DELETE /api/timetable/meetings/{id}`.

#### 3.6  Timetable Grid Endpoint
- [x] `GET /api/timetable/{version_id}/grid` — returns structured response:
  weekday, start_slot, duration_slots, room, professor, course, groups.
- [x] Support query params: `?branch_id=`, `?cohort_id=`, `?professor_id=`.

#### 3.7  Batch Update Endpoint
- [x] `POST /api/timetable/batch-update` — validates and saves multiple
  meeting changes in one atomic transaction.

#### 3.8  Audit Logging
- [x] `ScheduleChangeAudit` model: `meeting_id`, `action`, `before_json`,
  `after_json`, `user_id`, `created_at`.
- [x] Write an audit row on every create / update / delete.

---

### 🖥️ Frontend — Phase 3

#### 3.1  Timetable Grid Component
- [x] CSS-grid weekly timetable: 8 rows (time slots) x 5 columns (Mon–Fri).
- [x] Lunch gap rendered as a visual separator row.
- [x] Color-coded cells: green / red / yellow per placement state.
- [x] Scheduled meetings displayed as cards inside cells.
- [x] Meeting card shows: course name, professor, room.

#### 3.2  Drag-and-Drop Scheduling
- [x] Use `@dnd-kit/core` or HTML5 native drag-and-drop.
- [x] On drag-start: highlight valid and invalid slots with color hints.
- [x] On hover over a slot: debounced call to `POST /api/timetable/validate`.
  - Green overlay → `allowed: true`.
  - Red overlay → `allowed: false` with conflict tooltip.
  - Yellow → soft warning.
- [x] On drop: call `POST /api/timetable/meetings`, show success/error toast.

#### 3.3  Conflict Panel
- [x] Side panel listing all current conflicts for the open draft version.
- [x] Each item shows: type (PROFESSOR_BUSY, ROOM_BUSY, GROUP_BUSY), slot, reason.
- [x] Auto-refreshes on every save action.

#### 3.4  Meeting Detail Modal
- [x] Click on a meeting card → modal with full details.
- [x] Buttons: **Edit** (change room / slot), **Delete**.
- [x] Confirmation prompt before delete.

#### 3.5  Cohort Timetable Selector
- [x] Dropdown chain: branch → term → cohort → schedule version.
- [x] Grid updates reactively when selection changes.

#### 3.6  Available Rooms Panel
- [x] For the currently hovered slot, list free compatible rooms.
- [x] Filter by room type matching the course.

#### 3.7  Validation Feedback UI
- [x] Global error banner for 409 Conflict responses.
- [x] Per-slot tooltip with conflict type and message.
- [x] Toast notifications for successful saves.

---

### ✅ Manual Test Checklist — Phase 3

| # | What to test | Expected result |
|---|---|---|
| 1 | `POST /api/timetable/validate` for a free slot | `allowed: true` |
| 2 | Validate a slot where professor is already booked | `allowed: false`, `PROFESSOR_BUSY` |
| 3 | Validate a slot that crosses lunch | 400 / `allowed: false` |
| 4 | Save a meeting to a free slot | 201 Created, reservation rows inserted |
| 5 | Save a second meeting for same professor + slot | 409 Conflict |
| 6 | Two coordinators save simultaneously (two browser tabs) | Exactly one succeeds, other gets 409 |
| 7 | Delete a meeting | Reservation rows removed from DB |
| 8 | Edit a meeting's room | Old room reservation removed, new one created |
| 9 | Open timetable grid in browser | 8 slots × 5 days grid renders |
| 10 | Drag course onto a free slot | Green overlay shown; saved on drop |
| 11 | Drag course onto occupied professor slot | Red overlay; tooltip shows reason |
| 12 | Save a 3-hour lab | Three reservation rows per table (professor, room, group) |
| 13 | Conflict panel shows existing clashes | All conflicts listed |
| 14 | `GET /api/timetable/{version_id}/grid` | Returns all meetings for version |
| 15 | Audit log entry created after save | Row in `schedule_change_audits` |

---

## Phase 4 — Real-Time Updates, Publication & Professor Views

**Goal:** WebSocket live updates, full draft→publish workflow, professor
personal timetable view, branch timetable view, and audit log UI.

**Estimated duration:** 1.5 weeks

---

### 🔧 Backend — Phase 4

#### 4.1  Django Channels & Redis
- [x] Configure `CHANNEL_LAYERS` with Redis backend.
- [x] `asgi.py` — route HTTP to Django, WS to Channels.
- [x] `TimetableConsumer`: handles `/ws/timetable/{version_id}/`.
- [x] `NotificationConsumer`: handles `/ws/notifications/`.

#### 4.2  WebSocket Events
- [x] Broadcast after every save: `meeting.created`, `meeting.updated`,
  `meeting.deleted`, `schedule.revision.changed`.
- [x] After publish: broadcast `schedule.published`.
- [x] After conflict on save: send `validation.conflict` to saving client only.

#### 4.3  Publication Workflow
- [x] `POST /api/timetable/{version_id}/submit-review` → status: `UNDER_REVIEW`.
- [x] `POST /api/timetable/{version_id}/publish` (Admin only):
  - Run final full-sweep validation.
  - If clean: status → `PUBLISHED`, archive previous published version.
  - If conflicts: return 422 with conflict list.
- [x] Never mutate a `PUBLISHED` version; new changes require a new `DRAFT`.

#### 4.4  Read-Only Timetable Endpoints
- [x] `GET /api/my-timetable` — professor's own published timetable.
- [x] `GET /api/professors/{id}/timetable` — admin view.
- [x] `GET /api/branches/{id}/timetable` — branch public timetable.

#### 4.5  Holiday Calendar & Date Overrides
- [x] `HolidayCalendar` model: `term_id`, `date`, `reason`.
- [x] `DateOverride` model: `scheduled_meeting_id`, `original_date`,
  `new_date`, `new_slot`, `status` (CANCELLED / RESCHEDULED).
- [x] Endpoints: `/api/holidays`, `/api/date-overrides`.

#### 4.6  Audit Log API
- [x] `GET /api/audit-logs` — paginated, filterable by meeting / user / date.
- [x] Super Admin only.

---

### 🖥️ Frontend — Phase 4

#### 4.1  WebSocket Client
- [x] `useTimetableSocket(versionId)` hook connecting to `/ws/timetable/{version_id}/`.
- [x] On `meeting.*` events → update TanStack Query cache without reload.
- [x] "Live" animated indicator when WS is connected.
- [x] Reconnect with exponential back-off on disconnect.

#### 4.2  Version Status Bar
- [x] Display current version status badge.
- [x] Coordinator: **Submit for Review** button (DRAFT only).
- [x] Admin: **Publish** button (UNDER_REVIEW only) with confirmation dialog.
- [x] Publish button disabled with tooltip when conflicts exist.

#### 4.3  Professor Personal Timetable
- [x] Route: `/my-timetable` (Professor role, read-only).
- [x] Weekly grid coloured by course type.
- [x] **Print** button triggers `window.print()`.

#### 4.4  Branch Timetable View
- [x] Route: `/branches/:id/timetable` (all roles, read-only).
- [x] Cohort/section selector at top; no edit controls shown.

#### 4.5  Schedule Review Page (Admin)
- [x] List all `UNDER_REVIEW` versions with summary stats.
- [x] Click → read-only grid with conflict overlay.
- [x] **Approve & Publish** / **Send Back to Draft** buttons.

#### 4.6  Audit Log Viewer (Admin UI)
- [x] Paginated table: timestamp, user, action, before/after JSON diff.
- [x] Filter by date range, user, meeting.
- [x] Expandable row to show full diff.

#### 4.7  Holiday & Date Override UI
- [x] **Holiday calendar** — month view, add/remove holidays.
- [x] **Date overrides** — list of cancelled/rescheduled meetings, add override from meeting detail.

---

### ✅ Manual Test Checklist — Phase 4

| # | What to test | Expected result |
|---|---|---|
| 1 | Save a meeting in Tab A while Tab B is open | Tab B grid updates automatically |
| 2 | Disconnect internet then reconnect | WS reconnects, stale data refreshed |
| 3 | Submit a draft version for review | Status → `UNDER_REVIEW` |
| 4 | Edit a meeting in `UNDER_REVIEW` as Coordinator | 403 Forbidden |
| 5 | Publish version with no conflicts as Admin | Status → `PUBLISHED`, broadcast received |
| 6 | Publish version with existing conflicts | 422, conflict list returned |
| 7 | Professor visits `/my-timetable` | Sees only their own classes |
| 8 | Coordinator visits `/branches/:id/timetable` | Cohort timetable, no edit controls |
| 9 | Add a holiday date | Visually marked on timetable |
| 10 | Create a date override (cancel a class) | Appears in list, original slot shown as cancelled |
| 11 | Visit audit log page | All mutations listed with JSON diff |
| 12 | Filter audit log by date range | Only matching rows shown |

---

## Phase 5 — Smart Auto-Scheduling (OR-Tools)

**Goal:** Automated timetable generation using Google OR-Tools CP-SAT as a
background Celery task, with a preview UI before committing.

**Estimated duration:** 2 weeks

---

### 🔧 Backend — Phase 5

#### 5.1  Celery Setup
- [x] Configure `celery.py` in `config/`.
- [x] Install `celery[redis]` and `django-celery-results`.
- [x] Register task queues: `default`, `scheduler`, `imports`.
- [x] Add Celery Beat for recurring maintenance tasks.

#### 5.2  Generator Service (`scheduler/services/generator.py`)
- [x] Load all `TeachingAssignment` records for the requested term.
- [x] Build CP-SAT model with variables `(assignment, weekday, start_slot, room)`.
- [x] Implement all hard constraints from §10 of architecture spec.
- [x] Implement soft constraints with CP-SAT objective function.
- [x] Solve with configurable time limit (default 60 s).

#### 5.3  Scheduling Task
- [x] Celery task `generate_timetable(version_id, branch_ids, time_limit)`.
- [x] Save progress percentage to Redis for polling.
- [x] On completion: store candidate meetings in `AutoScheduleProposal` table.
- [x] Endpoint: `POST /api/timetable/{version_id}/generate` → returns `task_id`.
- [x] Endpoint: `GET  /api/tasks/{task_id}/status` → returns progress + result.

#### 5.4  Proposal Review & Commit
- [x] `GET /api/timetable/{version_id}/proposals` — return proposed meetings.
- [x] `POST /api/timetable/{version_id}/commit-proposal` — batch reservation-save.
- [x] If conflict at commit time → 409 with detail.

#### 5.5  Scoring Report
- [x] Scoring service evaluates schedule against soft constraints.
- [x] Endpoint: `GET /api/timetable/{version_id}/score` — score breakdown.

---

### 🖥️ Frontend — Phase 5

#### 5.1  Auto-Generate Button
- [x] **Auto-Generate** button on timetable planner (Admin/Coordinator).
- [x] Configuration dialog: select branches, time limit, replace-existing checkbox.
- [x] Calls `POST /api/timetable/{version_id}/generate`.

#### 5.2  Generation Progress UI
- [x] Full-screen progress modal with animated spinner.
- [x] Percentage from polling `GET /api/tasks/{task_id}/status`.
- [x] Cancel button.
- [x] On completion → transition to Proposal Preview.

#### 5.3  Proposal Preview Page
- [x] Read-only timetable grid showing the proposed schedule.
- [x] Sidebar: quality score, unscheduled offerings, soft-constraint breakdown.
- [x] **Commit Proposal** and **Discard** buttons.

#### 5.4  Scoring Dashboard
- [x] Visual bar chart for soft-constraint scores.
- [x] Table of unscheduled offerings with reason.

---

### ✅ Manual Test Checklist — Phase 5

| # | What to test | Expected result |
|---|---|---|
| 1 | Start Celery worker and beat | Workers start without errors |
| 2 | Trigger auto-generate for a branch | Task starts, `task_id` returned |
| 3 | Poll task status during generation | Progress percentage increases |
| 4 | Proposal returned after generation | 0 hard constraint violations |
| 5 | Commit proposal with no conflicts | All meetings saved, reservations created |
| 6 | Commit proposal when professor manually booked in conflicting slot | 409 Conflict, proposal not committed |
| 7 | View quality score | Score report with soft constraint breakdown |
| 8 | Discard proposal | Proposal removed, draft unaffected |
| 9 | Check professor never double-booked in generated schedule | No PROFESSOR_BUSY conflicts in sweep |
| 10 | Generate for branch with only lab courses | Labs placed in 3-continuous slots, no lunch crossing |

---

## Phase 6 — Reporting, Export, Security & Deployment

**Goal:** PDF/CSV exports, printable views, final security hardening,
production Docker deployment, and end-to-end tests.

**Estimated duration:** 1 – 1.5 weeks

---

### 🔧 Backend — Phase 6

#### 6.1  Export Service (`reports/services/export_service.py`)
- [ ] CSV export: branch timetable, professor timetable, room utilisation.
- [ ] PDF export using `weasyprint` or `reportlab`.
- [ ] Role-gated: professors can only export their own timetable.
- [ ] Endpoints: `GET /api/exports/branch-timetable?format=csv|pdf`,
  `GET /api/exports/professor-timetable?format=csv|pdf`.

#### 6.2  Security Hardening
- [ ] HTTPS redirect in Nginx config.
- [ ] CSRF protection on all non-GET endpoints.
- [ ] Rate limiting on `POST /api/auth/login` (5 attempts / minute).
- [ ] All secrets loaded from environment variables.
- [ ] Every query row-level scoped by role and branch.
- [ ] Dependency audit: `pip audit` or `safety check`.

#### 6.3  Production Configuration
- [ ] `settings/production.py` with `DEBUG=False`, allowed hosts, static files.
- [ ] `Dockerfile` for Django app (multi-stage build).
- [ ] `docker-compose.yml`: Django + Nginx + MySQL + Redis + Celery worker.
- [ ] Nginx config: serve React static files, proxy `/api/` and `/ws/`.
- [ ] Health check endpoint: `GET /api/health/`.

#### 6.4  Automated Tests
- [ ] `pytest-django` suite covering all Phase 1–5 checklist scenarios.
- [ ] Concurrent-save test: two threads, same professor same slot — verify one 409.
- [ ] Playwright E2E: login → drag-and-drop → save a meeting.

---

### 🖥️ Frontend — Phase 6

#### 6.1  Printable Timetable
- [ ] `/print/branch/:id/timetable` — print-optimised route (no sidebar/nav).
- [ ] Print CSS: one page per cohort, B&W-safe colours.
- [ ] **Print** button triggers `window.print()`.

#### 6.2  CSV / PDF Export UI
- [ ] Export button with format picker (CSV / PDF) on all timetable pages.
- [ ] Download progress indicator for large exports.

#### 6.3  Notifications Centre
- [ ] Bell icon in top bar with unread count badge.
- [ ] Uses `/ws/notifications/` WebSocket.
- [ ] Types: schedule published, submitted for review, conflict on save.

#### 6.4  Error & Empty States
- [ ] Empty state illustrations: no cohorts, no timetable, nothing scheduled.
- [ ] Network error boundary with retry button.
- [ ] Custom 403 / 404 pages.

#### 6.5  Performance & Polish
- [ ] Lazy-load timetable grid (code split).
- [ ] Memoize grid cells to prevent full re-renders.
- [ ] Loading skeletons for all fetch states.
- [ ] Keyboard navigation + ARIA labels on grid.

---

### ✅ Manual Test Checklist — Phase 6

| # | What to test | Expected result |
|---|---|---|
| 1 | Export branch timetable as CSV | Valid CSV downloaded |
| 2 | Export professor timetable as PDF | Well-formatted PDF |
| 3 | Professor exports another professor's timetable | 403 Forbidden |
| 4 | Print timetable page | Print dialog opens, layout fits A4 |
| 5 | Wrong password 6 times | 6th attempt returns 429 Too Many Requests |
| 6 | `docker compose up` | All services start without errors |
| 7 | Access app via Nginx URL | React app served, API responds |
| 8 | `GET /api/health/` | `{"status": "ok"}` |
| 9 | Notification appears when admin publishes schedule | Bell badge updates in real time |
| 10 | Network disconnected mid-drag | Error toast shown, placement cancelled gracefully |
| 11 | `pytest` suite | All tests pass (0 failures) |
| 12 | Playwright E2E: login → schedule meeting | Pass |

---

## Summary Table

| Phase | Name | Duration | Key Deliverable |
|---|---|---|---|
| 1 | Foundation & Auth | 1–1.5 wks | Login, roles, departments, branches |
| 2 | Academic Data Setup | 1.5–2 wks | Courses, curriculum, cohorts, rooms, assignments |
| 3 | Timetable Grid & Validation | 2–2.5 wks | Drag-and-drop planner + conflict prevention |
| 4 | Real-Time & Publication | 1.5 wks | WebSockets, publish workflow, professor view |
| 5 | Smart Auto-Scheduling | 2 wks | OR-Tools generation, preview, commit |
| 6 | Reports, Security & Deploy | 1–1.5 wks | Exports, hardening, Docker, E2E tests |

**Total estimated duration:** 9 – 11 weeks

---

## Tech-Stack Quick Reference

| Concern | Technology |
|---|---|
| Backend | Python 3.12+, Django, Django REST Framework |
| Database | MySQL 8.x (InnoDB, utf8mb4, strict mode) |
| Real-time | Django Channels, Redis |
| Background tasks | Celery + Redis, Celery Beat |
| Auto-scheduling | Google OR-Tools CP-SAT |
| Frontend | React, TypeScript, Vite |
| State / data | TanStack Query |
| Forms | React Hook Form + Zod |
| Drag-and-drop | @dnd-kit/core |
| Styling | Tailwind CSS or Material UI |
| API docs | drf-spectacular (OpenAPI) |
| Testing | pytest-django, Playwright |
| Deployment | Docker, Nginx, Daphne/Uvicorn |

