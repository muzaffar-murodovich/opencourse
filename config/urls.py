from django.contrib import admin
from django.urls import path, include
from learning.views import HomeView
from users.views import TelegramConfirmView, CheckTokenView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('malaka/', include('learning.urls')),
    path('api/auth/confirm/', TelegramConfirmView.as_view()),
    path('api/auth/check/<str:token>/', CheckTokenView.as_view()),
    path('', HomeView.as_view(), name='home'),
]
