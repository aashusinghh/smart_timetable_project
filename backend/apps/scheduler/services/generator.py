import time
import logging
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from collections import defaultdict
from ortools.sat.python import cp_model

from django.db.models import Q
from apps.timetable.models import (
    ScheduleVersion,
    ScheduledMeeting,
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
)
from apps.academics.models import (
    Cohort,
    TeachingAssignment,
    Course,
    InstructionGroup,
)
from apps.facilities.models import Room, RoomUnavailability
from apps.faculty.models import ProfessorUnavailability
from .scoring import ScheduleScorer

logger = logging.getLogger(__name__)


class SolverProgressCallback(cp_model.CpSolverSolutionCallback):
    """Callback to receive intermediate solutions and notify progress."""
    def __init__(self, on_progress: Optional[Callable[[int, str], None]] = None):
        super().__init__()
        self.on_progress = on_progress
        self.solution_count = 0
        self.start_time = time.time()

    def on_solution_callback(self):
        self.solution_count += 1
        elapsed = time.time() - self.start_time
        obj = self.objective_value
        if self.on_progress:
            # Scale progress roughly between 40% and 85% during solver iterations
            pct = min(85, 40 + self.solution_count * 5)
            self.on_progress(pct, f"Found candidate schedule #{self.solution_count} (Objective: {obj:.0f})")


