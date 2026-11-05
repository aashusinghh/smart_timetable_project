import logging
import traceback
from typing import List, Optional
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from apps.timetable.models import ScheduleVersion
from apps.accounts.models import User, Role
from .models import AutoScheduleProposal
from .services.generator import TimetableGenerator

logger = logging.getLogger(__name__)


def update_task_progress(task_id: str, percentage: int, message: str, **extra):
    """
    Stores task progress into cache (Redis or LocMem) for fast real-time polling.
    """
    data = {
        'task_id': task_id,
        'status': 'PROGRESS',
        'percentage': percentage,
        'message': message,
        'updated_at': timezone.now().isoformat(),
        **extra
    }
    cache.set(f"task_progress_{task_id}", data, timeout=3600)


@shared_task(bind=True, queue='scheduler', name='apps.scheduler.tasks.generate_timetable')
def generate_timetable(
    self,
    version_id: int,
    branch_ids: Optional[List[int]] = None,
    time_limit: int = 60,
    replace_existing: bool = False,
    user_id: Optional[int] = None
):
    """
    Asynchronous Celery task for generating auto-schedule proposals using OR-Tools CP-SAT.
    """
    task_id = self.request.id or 'sync-task'
    update_task_progress(task_id, 5, "Initializing auto-scheduler task...")

    try:
        # 1. Validate Schedule Version
        try:
            schedule_version = ScheduleVersion.objects.get(id=version_id)
        except ScheduleVersion.DoesNotExist:
            err_msg = f"Schedule version #{version_id} not found."
            update_task_progress(task_id, 100, err_msg, status='FAILURE', error=err_msg)
            return {'status': 'FAILURE', 'error': err_msg}

        if schedule_version.status == ScheduleVersion.Status.PUBLISHED:
            err_msg = "Cannot auto-schedule for a PUBLISHED schedule version."
            update_task_progress(task_id, 100, err_msg, status='FAILURE', error=err_msg)
            return {'status': 'FAILURE', 'error': err_msg}

        if schedule_version.status == ScheduleVersion.Status.ARCHIVED:
            err_msg = "Cannot auto-schedule for an ARCHIVED schedule version."
            update_task_progress(task_id, 100, err_msg, status='FAILURE', error=err_msg)
            return {'status': 'FAILURE', 'error': err_msg}

        # 2. Validate User Permissions
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                # If coordinator, ensure they have access to requested branches
                is_admin = user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN)
                if not is_admin:
                    user_branch_ids = set(
                        user.role_assignments.filter(
                            role__code=Role.Code.BRANCH_COORDINATOR
                        ).values_list('branch_id', flat=True)
                    )
                    if branch_ids:
                        unauthorized = set(branch_ids) - user_branch_ids
                        if unauthorized:
                            err_msg = f"You do not have coordinator permissions for branches: {list(unauthorized)}."
                            update_task_progress(task_id, 100, err_msg, status='FAILURE', error=err_msg)
                            return {'status': 'FAILURE', 'error': err_msg}
            except User.DoesNotExist:
                pass

        # Progress callback wrapper
        def on_generator_progress(pct: int, msg: str):
            update_task_progress(task_id, pct, msg)
            try:
                self.update_state(state='PROGRESS', meta={'percentage': pct, 'message': msg})
            except Exception:
                pass

        # 3. Instantiate & Run Generator
        generator = TimetableGenerator(
            schedule_version=schedule_version,
            branch_ids=branch_ids,
            time_limit=time_limit,
            replace_existing=replace_existing,
            progress_callback=on_generator_progress,
        )

        result_payload = generator.generate()

        # 4. Persist Proposal in Database
        proposal = AutoScheduleProposal.objects.create(
            schedule_version=schedule_version,
            selected_branches=branch_ids or [],
            proposed_meetings=result_payload['proposed_meetings'],
            solver_status=result_payload['solver_status'],
            quality_score=result_payload['quality_score'],
            unscheduled_offerings=result_payload['unscheduled_offerings'],
            constraint_score_breakdown=result_payload['constraint_score_breakdown'],
            generation_metadata=result_payload['generation_metadata'],
            status=AutoScheduleProposal.ProposalStatus.PENDING,
            created_by=user,
        )

        final_data = {
            'task_id': task_id,
            'status': 'SUCCESS',
            'percentage': 100,
            'message': f"Proposal #{proposal.id} generated with quality score {proposal.quality_score:.1f}",
            'proposal_id': proposal.id,
            'quality_score': proposal.quality_score,
            'solver_status': proposal.solver_status,
            'placed_count': len(proposal.proposed_meetings),
            'unscheduled_count': len(proposal.unscheduled_offerings),
            'updated_at': timezone.now().isoformat(),
        }
        cache.set(f"task_progress_{task_id}", final_data, timeout=3600)

        return final_data

    except Exception as exc:
        logger.error(f"Error during auto-scheduling task {task_id}: {exc}\n{traceback.format_exc()}")
        err_msg = f"Scheduler execution error: {str(exc)}"
        final_data = {
            'task_id': task_id,
            'status': 'FAILURE',
            'percentage': 100,
            'message': err_msg,
            'error': err_msg,
            'updated_at': timezone.now().isoformat(),
        }
        cache.set(f"task_progress_{task_id}", final_data, timeout=3600)
        return final_data


@shared_task(queue='default', name='apps.scheduler.tasks.cleanup_stale_proposals')
def cleanup_stale_proposals():
    """
    Maintenance task to prune discarded or failed proposals older than 30 days.
    """
    cutoff = timezone.now() - timezone.timedelta(days=30)
    deleted_count, _ = AutoScheduleProposal.objects.filter(
        status__in=[AutoScheduleProposal.ProposalStatus.DISCARDED, AutoScheduleProposal.ProposalStatus.FAILED],
        created_at__lt=cutoff
    ).delete()
    return f"Cleaned up {deleted_count} stale proposals."
