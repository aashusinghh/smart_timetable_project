from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, LogoutView, CurrentUserView, RoleViewSet, UserViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='auth_login'),
    path('auth/logout', LogoutView.as_view(), name='auth_logout'),
    path('auth/me', CurrentUserView.as_view(), name='auth_me'),
    path('', include(router.urls)),
]

