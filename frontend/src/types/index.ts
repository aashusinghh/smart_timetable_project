export type RoleCode = 'SUPER_ADMIN' | 'BRANCH_COORDINATOR' | 'PROFESSOR';

export interface Role {
  id: number;
  code: RoleCode;
  name: string;
  description?: string;
}

export interface BranchSummary {
  id: number;
  code: string;
  name: string;
  degree_name: string;
}

export interface DepartmentSummary {
  id: number;
  code: string;
  name: string;
}

export interface UserRoleAssignment {
  id: number;
  role: Role;
  branch?: BranchSummary | null;
  created_at: string;
}

export interface ProfessorProfile {
  id: number;
  designation: string;
  department: DepartmentSummary;
  max_hours_per_day: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  employee_code?: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  roles: RoleCode[];
  role_assignments: UserRoleAssignment[];
  professor_profile?: ProfessorProfile | null;
  created_at: string;
  updated_at?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse extends AuthTokens {
  user: User;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  description?: string;
  branches_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Branch {
  id: number;
  department: number;
  department_name?: string;
  department_code?: string;
  code: string;
  name: string;
  degree_name: string;
  max_semesters: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ==========================================
// Phase 2 Types
// ==========================================

export type RoomType =
  | 'CLASSROOM'
  | 'COMPUTER_LAB'
  | 'ELECTRONICS_LAB'
  | 'CHEMISTRY_LAB'
  | 'SEMINAR_HALL';

export interface Campus {
  id: number;
  code: string;
  name: string;
  address?: string;
  is_active: boolean;
  buildings_count: number;
  created_at: string;
  updated_at: string;
}

export interface Building {
  id: number;
  campus: number;
  campus_name?: string;
  campus_code?: string;
  code: string;
  name: string;
  floors_count: number;
  is_active: boolean;
  rooms_count: number;
  created_at: string;
  updated_at: string;
}

export interface Room {
  id: number;
  building: number;
  building_code?: string;
  building_name?: string;
  campus_code?: string;
  room_no: string;
  name?: string;
  room_type: RoomType;
  room_type_display?: string;
  capacity: number;
  floor: number;
  has_projector: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RoomUnavailability {
  id: number;
  room: number;
  room_str?: string;
  weekday?: number | null;
  specific_date?: string | null;
  start_slot: number;
  end_slot: number;
  reason: string;
  created_at: string;
}

export interface AcademicYear {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  is_active: boolean;
  terms_count: number;
  created_at: string;
  updated_at: string;
}

export type TermType = 'ODD' | 'EVEN' | 'SUMMER';

export interface AcademicTerm {
  id: number;
  academic_year: number;
  year_name?: string;
  name: string;
  term_type: TermType;
  term_type_display?: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type TimeSession = 'MORNING' | 'AFTERNOON';

export interface TimeSlot {
  id: number;
  slot_no: number;
  start_time: string;
  end_time: string;
  session: TimeSession;
  session_display?: string;
  is_active: boolean;
}

export interface InstructionGroup {
  id: number;
  cohort: number;
  cohort_str?: string;
  code: string;
  name?: string;
  size: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Cohort {
  id: number;
  branch: number;
  branch_code?: string;
  branch_name?: string;
  term: number;
  term_name?: string;
  semester_no: number;
  section_code: string;
  student_count: number;
  is_active: boolean;
  instruction_groups: InstructionGroup[];
  created_at: string;
  updated_at: string;
}

export type CourseType = 'THEORY' | 'LAB' | 'PROJECT' | 'SEMINAR';

export interface CourseDeliveryRule {
  id?: number;
  course?: number;
  weekly_meetings: number;
  duration_slots: number;
  preferred_room_type?: string;
  total_contact_hours?: number;
}

export interface Course {
  id: number;
  department?: number | null;
  department_code?: string;
  department_name?: string;
  code: string;
  name: string;
  credit: number;
  course_type: CourseType;
  course_type_display?: string;
  description?: string;
  is_active: boolean;
  delivery_rule?: CourseDeliveryRule | null;
  created_at: string;
  updated_at: string;
}

export interface CurriculumItem {
  id: number;
  branch: number;
  branch_code?: string;
  semester_no: number;
  course: number;
  course_code?: string;
  course_name?: string;
  course_type?: CourseType;
  course_credit?: number;
  is_elective: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CourseOffering {
  id: number;
  term: number;
  term_name?: string;
  cohort: number;
  cohort_str?: string;
  curriculum_item: number;
  course_code?: string;
  course_name?: string;
  course_type?: CourseType;
  course_credit?: number;
  assignments_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeachingAssignment {
  id: number;
  course_offering: number;
  cohort_str?: string;
  course_code?: string;
  course_name?: string;
  professor: number;
  professor_name?: string;
  professor_email?: string;
  instruction_group?: number | null;
  group_code?: string | null;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProfessorListItem {
  id: number;
  email: string;
  full_name: string;
  employee_code?: string | null;
  is_active: boolean;
  designation: string;
  department_id: number;
  department_code: string;
  department_name: string;
  max_hours_per_day: number;
  roles: RoleCode[];
  assignments_count: number;
  created_at: string;
}

export interface ProfessorUnavailability {
  id: number;
  professor?: number;
  professor_name?: string;
  weekday?: number | null;
  specific_date?: string | null;
  start_slot: number;
  end_slot: number;
  reason: string;
  created_at: string;
}

export interface CSVImportError {
  row: number;
  message: string;
}

export interface CSVImportResult {
  success: boolean;
  imported_count: number;
  errors: CSVImportError[];
}


// ==========================================
// Phase 3 Types: Timetable Grid & Reservations
// ==========================================

export type ScheduleStatus = 'DRAFT' | 'UNDER_REVIEW' | 'PUBLISHED' | 'ARCHIVED';

export interface ScheduleVersion {
  id: number;
  term: number;
  term_name?: string;
  version_no: number;
  status: ScheduleStatus;
  status_display?: string;
  revision: number;
  name?: string;
  notes?: string;
  meetings_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ScheduledMeeting {
  id: number;
  schedule_version: number;
  teaching_assignment: number;
  weekday: number; // 1=Mon..5=Fri
  weekday_display?: string;
  start_slot: number; // 1..8
  duration_slots: number; // 1 or 3
  end_slot: number;
  room: number;
  room_no?: string;
  building_code?: string;
  building_name?: string;
  room_type?: RoomType;
  course_code?: string;
  course_name?: string;
  course_type?: CourseType;
  course_credit?: number;
  professor_id?: number;
  professor_name?: string;
  cohort_id?: number;
  cohort_str?: string;
  branch_id?: number;
  branch_code?: string;
  group_codes?: string[];
  created_at: string;
  updated_at: string;
}

export interface ConflictDetail {
  type: string;
  slot?: number;
  message: string;
}

export interface ValidationResponse {
  allowed: boolean;
  conflicts: ConflictDetail[];
  warnings?: ConflictDetail[];
}

export interface ValidatePlacementInput {
  schedule_version_id: number;
  teaching_assignment_id: number;
  weekday: number;
  start_slot: number;
  duration_slots: number;
  room_id: number;
  instruction_group_ids?: number[];
  exclude_meeting_id?: number | null;
}

export interface SaveMeetingInput {
  schedule_version_id: number;
  teaching_assignment_id: number;
  weekday: number;
  start_slot: number;
  duration_slots: number;
  room_id: number;
  instruction_group_ids?: number[];
  existing_meeting_id?: number | null;
}

export interface AvailableRoomItem {
  id: number;
  room_no: string;
  name?: string;
  building_code: string;
  room_type: RoomType;
  room_type_display: string;
  capacity: number;
  has_projector: boolean;
}

export interface TimetableGridResponse {
  schedule_version_id: number;
  revision: number;
  status: ScheduleStatus;
  meetings: ScheduledMeeting[];
  total_count: number;
}

// Phase 4 Types

export interface HolidayCalendar {
  id: number;
  term: number;
  term_name?: string;
  date: string;
  name: string;
  description?: string;
  is_academic_holiday: boolean;
  created_at: string;
  updated_at: string;
}

export type OverrideStatus = 'CANCELLED' | 'RESCHEDULED';

export interface DateOverride {
  id: number;
  scheduled_meeting: number;
  meeting_course?: string;
  meeting_professor?: string;
  original_date: string;
  new_date?: string | null;
  new_start_slot?: number | null;
  new_room?: number | null;
  new_room_no?: string | null;
  status: OverrideStatus;
  status_display?: string;
  reason?: string;
  created_by_email?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLogEntry {
  id: number;
  schedule_version: number;
  meeting_id?: number | null;
  action: string;
  before_json: Record<string, any>;
  after_json: Record<string, any>;
  user_email?: string | null;
  created_at: string;
}

export interface MyTimetableResponse {
  schedule_version_id?: number | null;
  term_name?: string | null;
  status?: ScheduleStatus | null;
  professor_id: number;
  professor_name: string;
  meetings: ScheduledMeeting[];
  unavailability: Array<{
    id: number;
    weekday: number | null;
    start_slot: number;
    end_slot: number;
    reason: string;
  }>;
  holidays: Array<{
    id: number;
    date: string;
    name: string;
    is_academic_holiday: boolean;
  }>;
}

export interface BranchTimetableResponse {
  branch_id: number;
  branch_code: string;
  branch_name: string;
  schedule_version_id?: number | null;
  meetings: ScheduledMeeting[];
}

export interface ValidationSweepResponse {
  valid: boolean;
  total_conflicts: number;
  conflicts: Array<{
    type: string;
    slot?: number;
    message: string;
    meeting_id?: number;
    course_code?: string;
  }>;
}

export interface WebSocketTimetableEvent {
  type: string;
  payload?: any;
  revision?: number;
  status?: ScheduleStatus;
}