class TimetableGenerator:
    """
    CP-SAT Optimization Engine for University Timetable Auto-Scheduling.
    Implements all Hard Constraints (§10) and Soft Constraints (§10).
    """

    ALLOWED_LAB_STARTS = [1, 2, 5, 6]  # 08:30, 09:30, 14:00, 15:00
    THEORY_STARTS = [1, 2, 3, 4, 5, 6, 7, 8]

    def __init__(
        self,
        schedule_version: ScheduleVersion,
        branch_ids: Optional[List[int]] = None,
        time_limit: int = 60,
        replace_existing: bool = False,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        self.schedule_version = schedule_version
        self.term = schedule_version.term
        self.branch_ids = branch_ids or []
        self.time_limit = max(5, int(time_limit))
        self.replace_existing = replace_existing
        self.progress_callback = progress_callback

    def _notify(self, percentage: int, message: str):
        if self.progress_callback:
            try:
                self.progress_callback(percentage, message)
            except Exception as e:
                logger.warning(f"Error in progress callback: {e}")

    def generate(self) -> Dict[str, Any]:
        """
        Main entry point: loads data, builds CP-SAT model, solves, and returns proposal payload.
        """
        start_time = time.time()
        self._notify(10, "Loading academic structure and teaching assignments...")

        # 1. Resolve target cohorts
        cohort_qs = Cohort.objects.filter(
            term=self.term,
            is_active=True
        ).select_related('branch')

        if self.branch_ids:
            cohort_qs = cohort_qs.filter(branch_id__in=self.branch_ids)

        cohorts = list(cohort_qs)
        if not cohorts:
            return {
                'solver_status': 'INFEASIBLE',
                'quality_score': 0.0,
                'proposed_meetings': [],
                'unscheduled_offerings': [{'reason': 'No active cohorts found for selected branches.'}],
                'constraint_score_breakdown': {},
                'generation_metadata': {'solve_time_seconds': round(time.time() - start_time, 2)},
            }

        cohort_ids = [c.id for c in cohorts]

        # 2. Load Teaching Assignments
        assignments_qs = TeachingAssignment.objects.filter(
            course_offering__cohort_id__in=cohort_ids,
            is_active=True
        ).select_related(
            'course_offering__cohort__branch',
            'course_offering__curriculum_item__course__delivery_rule',
            'course_offering__curriculum_item__course',
            'professor__professor_profile',
            'instruction_group'
        ).order_by('id')

        assignments = list(assignments_qs)
        if not assignments:
            return {
                'solver_status': 'FEASIBLE',
                'quality_score': 100.0,
                'proposed_meetings': [],
                'unscheduled_offerings': [],
                'constraint_score_breakdown': ScheduleScorer.calculate_score([]),
                'generation_metadata': {'solve_time_seconds': round(time.time() - start_time, 2), 'message': 'No teaching assignments required.'},
            }

        self._notify(20, "Loading room facilities, capacities, and unavailability records...")

        # 3. Load Rooms
        rooms = list(Room.objects.filter(is_active=True).select_related('building'))
        lab_rooms = [r for r in rooms if r.room_type in [
            Room.RoomType.COMPUTER_LAB,
            Room.RoomType.ELECTRONICS_LAB,
            Room.RoomType.CHEMISTRY_LAB,
        ]]
        theory_rooms = [r for r in rooms if r.room_type in [
            Room.RoomType.CLASSROOM,
            Room.RoomType.SEMINAR_HALL,
        ]]

        # 4. Load Unavailabilities
        prof_unavail_qs = ProfessorUnavailability.objects.all()
        prof_unavail: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)
        for u in prof_unavail_qs:
            days = [u.weekday] if u.weekday else list(range(1, 6))
            for d in days:
                for s in range(u.start_slot, u.end_slot + 1):
                    prof_unavail[u.professor_id].add((d, s))

        room_unavail_qs = RoomUnavailability.objects.all()
        room_unavail: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)
        for u in room_unavail_qs:
            days = [u.weekday] if u.weekday else list(range(1, 6))
            for d in days:
                for s in range(u.start_slot, u.end_slot + 1):
                    room_unavail[u.room_id].add((d, s))

        # 5. Load Existing Reservations (Fixed obstacles)
        fixed_prof_slots: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)
        fixed_room_slots: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)
        fixed_group_slots: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)
        existing_assigned_counts: Dict[int, int] = defaultdict(int)

        existing_meetings = ScheduledMeeting.objects.filter(
            schedule_version=self.schedule_version
        ).select_related('teaching_assignment').prefetch_related('meeting_instruction_groups')

        for em in existing_meetings:
            em_asgn = em.teaching_assignment
            em_branch_id = em_asgn.course_offering.cohort.branch_id

            if self.replace_existing and em_branch_id in (self.branch_ids or [c.branch_id for c in cohorts]):
                # This meeting will be replaced by the proposal; do not treat as fixed obstacle
                continue

            # Record fixed reservation
            existing_assigned_counts[em_asgn.id] += 1
            slots = list(range(em.start_slot, em.start_slot + em.duration_slots))
            for s in slots:
                fixed_prof_slots[em_asgn.professor_id].add((em.weekday, s))
                fixed_room_slots[em.room_id].add((em.weekday, s))
                for mig in em.meeting_instruction_groups.all():
                    fixed_group_slots[mig.instruction_group_id].add((em.weekday, s))

        self._notify(30, "Formulating CP-SAT constraint satisfaction problem...")

        # 6. Deconstruct assignments into meeting requirements
        meeting_tasks = []
        unscheduled_offerings = []

        for asgn in assignments:
            offering = asgn.course_offering
            course = offering.curriculum_item.course
            rule = getattr(course, 'delivery_rule', None)

            # Determine weekly meetings & duration
            if rule:
                weekly_meetings = rule.weekly_meetings
                duration_slots = rule.duration_slots
            else:
                if course.course_type == Course.CourseType.LAB:
                    weekly_meetings = 2
                    duration_slots = 3
                elif course.credit >= 4:
                    weekly_meetings = 4
                    duration_slots = 1
                else:
                    weekly_meetings = max(1, course.credit)
                    duration_slots = 1

            # If not replacing existing, subtract already scheduled count
            if not self.replace_existing:
                scheduled_so_far = existing_assigned_counts[asgn.id]
                meetings_to_schedule = max(0, weekly_meetings - scheduled_so_far)
            else:
                meetings_to_schedule = weekly_meetings

            if meetings_to_schedule == 0:
                continue

            # Determine student groups & size
            target_groups = []
            if asgn.instruction_group:
                target_groups = [asgn.instruction_group]
                required_capacity = asgn.instruction_group.size
            else:
                target_groups = list(offering.cohort.instruction_groups.all())
                required_capacity = sum(g.size for g in target_groups) if target_groups else offering.cohort.student_count

            group_ids = [g.id for g in target_groups]

            # Find compatible candidate rooms
            if course.course_type == Course.CourseType.LAB:
                candidate_rooms = [r for r in lab_rooms if r.capacity >= required_capacity]
            else:
                candidate_rooms = [r for r in theory_rooms if r.capacity >= required_capacity]

            if not candidate_rooms:
                unscheduled_offerings.append({
                    'assignment_id': asgn.id,
                    'course_code': course.code,
                    'course_name': course.name,
                    'cohort': str(offering.cohort),
                    'professor': asgn.professor.full_name,
                    'reason': f"No compatible {'laboratory' if course.course_type == Course.CourseType.LAB else 'classroom'} found with capacity >= {required_capacity}."
                })
                continue

            # Add meeting instances
            for m_idx in range(meetings_to_schedule):
                meeting_tasks.append({
                    'task_id': len(meeting_tasks),
                    'assignment': asgn,
                    'meeting_index': m_idx,
                    'total_meetings': weekly_meetings,
                    'course': course,
                    'cohort': offering.cohort,
                    'professor': asgn.professor,
                    'duration_slots': duration_slots,
                    'group_ids': group_ids,
                    'candidate_rooms': candidate_rooms,
                })

        # 7. Build CP-SAT Model
        model = cp_model.CpModel()

        # Variables: x[task_id, day, start_slot, room_id] = BoolVar
        x = {}
        task_placements: Dict[int, List[Tuple[int, int, int, Any]]] = defaultdict(list)
        slack_unscheduled = {}

        # Precompute valid slot choices per task
        for t in meeting_tasks:
            tid = t['task_id']
            dur = t['duration_slots']
            prof_id = t['professor'].id
            grp_ids = t['group_ids']
            is_lab = t['course'].course_type == Course.CourseType.LAB

            allowed_starts = self.ALLOWED_LAB_STARTS if is_lab else self.THEORY_STARTS

            for day in range(1, 6):
                for start_slot in allowed_starts:
                    # Check end slot
                    end_slot = start_slot + dur - 1
                    if end_slot > 8:
                        continue

                    # Check lunch break (slots 1..4 vs 5..8)
                    if start_slot <= 4 and end_slot >= 5:
                        continue

                    # Check professor availability and fixed reservations
                    slots = list(range(start_slot, end_slot + 1))
                    prof_clash = any((day, s) in prof_unavail[prof_id] or (day, s) in fixed_prof_slots[prof_id] for s in slots)
                    if prof_clash:
                        continue

                    # Check student groups clash
                    grp_clash = any(
                        (day, s) in fixed_group_slots[gid]
                        for gid in grp_ids
                        for s in slots
                    )
                    if grp_clash:
                        continue

                    # Rooms
                    for room in t['candidate_rooms']:
                        room_id = room.id
                        room_clash = any(
                            (day, s) in room_unavail[room_id] or (day, s) in fixed_room_slots[room_id]
                            for s in slots
                        )
                        if room_clash:
                            continue

                        # Feasible placement variable
                        var = model.NewBoolVar(f"x_{tid}_d{day}_s{start_slot}_r{room_id}")
                        x[tid, day, start_slot, room_id] = var
                        task_placements[tid].append((day, start_slot, room_id, var))

            # Slack variable for infeasibility resilience
            slack_unscheduled[tid] = model.NewBoolVar(f"slack_{tid}")

            # Exactly one placement OR slack
            placed_vars = [item[3] for item in task_placements[tid]]
            if placed_vars:
                model.Add(sum(placed_vars) + slack_unscheduled[tid] == 1)
            else:
                model.Add(slack_unscheduled[tid] == 1)

        # ----------------------------------------------------
        # HARD CONSTRAINTS
        # ----------------------------------------------------

        # Constraint 1, 2, 3: Distinct days per assignment
        # (3-credit theory: 3 meetings on distinct days; 4-credit: 4 distinct days; 2-credit lab: 2 distinct days)
        tasks_by_assignment: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for t in meeting_tasks:
            tasks_by_assignment[t['assignment'].id].append(t)

        for asgn_id, asgn_tasks in tasks_by_assignment.items():
            if len(asgn_tasks) > 1:
                for day in range(1, 6):
                    day_vars = []
                    for t in asgn_tasks:
                        tid = t['task_id']
                        day_vars.extend([
                            var for (d, s, r, var) in task_placements[tid] if d == day
                        ])
                    if day_vars:
                        model.Add(sum(day_vars) <= 1)

        # Constraint 4: No Professor Overlapping
        # For each prof, each day, each slot: sum <= 1
        prof_day_slot_vars: Dict[Tuple[int, int, int], List[Any]] = defaultdict(list)
        for t in meeting_tasks:
            tid = t['task_id']
            prof_id = t['professor'].id
            dur = t['duration_slots']
            for (d, s, r, var) in task_placements[tid]:
                for occupied_slot in range(s, s + dur):
                    prof_day_slot_vars[prof_id, d, occupied_slot].append(var)

        for (prof_id, d, slot), vars_list in prof_day_slot_vars.items():
            if len(vars_list) > 1:
                model.Add(sum(vars_list) <= 1)

        # Constraint 5: No Room Overlapping
        # For each room, each day, each slot: sum <= 1
        room_day_slot_vars: Dict[Tuple[int, int, int], List[Any]] = defaultdict(list)
        for t in meeting_tasks:
            tid = t['task_id']
            dur = t['duration_slots']
            for (d, s, r, var) in task_placements[tid]:
                for occupied_slot in range(s, s + dur):
                    room_day_slot_vars[r, d, occupied_slot].append(var)

        for (room_id, d, slot), vars_list in room_day_slot_vars.items():
            if len(vars_list) > 1:
                model.Add(sum(vars_list) <= 1)

        # Constraint 6: No Instruction Group Overlapping
        # For each group (or full cohort), each day, each slot: sum <= 1
        group_day_slot_vars: Dict[Tuple[int, int, int], List[Any]] = defaultdict(list)
        for t in meeting_tasks:
            tid = t['task_id']
            dur = t['duration_slots']
            grp_ids = t['group_ids']
            cohort_pseudo_id = -t['cohort'].id  # If no lab group, use cohort pseudo-group

            target_keys = grp_ids if grp_ids else [cohort_pseudo_id]
            for (d, s, r, var) in task_placements[tid]:
                for occupied_slot in range(s, s + dur):
                    for gkey in target_keys:
                        group_day_slot_vars[gkey, d, occupied_slot].append(var)

        for (gkey, d, slot), vars_list in group_day_slot_vars.items():
            if len(vars_list) > 1:
                model.Add(sum(vars_list) <= 1)

        # ----------------------------------------------------
        # SOFT CONSTRAINTS & WEIGHTED OBJECTIVE
        # ----------------------------------------------------
        objective_terms = []

        # Objective A: Heavy penalty on unscheduled meetings (100,000 per unscheduled meeting)
        for tid, slack_var in slack_unscheduled.items():
            objective_terms.append(slack_var * 100_000)

        # Objective B: Undesirable First (slot 1) and Last (slot 8) slots penalty
        for (tid, day, start_slot, room_id), var in x.items():
            if start_slot == 1:
                objective_terms.append(var * 8)
            elif start_slot == 8:
                objective_terms.append(var * 10)
            elif start_slot in [2, 3, 5, 6]:
                # Prime mid-day preference bonus (negative penalty)
                objective_terms.append(var * -5)

        # Objective C: Spreading multi-meeting courses across the week (avoid adjacent days)
        for asgn_id, asgn_tasks in tasks_by_assignment.items():
            if len(asgn_tasks) >= 2:
                for day in range(1, 5):
                    # Check if scheduled on day and day+1
                    d1_vars = [var for t in asgn_tasks for (d, s, r, var) in task_placements[t['task_id']] if d == day]
                    d2_vars = [var for t in asgn_tasks for (d, s, r, var) in task_placements[t['task_id']] if d == day + 1]
                    if d1_vars and d2_vars:
                        adj_var = model.NewBoolVar(f"adj_{asgn_id}_d{day}")
                        # adj_var is 1 if both day and day+1 are occupied
                        model.Add(sum(d1_vars) + sum(d2_vars) <= 1 + adj_var)
                        objective_terms.append(adj_var * 25)

        # Objective D: Student Timetable Gaps & Cohort Load Balance
        # For each cohort, each day, define cohort_active[c, d, slot]
        cohort_tasks = defaultdict(list)
        for t in meeting_tasks:
            cohort_tasks[t['cohort'].id].append(t)

        for cid, ctasks in cohort_tasks.items():
            for day in range(1, 6):
                # Day slots active
                slot_active_vars = {}
                for slot in range(1, 9):
                    svars = []
                    for t in ctasks:
                        dur = t['duration_slots']
                        svars.extend([
                            var for (d, s, r, var) in task_placements[t['task_id']]
                            if d == day and s <= slot < s + dur
                        ])
                    if svars:
                        slot_active = model.NewBoolVar(f"c_{cid}_d{day}_s{slot}_active")
                        model.Add(sum(svars) == slot_active)
                        slot_active_vars[slot] = slot_active

                # Student gap penalty: active at s-1 and s+1, but inactive at s (skipping lunch boundary s=4/5)
                for slot in [2, 3, 6, 7]:
                    if (slot - 1) in slot_active_vars and (slot + 1) in slot_active_vars and slot in slot_active_vars:
                        gap_var = model.NewBoolVar(f"cgap_{cid}_d{day}_s{slot}")
                        model.Add(
                            gap_var >= slot_active_vars[slot - 1] + slot_active_vars[slot + 1] - slot_active_vars[slot] - 1
                        )
                        objective_terms.append(gap_var * 20)

        # Objective E: Professor Timetable Gaps & Max Consecutive Hours
        prof_tasks = defaultdict(list)
        for t in meeting_tasks:
            prof_tasks[t['professor'].id].append(t)

        for pid, ptasks in prof_tasks.items():
            for day in range(1, 6):
                slot_active_vars = {}
                for slot in range(1, 9):
                    svars = []
                    for t in ptasks:
                        dur = t['duration_slots']
                        svars.extend([
                            var for (d, s, r, var) in task_placements[t['task_id']]
                            if d == day and s <= slot < s + dur
                        ])
                    if svars:
                        p_active = model.NewBoolVar(f"p_{pid}_d{day}_s{slot}_active")
                        model.Add(sum(svars) == p_active)
                        slot_active_vars[slot] = p_active

                # Professor gap penalty
                for slot in [2, 3, 6, 7]:
                    if (slot - 1) in slot_active_vars and (slot + 1) in slot_active_vars and slot in slot_active_vars:
                        pgap = model.NewBoolVar(f"pgap_{pid}_d{day}_s{slot}")
                        model.Add(
                            pgap >= slot_active_vars[slot - 1] + slot_active_vars[slot + 1] - slot_active_vars[slot] - 1
                        )
                        objective_terms.append(pgap * 15)

                # Excessive consecutive hours penalty (more than 3 hours continuous)
                # Morning: 1, 2, 3, 4
                m_slots = [slot_active_vars[s] for s in [1, 2, 3, 4] if s in slot_active_vars]
                if len(m_slots) == 4:
                    fatigue_m = model.NewBoolVar(f"pfatigue_m_{pid}_d{day}")
                    model.Add(sum(m_slots) <= 3 + fatigue_m)
                    objective_terms.append(fatigue_m * 35)

                # Afternoon: 5, 6, 7, 8
                a_slots = [slot_active_vars[s] for s in [5, 6, 7, 8] if s in slot_active_vars]
                if len(a_slots) == 4:
                    fatigue_a = model.NewBoolVar(f"pfatigue_a_{pid}_d{day}")
                    model.Add(sum(a_slots) <= 3 + fatigue_a)
                    objective_terms.append(fatigue_a * 35)

        # Set model objective
        model.Minimize(sum(objective_terms))

        self._notify(40, f"Executing OR-Tools CP-SAT solver (Time limit: {self.time_limit}s)...")

        # 8. Solve Model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.time_limit)
        solver.parameters.num_search_workers = 4

        callback = SolverProgressCallback(on_progress=self._notify)
        solve_status = solver.Solve(model, callback)

        elapsed_time = round(time.time() - start_time, 2)
        self._notify(90, "Processing generated schedule and evaluating quality score...")

        # 9. Interpret Results
        solver_status_map = {
            cp_model.OPTIMAL: 'OPTIMAL',
            cp_model.FEASIBLE: 'FEASIBLE',
            cp_model.INFEASIBLE: 'INFEASIBLE',
            cp_model.UNKNOWN: 'UNKNOWN',
            cp_model.MODEL_INVALID: 'MODEL_INVALID',
        }
        resolved_status = solver_status_map.get(solve_status, 'UNKNOWN')

        if solve_status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            proposed_meetings = []
            placed_task_count = 0

            for t in meeting_tasks:
                tid = t['task_id']
                is_slack = solver.Value(slack_unscheduled[tid]) == 1

                if is_slack:
                    unscheduled_offerings.append({
                        'assignment_id': t['assignment'].id,
                        'course_code': t['course'].code,
                        'course_name': t['course'].name,
                        'cohort': str(t['cohort']),
                        'professor': t['professor'].full_name,
                        'meeting_index': t['meeting_index'] + 1,
                        'reason': 'Solver could not find a clash-free slot with compatible room/professor availability.',
                    })
                    continue

                # Find which placement variable was chosen
                for (day, start_slot, room_id, var) in task_placements[tid]:
                    if solver.Value(var) == 1:
                        placed_task_count += 1
                        room_obj = next((r for r in t['candidate_rooms'] if r.id == room_id), None)
                        proposed_meetings.append({
                            'teaching_assignment_id': t['assignment'].id,
                            'course_code': t['course'].code,
                            'course_name': t['course'].name,
                            'course_type': t['course'].course_type,
                            'cohort_id': t['cohort'].id,
                            'cohort_name': str(t['cohort']),
                            'branch_id': t['cohort'].branch_id,
                            'professor_id': t['professor'].id,
                            'professor_name': t['professor'].full_name,
                            'room_id': room_id,
                            'room_no': room_obj.room_no if room_obj else str(room_id),
                            'building_code': room_obj.building.code if room_obj else '',
                            'room_type': room_obj.room_type if room_obj else '',
                            'weekday': day,
                            'start_slot': start_slot,
                            'duration_slots': t['duration_slots'],
                            'instruction_group_ids': t['group_ids'],
                        })
                        break

            # Calculate Quality Score
            score_data = ScheduleScorer.calculate_score(
                proposed_meetings,
                unscheduled_count=len(unscheduled_offerings)
            )

            self._notify(100, f"Auto-scheduling completed successfully! ({placed_task_count} meetings placed)")

            return {
                'solver_status': resolved_status,
                'quality_score': score_data['overall_score'],
                'proposed_meetings': proposed_meetings,
                'unscheduled_offerings': unscheduled_offerings,
                'constraint_score_breakdown': score_data,
                'generation_metadata': {
                    'solve_time_seconds': elapsed_time,
                    'total_tasks': len(meeting_tasks),
                    'placed_meetings': placed_task_count,
                    'unscheduled_meetings': len(unscheduled_offerings),
                    'replace_existing': self.replace_existing,
                    'selected_branches': self.branch_ids,
                    'solver_objective': solver.ObjectiveValue() if solve_status == cp_model.OPTIMAL else None,
                }
            }

        else:
            self._notify(100, f"Solver ended with status: {resolved_status}")
            return {
                'solver_status': resolved_status,
                'quality_score': 0.0,
                'proposed_meetings': [],
                'unscheduled_offerings': unscheduled_offerings or [{'reason': f"CP-SAT solver returned {resolved_status}."}],
                'constraint_score_breakdown': {},
                'generation_metadata': {
                    'solve_time_seconds': elapsed_time,
                    'total_tasks': len(meeting_tasks),
                    'replace_existing': self.replace_existing,
                    'selected_branches': self.branch_ids,
                }
            }
