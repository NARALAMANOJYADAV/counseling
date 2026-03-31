from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
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
    path('delete-student/<str:user_id>/', views.delete_student_view, name='delete_student'),
    path('admin-users/', views.admin_users_view, name='admin_users'),
    path('bulk-assign-counselor/', views.bulk_assign_counselor, name='bulk_assign_counselor'),
    path('bulk-add-students/', views.bulk_add_students, name='bulk_add_students'),
    path('bulk-delete-students/', views.bulk_delete_students, name='bulk_delete_students'),
    
    # Password Reset specifically defined to avoid /accounts/login redirection conflicts
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('test-email/', views.test_email_view, name='test_email'),
]

