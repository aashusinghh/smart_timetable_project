from typing import List, Dict, Any, Optional
from django.db.models import Q
from apps.accounts.models import User, Role
from apps.academics.models import (
    TeachingAssignment,
    Course,
    Cohort,
    InstructionGroup,
)
from apps.facilities.models import Room, RoomUnavailability
from apps.faculty.models import ProfessorUnavailability
from ..models import (
    ScheduleVersion,
    ScheduledMeeting,
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
)

class TimetableValidator:
    """
    Authoritative Timetable Clash & Constraint Validation Service.
    Implements all rules from Architecture Specification §8.
    """

    @classmethod
    def validate_meeting_placement(
        cls,
        schedule_version: ScheduleVersion,
        teaching_assignment: TeachingAssignment,
        weekday: int,
        start_slot: int,
        duration_slots: int,
        room: Room,
        instruction_group_ids: Optional[List[int]] = None,
        exclude_meeting_id: Optional[int] = None,
        user: Optional[User] = None,
        check_permissions: bool = True,
    ) -> Dict[str, Any]:
        conflicts = []
        warnings = []

        offering = teaching_assignment.course_offering
        cohort = offering.cohort
        curriculum_item = offering.curriculum_item
        course = curriculum_item.course
        delivery_rule = getattr(course, 'delivery_rule', None)

        # 1. User Permission Check (Skipped during system/sweep validation)
        if check_permissions and user and not user.is_superuser and not user.has_role(Role.Code.SUPER_ADMIN):
            coord_branch_ids = user.get_coordinated_branch_ids() if hasattr(user, 'get_coordinated_branch_ids') else None
            has_branch_coord = (
                cohort.branch_id in coord_branch_ids
                if coord_branch_ids is not None
                else user.role_assignments.filter(
                    role__code=Role.Code.BRANCH_COORDINATOR,
                    branch=cohort.branch
                ).exists()
            )
            if not has_branch_coord:
                conflicts.append({
                    'type': 'PERMISSION_DENIED',
                    'slot': start_slot,
                    'message': f"You do not have coordinator permissions for branch {cohort.branch.code}."
                })

        # 2. Schedule Version Status Check (Edit-lock for user modifications)
        if check_permissions and user:
            is_admin = user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN)
            if schedule_version.status == ScheduleVersion.Status.PUBLISHED:
                conflicts.append({
                    'type': 'VERSION_LOCKED',
                    'slot': start_slot,
                    'message': "Schedule version is PUBLISHED and cannot be modified. Create a new draft for updates."
                })
            elif schedule_version.status == ScheduleVersion.Status.ARCHIVED:
                conflicts.append({
                    'type': 'VERSION_LOCKED',
                    'slot': start_slot,
                    'message': "Schedule version is ARCHIVED and cannot be modified."
                })
            elif schedule_version.status == ScheduleVersion.Status.UNDER_REVIEW:
                if not is_admin:
                    conflicts.append({
                        'type': 'VERSION_UNDER_REVIEW',
                        'slot': start_slot,
                        'message': "Schedule version is currently UNDER_REVIEW by administrators and cannot be edited by coordinators."
                    })

        # 3. Term Consistency Check
        if offering.term_id != schedule_version.term_id:
            conflicts.append({
                'type': 'TERM_MISMATCH',
                'slot': start_slot,
                'message': "Course offering academic term does not match the schedule version term."
            })

        # 4. Bounds & Slot Indices Check
        if start_slot < 1 or start_slot > 8:
            conflicts.append({
                'type': 'INVALID_SLOT',
                'slot': start_slot,
                'message': f"Start slot {start_slot} is outside the university day (1..8)."
            })
            return {'allowed': False, 'conflicts': conflicts, 'warnings': warnings}

        end_slot = start_slot + duration_slots - 1
        if end_slot > 8:
            conflicts.append({
                'type': 'OUT_OF_BOUNDS',
                'slot': end_slot,
                'message': f"Meeting extends to slot {end_slot}, past the end of the teaching day (18:00)."
            })

        target_slots = list(range(start_slot, min(end_slot + 1, 9)))

        # 5. Delivery Rule & Duration Check
        if delivery_rule and duration_slots != delivery_rule.duration_slots:
            conflicts.append({
                'type': 'DURATION_MISMATCH',
                'slot': start_slot,
                'message': f"Course requires duration of {delivery_rule.duration_slots} slot(s), but requested {duration_slots}."
            })

        # 6. Lunch Break Protection (§6 of spec: Lunch is 12:30 to 14:00 between slots 4 and 5)
        # Slots 1..4 = morning; Slots 5..8 = afternoon.
        if start_slot <= 4 and end_slot >= 5:
            conflicts.append({
                'type': 'LUNCH_CROSSING',
                'slot': 4,
                'message': "Classes cannot cross the mandatory university lunch break (12:30–14:00)."
            })

        # 7. Lab Continuity Check (§6)
        if course.course_type == Course.CourseType.LAB:
            if duration_slots != 3:
                conflicts.append({
                    'type': 'LAB_DURATION_INVALID',
                    'slot': start_slot,
                    'message': "Laboratory sessions must be scheduled as exactly 3 continuous slots."
                })
            # Allowed 3-hour lab starts per §6:
            # Morning: Slot 1 (08:30-11:30), Slot 2 (09:30-12:30)
            # Afternoon: Slot 5 (14:00-17:00), Slot 6 (15:00-18:00)
            if start_slot not in [1, 2, 5, 6]:
                conflicts.append({
                    'type': 'LAB_START_INVALID',
                    'slot': start_slot,
                    'message': f"Lab cannot start at slot {start_slot}. Allowed 3-hour lab start slots are 1, 2, 5, or 6."
                })

        # 8. Weekly Meeting Quota Check
        if delivery_rule:
            existing_meetings_query = ScheduledMeeting.objects.filter(
                schedule_version=schedule_version,
                teaching_assignment=teaching_assignment
            )
            if exclude_meeting_id:
                existing_meetings_query = existing_meetings_query.exclude(id=exclude_meeting_id)

            scheduled_count = existing_meetings_query.count()
            if scheduled_count >= delivery_rule.weekly_meetings:
                conflicts.append({
                    'type': 'QUOTA_EXCEEDED',
                    'slot': start_slot,
                    'message': f"Course already has {scheduled_count} meetings scheduled (weekly max: {delivery_rule.weekly_meetings})."
                })

        # 9. Professor Slot Collision Check (University-wide across all departments)
        prof_res_qs = ProfessorSlotReservation.objects.filter(
            schedule_version=schedule_version,
            professor=teaching_assignment.professor,
            weekday=weekday,
            slot_no__in=target_slots
        )
        if exclude_meeting_id:
            prof_res_qs = prof_res_qs.exclude(scheduled_meeting_id=exclude_meeting_id)

        for res in prof_res_qs:
            conflicts.append({
                'type': 'PROFESSOR_BUSY',
                'slot': res.slot_no,
                'message': f"Professor {teaching_assignment.professor.full_name} is already scheduled at this slot."
            })

        # Professor Unavailability (Leaves, administrative blocks)
        prof_unavail = ProfessorUnavailability.objects.filter(
            professor=teaching_assignment.professor
        ).filter(
            Q(weekday=weekday) | Q(weekday__isnull=True)
        )
        for unavail in prof_unavail:
            # Check slot overlap
            if not (end_slot < unavail.start_slot or start_slot > unavail.end_slot):
                conflicts.append({
                    'type': 'PROFESSOR_UNAVAILABLE',
                    'slot': start_slot,
                    'message': f"Professor {teaching_assignment.professor.full_name} is unavailable: {unavail.reason}"
                })

        # 10. Room Slot Collision Check
        room_res_qs = RoomSlotReservation.objects.filter(
            schedule_version=schedule_version,
            room=room,
            weekday=weekday,
            slot_no__in=target_slots
        )
        if exclude_meeting_id:
            room_res_qs = room_res_qs.exclude(scheduled_meeting_id=exclude_meeting_id)

        for res in room_res_qs:
            conflicts.append({
                'type': 'ROOM_BUSY',
                'slot': res.slot_no,
                'message': f"Room {room.room_no} ({room.building.code}) is already occupied at slot {res.slot_no}."
            })

        # Room Type Compatibility
        if course.course_type == Course.CourseType.LAB:
            allowed_lab_types = [
                Room.RoomType.COMPUTER_LAB,
                Room.RoomType.ELECTRONICS_LAB,
                Room.RoomType.CHEMISTRY_LAB,
            ]
            if room.room_type not in allowed_lab_types:
                conflicts.append({
                    'type': 'ROOM_TYPE_INCOMPATIBLE',
                    'slot': start_slot,
                    'message': f"Course '{course.name}' is a laboratory session and cannot be scheduled in a {room.get_room_type_display()}."
                })

        # Room Capacity Check
        # Resolve target student groups
        target_groups = []
        if teaching_assignment.instruction_group:
            target_groups.append(teaching_assignment.instruction_group)
            total_students = teaching_assignment.instruction_group.size
        elif instruction_group_ids:
            target_groups = list(InstructionGroup.objects.filter(id__in=instruction_group_ids))
            total_students = min(sum(g.size for g in target_groups), cohort.student_count) if cohort.student_count else sum(g.size for g in target_groups)
        else:
            # Default to all cohort lab groups for collision checking
            target_groups = list(cohort.instruction_groups.all())
            total_students = cohort.student_count

        if room.capacity < total_students:
            conflicts.append({
                'type': 'CAPACITY_INSUFFICIENT',
                'slot': start_slot,
                'message': f"Room {room.room_no} capacity ({room.capacity}) is insufficient for {total_students} students."
            })

        # Room Unavailability
        room_unavail = RoomUnavailability.objects.filter(
            room=room
        ).filter(
            Q(weekday=weekday) | Q(weekday__isnull=True)
        )
        for unavail in room_unavail:
            if not (end_slot < unavail.start_slot or start_slot > unavail.end_slot):
                conflicts.append({
                    'type': 'ROOM_UNAVAILABLE',
                    'slot': start_slot,
                    'message': f"Room {room.room_no} is blocked: {unavail.reason}"
                })

        # 11. Instruction Groups Collision Check
        for grp in target_groups:
            grp_res_qs = GroupSlotReservation.objects.filter(
                schedule_version=schedule_version,
                instruction_group=grp,
                weekday=weekday,
                slot_no__in=target_slots
            )
            if exclude_meeting_id:
                grp_res_qs = grp_res_qs.exclude(scheduled_meeting_id=exclude_meeting_id)

            for res in grp_res_qs:
                conflicts.append({
                    'type': 'GROUP_BUSY',
                    'slot': res.slot_no,
                    'message': f"Student group '{grp.code}' is already scheduled at slot {res.slot_no}."
                })

        allowed = len(conflicts) == 0
        return {
            'allowed': allowed,
            'conflicts': conflicts,
            'warnings': warnings,
        }

    @classmethod
    def get_slots_availability(
        cls,
        schedule_version: ScheduleVersion,
        teaching_assignment: TeachingAssignment,
        room: Room,
        duration_slots: Optional[int] = None,
        instruction_group_ids: Optional[List[int]] = None,
        exclude_meeting_id: Optional[int] = None,
        user: Optional[User] = None,
        check_permissions: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculates availability and conflict states for all weekly slots (5 weekdays x 8 slots)
        simultaneously for a given course offering/assignment, room, and schedule version.
        Optimized with bulk pre-fetching for instant grid-wide visibility.
        """
        offering = teaching_assignment.course_offering
        cohort = offering.cohort
        curriculum_item = offering.curriculum_item
        course = curriculum_item.course
        delivery_rule = getattr(course, 'delivery_rule', None)

        if duration_slots is None or duration_slots <= 0:
            if course.course_type == Course.CourseType.LAB:
                duration_slots = 3
            elif delivery_rule:
                duration_slots = delivery_rule.duration_slots
            else:
                duration_slots = 1

        global_conflict = None

        # 1. User Permission Check
        if check_permissions and user and not user.is_superuser and not user.has_role(Role.Code.SUPER_ADMIN):
            coord_branch_ids = user.get_coordinated_branch_ids() if hasattr(user, 'get_coordinated_branch_ids') else None
            has_branch_coord = (
                cohort.branch_id in coord_branch_ids
                if coord_branch_ids is not None
                else user.role_assignments.filter(
                    role__code=Role.Code.BRANCH_COORDINATOR,
                    branch=cohort.branch
                ).exists()
            )
            if not has_branch_coord:
                global_conflict = {
                    'type': 'PERMISSION_DENIED',
                    'message': f"You do not have coordinator permissions for branch {cohort.branch.code}."
                }

        # 2. Version status
        if not global_conflict and check_permissions and user:
            is_admin = user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN)
            if schedule_version.status == ScheduleVersion.Status.PUBLISHED:
                global_conflict = {
                    'type': 'VERSION_LOCKED',
                    'message': "Schedule version is PUBLISHED and cannot be modified."
                }
            elif schedule_version.status == ScheduleVersion.Status.ARCHIVED:
                global_conflict = {
                    'type': 'VERSION_LOCKED',
                    'message': "Schedule version is ARCHIVED and cannot be modified."
                }
            elif schedule_version.status == ScheduleVersion.Status.UNDER_REVIEW and not is_admin:
                global_conflict = {
                    'type': 'VERSION_UNDER_REVIEW',
                    'message': "Schedule version is currently UNDER_REVIEW by administrators."
                }

        # 3. Term consistency
        if not global_conflict and offering.term_id != schedule_version.term_id:
            global_conflict = {
                'type': 'TERM_MISMATCH',
                'message': "Course offering academic term does not match the schedule version term."
            }

        # 4. Quota check
        quota_exceeded = False
        scheduled_count = 0
        if delivery_rule:
            existing_meetings_query = ScheduledMeeting.objects.filter(
                schedule_version=schedule_version,
                teaching_assignment=teaching_assignment
            )
            if exclude_meeting_id:
                existing_meetings_query = existing_meetings_query.exclude(id=exclude_meeting_id)
            scheduled_count = existing_meetings_query.count()
            if scheduled_count >= delivery_rule.weekly_meetings:
                quota_exceeded = True

        # 5. Room type compatibility
        room_type_incompatible = False
        if course.course_type == Course.CourseType.LAB:
            allowed_lab_types = [
                Room.RoomType.COMPUTER_LAB,
                Room.RoomType.ELECTRONICS_LAB,
                Room.RoomType.CHEMISTRY_LAB,
            ]
            if room.room_type not in allowed_lab_types:
                room_type_incompatible = True

        # 6. Room capacity check
        target_groups = []
        if teaching_assignment.instruction_group:
            target_groups.append(teaching_assignment.instruction_group)
            total_students = teaching_assignment.instruction_group.size
        elif instruction_group_ids:
            target_groups = list(InstructionGroup.objects.filter(id__in=instruction_group_ids))
            total_students = min(sum(g.size for g in target_groups), cohort.student_count) if cohort.student_count else sum(g.size for g in target_groups)
        else:
            target_groups = list(cohort.instruction_groups.all())
            total_students = cohort.student_count

        capacity_insufficient = room.capacity < total_students

        # 7. Pre-fetch Professor Reservations & Unavailability
        prof_res_qs = ProfessorSlotReservation.objects.filter(
            schedule_version=schedule_version,
            professor=teaching_assignment.professor,
        )
        if exclude_meeting_id:
            prof_res_qs = prof_res_qs.exclude(scheduled_meeting_id=exclude_meeting_id)
        prof_res_slots = set(prof_res_qs.values_list('weekday', 'slot_no'))

        prof_unavail = list(ProfessorUnavailability.objects.filter(
            professor=teaching_assignment.professor
        ))

        # 8. Pre-fetch Room Reservations & Unavailability
        room_res_qs = RoomSlotReservation.objects.filter(
            schedule_version=schedule_version,
            room=room,
        )
        if exclude_meeting_id:
            room_res_qs = room_res_qs.exclude(scheduled_meeting_id=exclude_meeting_id)
        room_res_slots = set(room_res_qs.values_list('weekday', 'slot_no'))

        room_unavail = list(RoomUnavailability.objects.filter(room=room))

        # 9. Pre-fetch Group Reservations
        target_group_ids = [g.id for g in target_groups]
        grp_res_qs = GroupSlotReservation.objects.filter(
            schedule_version=schedule_version,
            instruction_group_id__in=target_group_ids,
        )
        if exclude_meeting_id:
            grp_res_qs = grp_res_qs.exclude(scheduled_meeting_id=exclude_meeting_id)
        grp_res_slots = set(grp_res_qs.values_list('weekday', 'slot_no'))

        # 10. Pre-fetch Cohort meetings
        cohort_meetings = ScheduledMeeting.objects.filter(
            schedule_version=schedule_version,
            teaching_assignment__course_offering__cohort=cohort,
        )
        if exclude_meeting_id:
            cohort_meetings = cohort_meetings.exclude(id=exclude_meeting_id)

        cohort_busy_slots = set()
        for m in cohort_meetings.values('weekday', 'start_slot', 'duration_slots'):
            for s in range(m['start_slot'], m['start_slot'] + m['duration_slots']):
                cohort_busy_slots.add((m['weekday'], s))

        # Evaluate all 40 slots
        slots = []
        for weekday in range(1, 6):
            for start_slot in range(1, 9):
                end_slot = start_slot + duration_slots - 1
                target_slots = list(range(start_slot, min(end_slot + 1, 9)))
                slot_conflicts = []

                if global_conflict:
                    slot_conflicts.append(global_conflict)
                elif quota_exceeded:
                    slot_conflicts.append({
                        'type': 'QUOTA_EXCEEDED',
                        'message': f"Weekly quota reached ({scheduled_count}/{delivery_rule.weekly_meetings})."
                    })
                elif room_type_incompatible:
                    slot_conflicts.append({
                        'type': 'ROOM_TYPE_INCOMPATIBLE',
                        'message': f"Course '{course.name}' requires a laboratory room."
                    })
                elif capacity_insufficient:
                    slot_conflicts.append({
                        'type': 'CAPACITY_INSUFFICIENT',
                        'message': f"Room {room.room_no} capacity ({room.capacity}) is insufficient for {total_students} students."
                    })
                elif end_slot > 8:
                    slot_conflicts.append({
                        'type': 'OUT_OF_BOUNDS',
                        'message': f"Meeting extends past timetable limit (18:00)."
                    })
                elif start_slot <= 4 and end_slot >= 5:
                    slot_conflicts.append({
                        'type': 'LUNCH_CROSSING',
                        'message': "Classes cannot cross the mandatory lunch break (12:30–14:00)."
                    })
                elif course.course_type == Course.CourseType.LAB and start_slot not in [1, 2, 5, 6]:
                    slot_conflicts.append({
                        'type': 'LAB_START_INVALID',
                        'message': "3-hour laboratory must start at slot 1, 2, 5, or 6."
                    })
                else:
                    # Check cohort collision
                    if any((weekday, s) in cohort_busy_slots for s in target_slots):
                        slot_conflicts.append({
                            'type': 'COHORT_BUSY',
                            'message': "Batch already has a class scheduled at this slot."
                        })
                    # Check professor collision
                    elif any((weekday, s) in prof_res_slots for s in target_slots):
                        slot_conflicts.append({
                            'type': 'PROFESSOR_BUSY',
                            'message': f"Professor {teaching_assignment.professor.full_name} is already busy at this slot."
                        })
                    else:
                        for unavail in prof_unavail:
                            if unavail.weekday is None or unavail.weekday == weekday:
                                if not (end_slot < unavail.start_slot or start_slot > unavail.end_slot):
                                    slot_conflicts.append({
                                        'type': 'PROFESSOR_UNAVAILABLE',
                                        'message': f"Professor {teaching_assignment.professor.full_name} unavailable: {unavail.reason}"
                                    })
                                    break

                    # Check room collision
                    if not slot_conflicts:
                        if any((weekday, s) in room_res_slots for s in target_slots):
                            slot_conflicts.append({
                                'type': 'ROOM_BUSY',
                                'message': f"Room {room.room_no} ({room.building.code}) is occupied at this slot."
                            })
                        else:
                            for unavail in room_unavail:
                                if unavail.weekday is None or unavail.weekday == weekday:
                                    if not (end_slot < unavail.start_slot or start_slot > unavail.end_slot):
                                        slot_conflicts.append({
                                            'type': 'ROOM_UNAVAILABLE',
                                            'message': f"Room {room.room_no} blocked: {unavail.reason}"
                                        })
                                        break

                    # Check group collision
                    if not slot_conflicts:
                        if any((weekday, s) in grp_res_slots for s in target_slots):
                            slot_conflicts.append({
                                'type': 'GROUP_BUSY',
                                'message': "Student group is already scheduled at this slot."
                            })

                is_allowed = len(slot_conflicts) == 0
                conflict = slot_conflicts[0] if slot_conflicts else None

                slots.append({
                    'weekday': weekday,
                    'slot_no': start_slot,
                    'allowed': is_allowed,
                    'status': 'AVAILABLE' if is_allowed else 'BUSY',
                    'conflict_type': conflict['type'] if conflict else None,
                    'message': conflict['message'] if conflict else f"Room {room.room_no} Available",
                })

        return {
            'schedule_version_id': schedule_version.id,
            'teaching_assignment_id': teaching_assignment.id,
            'room_id': room.id,
            'duration_slots': duration_slots,
            'slots': slots,
        }
