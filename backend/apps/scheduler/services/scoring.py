import math
from typing import List, Dict, Any, Optional
from collections import defaultdict
from apps.timetable.models import ScheduleVersion, ScheduledMeeting

class ScheduleScorer:
    """
    Evaluates timetable quality against soft constraints and generates a score report.
    Returns normalized sub-scores (0-100) and an overall weighted quality score.
    """

    @classmethod
    def evaluate_schedule_version(cls, schedule_version: ScheduleVersion) -> Dict[str, Any]:
        """
        Evaluates the currently saved meetings in a ScheduleVersion.
        """
        meetings_qs = ScheduledMeeting.objects.filter(
            schedule_version=schedule_version
        ).select_related(
            'teaching_assignment__course_offering__cohort',
            'teaching_assignment__course_offering__curriculum_item__course',
            'teaching_assignment__professor',
            'room'
        ).prefetch_related('meeting_instruction_groups__instruction_group')

        meeting_dicts = []
        for m in meetings_qs:
            asgn = m.teaching_assignment
            offering = asgn.course_offering
            cohort = offering.cohort
            course = offering.curriculum_item.course
            meeting_dicts.append({
                'id': m.id,
                'assignment_id': asgn.id,
                'course_code': course.code,
                'course_type': course.course_type,
                'credit': course.credit,
                'cohort_id': cohort.id,
                'professor_id': asgn.professor_id,
                'room_id': m.room_id,
                'weekday': m.weekday,
                'start_slot': m.start_slot,
                'duration_slots': m.duration_slots,
            })

        return cls.calculate_score(meeting_dicts)

    @classmethod
    def calculate_score(
        cls,
        meetings: List[Dict[str, Any]],
        unscheduled_count: int = 0
    ) -> Dict[str, Any]:
        """
        Computes detailed score breakdown and overall score for a list of meeting dicts.
        """
        if not meetings and unscheduled_count == 0:
            return {
                'overall_score': 100.0,
                'breakdown': {
                    'student_gaps_score': 100.0,
                    'professor_gaps_score': 100.0,
                    'load_balance_score': 100.0,
                    'consecutive_hours_score': 100.0,
                    'slot_preference_score': 100.0,
                    'day_spread_score': 100.0,
                },
                'metrics': {
                    'student_gap_hours': 0,
                    'professor_gap_hours': 0,
                    'max_consecutive_hours': 0,
                    'total_scheduled_meetings': 0,
                    'total_unscheduled_meetings': 0,
                }
            }

        # 1. Student Gaps & Load per Cohort per Day
        cohort_day_slots = defaultdict(lambda: defaultdict(set))
        cohort_day_hours = defaultdict(lambda: defaultdict(int))
        prof_day_slots = defaultdict(lambda: defaultdict(set))
        assignment_days = defaultdict(list)
        prime_slot_count = 0
        total_meetings = len(meetings)

        for m in meetings:
            cohort_id = m.get('cohort_id')
            prof_id = m.get('professor_id')
            weekday = m.get('weekday')
            start = m.get('start_slot')
            duration = m.get('duration_slots', 1)
            slots = list(range(start, start + duration))

            if cohort_id:
                for s in slots:
                    cohort_day_slots[cohort_id][weekday].add(s)
                cohort_day_hours[cohort_id][weekday] += duration

            if prof_id:
                for s in slots:
                    prof_day_slots[prof_id][weekday].add(s)

            if m.get('assignment_id'):
                assignment_days[m['assignment_id']].append(weekday)

            # Prime slot bonus: slots 2 to 7 (avoiding early slot 1 and late slot 8)
            if start in [2, 3, 4, 5, 6]:
                prime_slot_count += 1

        # Calculate student gap hours
        student_gap_hours = 0
        for cohort_id, days in cohort_day_slots.items():
            for day, slots in days.items():
                if len(slots) > 1:
                    min_s = min(slots)
                    max_s = max(slots)
                    # Gaps are unoccupied slots between first and last slot, excluding lunch gap (between 4 and 5)
                    for s in range(min_s, max_s + 1):
                        if s not in slots:
                            student_gap_hours += 1

        student_gaps_score = max(0.0, 100.0 - (student_gap_hours * 3.0))

        # Calculate professor gap hours & consecutive hours
        prof_gap_hours = 0
        max_consecutive_hours = 0
        consecutive_penalty = 0

        for prof_id, days in prof_day_slots.items():
            for day, slots in days.items():
                if len(slots) > 1:
                    min_s = min(slots)
                    max_s = max(slots)
                    for s in range(min_s, max_s + 1):
                        if s not in slots:
                            prof_gap_hours += 1

                # Check consecutive hours
                sorted_slots = sorted(list(slots))
                current_streak = 0
                prev_slot = None
                for s in sorted_slots:
                    if prev_slot is not None and s == prev_slot + 1:
                        current_streak += 1
                    else:
                        current_streak = 1
                    prev_slot = s
                    if current_streak > max_consecutive_hours:
                        max_consecutive_hours = current_streak
                    if current_streak > 3:
                        consecutive_penalty += (current_streak - 3)

        prof_gaps_score = max(0.0, 100.0 - (prof_gap_hours * 2.5))
        consecutive_hours_score = max(0.0, 100.0 - (consecutive_penalty * 8.0))

        # Cohort load balance across weekdays
        std_devs = []
        for cohort_id, day_hours in cohort_day_hours.items():
            hours_list = [day_hours[d] for d in range(1, 6)]
            mean_h = sum(hours_list) / 5.0
            variance = sum((h - mean_h) ** 2 for h in hours_list) / 5.0
            std_devs.append(math.sqrt(variance))

        avg_std_dev = (sum(std_devs) / len(std_devs)) if std_devs else 0.0
        load_balance_score = max(0.0, 100.0 - (avg_std_dev * 18.0))

        # Slot preference score
        slot_preference_score = (prime_slot_count / max(1, total_meetings)) * 100.0

        # Day spread score for multi-meeting courses
        spread_penalties = 0
        spread_evaluated = 0
        for asgn_id, days in assignment_days.items():
            if len(days) >= 2:
                spread_evaluated += 1
                sorted_days = sorted(days)
                # Check consecutive days
                for i in range(len(sorted_days) - 1):
                    if sorted_days[i + 1] - sorted_days[i] == 1:
                        # Adjacent days (e.g. Mon then Tue)
                        spread_penalties += 1

        day_spread_score = 100.0
        if spread_evaluated > 0:
            day_spread_score = max(0.0, 100.0 - ((spread_penalties / spread_evaluated) * 40.0))

        # Weighted composite score
        composite = (
            (student_gaps_score * 0.25) +
            (prof_gaps_score * 0.20) +
            (load_balance_score * 0.20) +
            (consecutive_hours_score * 0.15) +
            (slot_preference_score * 0.10) +
            (day_spread_score * 0.10)
        )

        # Unscheduled penalty
        if unscheduled_count > 0:
            composite = max(0.0, composite - (unscheduled_count * 20.0))

        overall_score = round(min(100.0, max(0.0, composite)), 1)

        return {
            'overall_score': overall_score,
            'breakdown': {
                'student_gaps_score': round(student_gaps_score, 1),
                'professor_gaps_score': round(prof_gaps_score, 1),
                'load_balance_score': round(load_balance_score, 1),
                'consecutive_hours_score': round(consecutive_hours_score, 1),
                'slot_preference_score': round(slot_preference_score, 1),
                'day_spread_score': round(day_spread_score, 1),
            },
            'metrics': {
                'student_gap_hours': student_gap_hours,
                'professor_gap_hours': prof_gap_hours,
                'max_consecutive_hours': max_consecutive_hours,
                'total_scheduled_meetings': total_meetings,
                'total_unscheduled_meetings': unscheduled_count,
            }
        }

