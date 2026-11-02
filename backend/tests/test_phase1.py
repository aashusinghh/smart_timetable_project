from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, Role, UserRoleAssignment, ProfessorProfile
from apps.academics.models import Department, Branch

class Phase1AuthAndAcademicsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed roles
        self.admin_role = Role.objects.create(
            code=Role.Code.SUPER_ADMIN,
            name='Super Administrator'
        )
        self.coord_role = Role.objects.create(
            code=Role.Code.BRANCH_COORDINATOR,
            name='Branch Coordinator'
        )
        self.prof_role = Role.objects.create(
            code=Role.Code.PROFESSOR,
            name='Professor'
        )

        # Create Admin
        self.admin_user = User.objects.create_user(
            email='admin@university.edu',
            password='AdminPassword123!',
            full_name='Admin User',
            is_staff=True,
            is_superuser=True
        )
        UserRoleAssignment.objects.create(user=self.admin_user, role=self.admin_role)

        # Create Department and Branch
        self.dept = Department.objects.create(code='CSE', name='Computer Science')
        self.branch = Branch.objects.create(
            department=self.dept,
            code='BTECH_CSE',
            name='B.Tech CSE',
            degree_name='B.Tech',
            max_semesters=8
        )

        # Create Professor
        self.prof_user = User.objects.create_user(
            email='prof@university.edu',
            password='ProfPassword123!',
            full_name='Dr. Professor'
        )
        UserRoleAssignment.objects.create(user=self.prof_user, role=self.prof_role)
        ProfessorProfile.objects.create(
            user=self.prof_user,
            department=self.dept,
            designation='Assistant Professor'
        )

    def test_login_valid_credentials(self):
        """Test #1: POST /api/auth/login with valid credentials -> 200 OK + token"""
        response = self.client.post('/api/auth/login', {
            'email': 'admin@university.edu',
            'password': 'AdminPassword123!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('SUPER_ADMIN', response.data['user']['roles'])

    def test_login_wrong_password(self):
        """Test #2: POST /api/auth/login with wrong password -> 401 Unauthorized"""
        response = self.client.post('/api/auth/login', {
            'email': 'admin@university.edu',
            'password': 'WrongPassword999!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_me_without_token(self):
        """Test #3: GET /api/auth/me without token -> 401/403 Forbidden"""
        response = self.client.get('/api/auth/me')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_auth_me_with_token(self):
        """Test #4: GET /api/auth/me with token -> Returns user + roles JSON"""
        login_res = self.client.post('/api/auth/login', {
            'email': 'prof@university.edu',
            'password': 'ProfPassword123!'
        }, format='json')
        token = login_res.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'prof@university.edu')
        self.assertIn('PROFESSOR', response.data['roles'])
        self.assertIsNotNone(response.data['professor_profile'])

    def test_create_department_as_super_admin(self):
        """Test #5: Create department via POST /api/departments as Super Admin -> 201 Created"""
        login_res = self.client.post('/api/auth/login', {
            'email': 'admin@university.edu',
            'password': 'AdminPassword123!'
        }, format='json')
        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post('/api/departments/', {
            'code': 'ECE',
            'name': 'Electronics and Communication Engineering'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'ECE')

    def test_create_department_as_professor_forbidden(self):
        """Test #6: Try to create department as Professor role -> 403 Forbidden"""
        login_res = self.client.post('/api/auth/login', {
            'email': 'prof@university.edu',
            'password': 'ProfPassword123!'
        }, format='json')
        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post('/api/departments/', {
            'code': 'MECH',
            'name': 'Mechanical Engineering'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_branch_tied_to_department(self):
        """Test #10: Add a branch tied to the department"""
        login_res = self.client.post('/api/auth/login', {
            'email': 'admin@university.edu',
            'password': 'AdminPassword123!'
        }, format='json')
        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post('/api/branches/', {
            'department': self.dept.id,
            'code': 'MCA',
            'name': 'Master of Computer Applications',
            'degree_name': 'MCA',
            'max_semesters': 6
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'MCA')
        self.assertEqual(response.data['max_semesters'], 6)

    def test_openapi_schema_endpoint(self):
        """Test #11: Visit OpenAPI schema & docs"""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

