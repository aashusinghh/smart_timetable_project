from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, full_name='', **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, full_name='Super Admin', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(email, password, full_name, **extra_fields)

        # Ensure SUPER_ADMIN role assignment exists
        try:
            role, _ = Role.objects.get_or_create(
                code=Role.Code.SUPER_ADMIN,
                defaults={'name': 'Super Administrator'}
            )
            UserRoleAssignment.objects.get_or_create(user=user, role=role, branch=None)
        except Exception:
            pass

        return user


class Role(models.Model):
    class Code(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        BRANCH_COORDINATOR = 'BRANCH_COORDINATOR', 'Branch Coordinator'
        PROFESSOR = 'PROFESSOR', 'Professor'

    code = models.CharField(max_length=50, unique=True, choices=Code.choices)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        ordering = ['code']

    def __str__(self):
        return f"{self.get_code_display()} ({self.code})"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    employee_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        ordering = ['email']

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    def get_role_codes(self):
        codes = list(self.role_assignments.values_list('role__code', flat=True).distinct())
        if self.is_superuser and Role.Code.SUPER_ADMIN not in codes:
            codes.append(Role.Code.SUPER_ADMIN)
        return codes

    def has_role(self, role_code):
        if self.is_superuser and role_code == Role.Code.SUPER_ADMIN:
            return True
        return self.role_assignments.filter(role__code=role_code).exists()


class UserRoleAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_assignments')
    branch = models.ForeignKey(
        'academics.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coordinator_assignments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_role_assignments'
        unique_together = ('user', 'role', 'branch')

    def __str__(self):
        branch_str = f" @ {self.branch.code}" if self.branch else ""
        return f"{self.user.email} -> {self.role.code}{branch_str}"


class ProfessorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professor_profile')
    designation = models.CharField(max_length=100, default='Assistant Professor')
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.CASCADE,
        related_name='professors'
    )
    max_hours_per_day = models.PositiveIntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professor_profiles'

    def __str__(self):
        return f"{self.designation} {self.user.full_name} ({self.department.code})"

