from django.db import models

class Department(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        ordering = ['code']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Branch(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='branches'
    )
    code = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=150)
    degree_name = models.CharField(max_length=100, default='B.Tech')
    max_semesters = models.PositiveIntegerField(default=8)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branches'
        unique_together = ('department', 'code')
        ordering = ['department', 'code']

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.degree_name}"

