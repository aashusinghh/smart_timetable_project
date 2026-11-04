from rest_framework import serializers
from .models import Campus, Building, Room, RoomUnavailability

class CampusSerializer(serializers.ModelSerializer):
    buildings_count = serializers.IntegerField(source='buildings.count', read_only=True)

    class Meta:
        model = Campus
        fields = ['id', 'code', 'name', 'address', 'is_active', 'buildings_count', 'created_at', 'updated_at']


class BuildingSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    campus_code = serializers.CharField(source='campus.code', read_only=True)
    rooms_count = serializers.IntegerField(source='rooms.count', read_only=True)

    class Meta:
        model = Building
        fields = [
            'id', 'campus', 'campus_name', 'campus_code',
            'code', 'name', 'floors_count', 'is_active',
            'rooms_count', 'created_at', 'updated_at'
        ]


class RoomUnavailabilitySerializer(serializers.ModelSerializer):
    room_str = serializers.CharField(source='room.__str__', read_only=True)

    class Meta:
        model = RoomUnavailability
        fields = [
            'id', 'room', 'room_str', 'weekday', 'specific_date',
            'start_slot', 'end_slot', 'reason', 'created_at', 'updated_at'
        ]


class RoomSerializer(serializers.ModelSerializer):
    building_code = serializers.CharField(source='building.code', read_only=True)
    building_name = serializers.CharField(source='building.name', read_only=True)
    campus_code = serializers.CharField(source='building.campus.code', read_only=True)
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)

    class Meta:
        model = Room
        fields = [
            'id', 'building', 'building_code', 'building_name', 'campus_code',
            'room_no', 'name', 'room_type', 'room_type_display',
            'capacity', 'floor', 'has_projector', 'is_active',
            'created_at', 'updated_at'
        ]
