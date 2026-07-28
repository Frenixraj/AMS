from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = "authentication"

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", views.me, name="me"),
    path("users/", views.UserListCreateView.as_view(), name="users_list"),
    path("users/<int:pk>/deactivate/", views.deactivate_user, name="user_deactivate"),
    path("users/<int:pk>/activate/", views.activate_user, name="user_activate"),
]
