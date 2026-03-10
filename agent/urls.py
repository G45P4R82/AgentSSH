"""Agent app URL configuration"""
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('hosts/test/', views.host_test_connection_view, name='host_test_connection'),
    path('', RedirectView.as_view(url='/agent/', permanent=False), name='home'),
    path('hosts/', views.home_view, name='hosts'),
    path('hosts/new/', views.host_new_view, name='host_new'),
    path('hosts/<int:host_id>/edit/', views.host_edit_view, name='host_edit'),
    path('hosts/<int:host_id>/delete/', views.host_delete_view, name='host_delete'),
    path('agent/<uuid:session_id>/', views.agent_view, name='agent_session'),
    path('agent/', views.agent_view, name='agent'),
    path('agent/execute/', views.agent_execute_view, name='agent_execute'),
    path('agent/stream/<int:task_id>/', views.agent_task_stream_view, name='agent_stream'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
