from django.db import models

class Campus(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    address = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campuses'
        ordering = ['code']
        verbose_name_plural = 'Campuses'

    def __str__(self):
        return f"{self.name} ({self.code})"


class Building(models.Model):
    campus = models.ForeignKey(
        Campus,
        on_delete=models.CASCADE,
        related_name='buildings'
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, db_index=True)
    floors_count = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'buildings'
        unique_together = ('campus', 'code')
        ordering = ['campus', 'code']

    def __str__(self):
        return f"{self.name} [{self.code}] - {self.campus.name}"


class Room(models.Model):
    class RoomType(models.TextChoices):
        CLASSROOM = 'CLASSROOM', 'Standard Classroom'
        COMPUTER_LAB = 'COMPUTER_LAB', 'Computer Lab'
        ELECTRONICS_LAB = 'ELECTRONICS_LAB', 'Electronics Lab'
        CHEMISTRY_LAB = 'CHEMISTRY_LAB', 'Chemistry Lab'
        SEMINAR_HALL = 'SEMINAR_HALL', 'Seminar Hall'

    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='rooms'
    )
    room_no = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=150, blank=True, default='')
    room_type = models.CharField(
        max_length=50,
        choices=RoomType.choices,
        default=RoomType.CLASSROOM,
        db_index=True
    )
    capacity = models.PositiveIntegerField(default=60)
    floor = models.PositiveIntegerField(default=1)
    has_projector = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        unique_together = ('building', 'room_no')
        ordering = ['building', 'room_no']

    def __str__(self):
        return f"{self.building.code}-{self.room_no} ({self.get_room_type_display()}, Cap: {self.capacity})"


class RoomUnavailability(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='unavailabilities'
    )
    weekday = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="1=Monday, 2=Tuesday, ..., 5=Friday (or recurring weekday)"
    )
    specific_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional specific calendar date"
    )
    start_slot = models.PositiveSmallIntegerField(default=1, help_text="Starting time slot (1..8)")
    end_slot = models.PositiveSmallIntegerField(default=8, help_text="Ending time slot (1..8)")
    reason = models.CharField(max_length=255, default='Maintenance / Reserved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'room_unavailability'
        ordering = ['room', 'specific_date', 'weekday', 'start_slot']

    def __str__(self):
        target = f"{self.specific_date}" if self.specific_date else f"Weekday {self.weekday}"
        return f"{self.room} unavailable on {target} (Slots {self.start_slot}-{self.end_slot}): {self.reason}"
