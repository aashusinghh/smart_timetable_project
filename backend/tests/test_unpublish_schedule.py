import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, Role
from apps.academics.models import AcademicYear, AcademicTerm, Department, Branch, Cohort, Course, CurriculumItem, CourseOffering, TeachingAssignment
from apps.timetable.models import ScheduleVersion, ScheduledMeeting
from apps.facilities.models import Campus, Building, Room

@pytest.fixture
def unpublish_env(db):
    dept = Department.objects.create(code='CSE', name='Computer Science')
    branch = Branch.objects.create(code='BTECH_CSE', name='B.Tech CSE', department=dept, max_semesters=8)
    year = AcademicYear.objects.create(name='2026-27', start_date='2026-08-01', end_date='2027-05-31', is_current=True)
    term = AcademicTerm.objects.create(academic_year=year, name='Autumn 2026', term_type=AcademicTerm.TermType.ODD, start_date='2026-08-01', end_date='2026-12-31', is_active=True)
    cohort = Cohort.objects.create(branch=branch, term=term, semester_no=1, section_code='A', student_count=60)

    admin_role = Role.objects.get_or_create(code=Role.Code.SUPER_ADMIN, defaults={'name': 'Super Admin'})[0]
    admin = User.objects.create_user(email='admin_unpub@nitjsr.ac.in', password='Password@123', is_superuser=True, full_name='Admin User')

    coord_role = Role.objects.get_or_create(code=Role.Code.BRANCH_COORDINATOR, defaults={'name': 'Coordinator'})[0]
    coord = User.objects.create_user(email='coord_unpub@nitjsr.ac.in', password='Password@123', full_name='Coord User')
    from apps.accounts.models import UserRoleAssignment
    UserRoleAssignment.objects.create(user=coord, role=coord_role, branch=branch)

    prof = User.objects.create_user(email='prof_unpub@nitjsr.ac.in', password='Password@123', full_name='Dr. Test Professor')

    course = Course.objects.create(
        code='CS101',
        name='Programming in C',
        department=dept,
        branch=branch,
        semester=1,
        credit=4,
        professor=prof
    )

    ci = CurriculumItem.objects.create(
        branch=branch,
        semester_no=1,
        course=course
    )

    offering = CourseOffering.objects.create(
        term=term,
        cohort=cohort,
        curriculum_item=ci
    )

    version = ScheduleVersion.objects.create(
        term=term,
        name='Schedule Autumn 2026',
        status=ScheduleVersion.Status.PUBLISHED,
        created_by=admin
    )

    return {
        'admin': admin,
        'coord': coord,
        'prof': prof,
        'cohort': cohort,
        'course': course,
        'offering': offering,
        'version': version,
        'term': term,
    }


@pytest.mark.django_db
class TestUnpublishScheduleAndCourseProfessorSync:

    def test_unpublish_schedule_as_admin_success(self, unpublish_env):
        client = APIClient()
        client.force_authenticate(user=unpublish_env['admin'])

        version = unpublish_env['version']
        assert version.status == ScheduleVersion.Status.PUBLISHED

        response = client.post(f'/api/timetable/versions/{version.id}/unpublish/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'DRAFT'

        version.refresh_from_db()
        assert version.status == ScheduleVersion.Status.DRAFT

    def test_unpublish_schedule_as_coordinator_forbidden(self, unpublish_env):
        client = APIClient()
        client.force_authenticate(user=unpublish_env['coord'])

        version = unpublish_env['version']
        response = client.post(f'/api/timetable/versions/{version.id}/unpublish/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unpublish_draft_schedule_rejected(self, unpublish_env):
        client = APIClient()
        client.force_authenticate(user=unpublish_env['admin'])

        version = unpublish_env['version']
        version.status = ScheduleVersion.Status.DRAFT
        version.save()

        response = client.post(f'/api/timetable/versions/{version.id}/unpublish/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_course_offering_serializer_includes_professor(self, unpublish_env):
        client = APIClient()
        client.force_authenticate(user=unpublish_env['admin'])

        cohort = unpublish_env['cohort']
        response = client.get(f'/api/course-offerings/?cohort={cohort.id}')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        assert len(results) == 1

        offering_data = results[0]
        assert offering_data['course_code'] == 'CS101'
        assert offering_data['professor_name'] == 'Dr. Test Professor'
        assert offering_data['professor_id'] == unpublish_env['prof'].id

    def test_self_healing_teaching_assignment_on_cohort_query(self, unpublish_env):
        client = APIClient()
        client.force_authenticate(user=unpublish_env['admin'])

        cohort = unpublish_env['cohort']
        # Teaching assignment was auto-created or should be auto-created on query
        response = client.get(f'/api/teaching-assignments/?cohort={cohort.id}')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        assert len(results) >= 1
        assert results[0]['professor_name'] == 'Dr. Test Professor'
