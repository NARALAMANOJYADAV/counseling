"""
URL configuration for student project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def admin_user_redirect(request):
    """Redirect non-superusers away from Django admin user list to our custom page."""
    if not request.user.is_superuser:
        return redirect('/admin-users/')
    return redirect('/admin/auth/user/')

urlpatterns = [
    path('admin/auth/user/', admin_user_redirect),
    path('admin/', admin.site.urls),
    path('', include('counseling.urls')),
]
