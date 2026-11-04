import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)

class TimetableConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time timetable collaboration.
    Clients connect to /ws/timetable/<version_id>/ to receive instant updates
    when any coordinator places, updates, or deletes meetings, or when the
    schedule status changes (DRAFT -> UNDER_REVIEW -> PUBLISHED).
    """

    async def connect(self):
        self.version_id = self.scope['url_route']['kwargs'].get('version_id')
        if not self.version_id:
            await self.close()
            return

        self.room_group_name = f"timetable_{self.version_id}"

        # Join the timetable version room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket client connected to {self.room_group_name}")

        # Send initial connection confirmation
        await self.send_json({
            'type': 'connection.established',
            'version_id': int(self.version_id),
            'message': f'Connected to live sync for timetable version {self.version_id}',
        })

    async def disconnect(self, close_code):
        # Leave the room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket client disconnected from {self.room_group_name}")

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming messages from the frontend WebSocket client.
        """
        msg_type = content.get('type')

        if msg_type == 'ping':
            await self.send_json({'type': 'pong', 'timestamp': content.get('timestamp')})
        elif msg_type == 'client.sync_request':
            await self.send_json({
                'type': 'sync.acknowledged',
                'version_id': int(self.version_id),
            })
        else:
            logger.debug(f"Unhandled WebSocket message type: {msg_type}")

    # Channel Layer Event Handlers
    async def timetable_broadcast(self, event):
        """
        Called when a background task or view broadcasts an event to the group.
        """
        await self.send_json({
            'type': event.get('event_type', 'schedule.updated'),
            'payload': event.get('payload', {}),
            'revision': event.get('revision'),
            'status': event.get('status'),
        })

    async def schedule_published(self, event):
        """
        Called when a schedule version is published by the Super Admin.
        """
        await self.send_json({
            'type': 'schedule.published',
            'payload': event.get('payload', {}),
            'revision': event.get('revision'),
            'status': 'PUBLISHED',
        })

    async def schedule_status_changed(self, event):
        """
        Called when status transitions (e.g. DRAFT -> UNDER_REVIEW).
        """
        await self.send_json({
            'type': 'schedule.status_changed',
            'status': event.get('status'),
            'revision': event.get('revision'),
            'payload': event.get('payload', {}),
        })


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for general university notifications and publication broadcasts.
    """

    async def connect(self):
        self.group_name = "university_notifications"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        user = self.scope.get('user')
        if user and user.is_authenticated:
            self.user_group = f"user_notifications_{user.id}"
            await self.channel_layer.group_add(
                self.user_group,
                self.channel_name
            )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

    async def system_notification(self, event):
        await self.send_json({
            'type': 'notification',
            'title': event.get('title', 'Notification'),
            'message': event.get('message', ''),
            'level': event.get('level', 'info'),
            'data': event.get('data', {}),
        })
