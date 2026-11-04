from django.contrib import admin
from .models import Campus, Building, Room, RoomUnavailability

class BuildingInline(admin.TabularInline):
    model = Building
    extra = 1


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    fields = ('room_no', 'name', 'room_type', 'capacity', 'floor', 'is_active')


class RoomUnavailabilityInline(admin.TabularInline):
    model = RoomUnavailability
    extra = 0


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)
    inlines = [BuildingInline]


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'campus', 'floors_count', 'is_active')
    search_fields = ('code', 'name', 'campus__name')
    list_filter = ('campus', 'is_active')
    inlines = [RoomInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_no', 'building', 'room_type', 'capacity', 'floor', 'has_projector', 'is_active')
    search_fields = ('room_no', 'name', 'building__code', 'building__name')
    list_filter = ('room_type', 'building__campus', 'building', 'is_active')
    inlines = [RoomUnavailabilityInline]


@admin.register(RoomUnavailability)
class RoomUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ('room', 'weekday', 'specific_date', 'start_slot', 'end_slot', 'reason')
    list_filter = ('weekday', 'room__building')
    search_fields = ('room__room_no', 'reason')
