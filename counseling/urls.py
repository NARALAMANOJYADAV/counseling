from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('status/', views.approval_status_view, name='approval_status'),
    path('grievance/', views.grievance_view, name='grievance_form'),
    path('grievance/status/', views.grievance_status_view, name='grievance_status'),
    path('grievance/success/', views.grievance_success_view, name='grievance_success'),
    path('', views.login_view, name='index'), # Root is now login
    path('form/', views.counseling_form_view, name='counseling_form'),
    path('profile/', views.profile_view, name='profile'),
    path('success/', views.success_view, name='success'),
    path('view-form/counseling/<int:pk>/', views.admin_view_counseling, name='admin_view_counseling'),
    path('view-form/grievance/<int:pk>/', views.admin_view_grievance, name='admin_view_grievance'),
]
