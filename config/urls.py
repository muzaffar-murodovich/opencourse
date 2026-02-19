from django.contrib import admin
from django.urls import path, include
from learning.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('malaka/', include('learning.urls')),
    path('', HomeView.as_view(), name='home'),
]
