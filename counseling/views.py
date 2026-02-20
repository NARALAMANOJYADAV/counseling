from django.shortcuts import render, redirect, get_object_or_404
from .forms import StudentCounselingForm, UserRegistrationForm, GrievanceForm
from .models import StudentCounseling, Grievance
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils import timezone
import json
from datetime import timedelta

@login_required
def dashboard_view(request):
    # Fetch real status data
    try:
        student = StudentCounseling.objects.get(roll_number=request.user.username)
        # Check if form was actually submitted (using last_submission_date as a proxy or just checking if it exists)
        if student.last_submission_date:
            counseling_status = student.approval_status
        else:
            counseling_status = "Not Submitted"
    except StudentCounseling.DoesNotExist:
        counseling_status = "Not Submitted"

    # Fetch latest grievance status
    latest_grievance = Grievance.objects.filter(roll_number=request.user.username).order_by('-submission_date').first()
    if latest_grievance:
        grievance_status = latest_grievance.status
    else:
        grievance_status = "No Grievances"

    context = {
        'counseling_status': counseling_status,
        'grievance_status': grievance_status,
    }
    return render(request, 'dashboard.html', context)

@login_required
def admin_dashboard_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    
    # Calculate stats
    total_students = StudentCounseling.objects.count()
    
    # Logic for pending counseling based on role
    user_upper = request.user.username.upper()
    if user_upper == 'COUNSELOR':
        counseling_qs = StudentCounseling.objects.filter(counselor_approval='Pending').exclude(approval_status='Rejected')
        grievance_qs = Grievance.objects.filter(counselor_approval='Pending').exclude(status='Rejected')
    elif user_upper == 'HOD':
        counseling_qs = StudentCounseling.objects.filter(hod_approval='Pending').exclude(approval_status='Rejected')
        grievance_qs = Grievance.objects.filter(hod_approval='Pending').exclude(status='Rejected')
    elif user_upper == 'INCHARGE':
        counseling_qs = StudentCounseling.objects.filter(incharge_approval='Pending').exclude(approval_status='Rejected')
        grievance_qs = Grievance.objects.filter(incharge_approval='Pending').exclude(status='Rejected')
    elif user_upper == 'DIRECTOR':
        counseling_qs = StudentCounseling.objects.filter(director_approval='Pending').exclude(approval_status='Rejected')
        grievance_qs = Grievance.objects.filter(director_approval='Pending').exclude(status='Rejected')
    else: # Superadmin (MANOJ)
        counseling_qs = StudentCounseling.objects.filter(approval_status='Pending')
        grievance_qs = Grievance.objects.filter(status='Pending')

    pending_counseling = counseling_qs.count()
    pending_grievances = grievance_qs.count()

    context = {
        'total_students': total_students,
        'pending_counseling': pending_counseling,
        'pending_grievances': pending_grievances,
        'recent_counseling_json': json.dumps([
            {'id': s.id, 'name': s.student_name, 'roll': s.roll_number, 'link': f"/view-form/counseling/{s.id}/"}
            for s in counseling_qs.order_by('-last_submission_date')[:5]
        ]),
        'recent_grievances_json': json.dumps([
            {'id': g.id, 'roll': g.roll_number, 'type': g.grievance_type, 'link': f"/view-form/grievance/{g.id}/"}
            for g in grievance_qs.order_by('-submission_date')[:5]
        ]),
    }
    return render(request, 'admin_dashboard.html', context)

def counseling_form_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    student = None
    try:
        student = StudentCounseling.objects.get(roll_number=request.user.username)
    except StudentCounseling.DoesNotExist:
        # Create user profile if it doesn't exist (should happen at register, but safe fallback)
        pass

    if request.method == 'POST':
        # One-Time Submission Check
        # Admins (superusers) bypass this check
        if student and student.last_submission_date and not request.user.is_superuser:
            # messages.error(request, "You have already submitted the counseling form. Each user is allowed only one submission.")
            return redirect('success')

        # Process form if check passes or user is admin
        if student:
            form = StudentCounselingForm(request.POST, instance=student)
        else:
            form = StudentCounselingForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.roll_number = request.user.username
            instance.email = request.user.email
            instance.last_submission_date = timezone.now() # Update submission time
            instance.save()
            request.session['submitted_now'] = True
            messages.success(request, "Counseling form submitted successfully.")
            return redirect('success')
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        # GET request
        # If already submitted, redirect to success/status page
        if student and student.last_submission_date and not request.user.is_superuser:
            # messages.info(request, "You have already submitted your counseling form.")
            return redirect('success')

        if student:
            form = StudentCounselingForm(instance=student)
        else:
            form = StudentCounselingForm(initial={'student_name': request.user.username})

    return render(request, 'student_counseling.html', {'form': form})

def success_view(request):
    try:
        student = StudentCounseling.objects.get(roll_number=request.user.username)
    except StudentCounseling.DoesNotExist:
        student = None
    
    submitted_now = request.session.pop('submitted_now', False)
    return render(request, 'success.html', {'student': student, 'submitted_now': submitted_now})

def csrf_failure(request, reason=""):
    messages.error(request, "Security verification failed (CSRF). Please refresh the page and try again.")
    return redirect('login')

@never_cache
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            print(f"DEBUG: Login failed for context: {form.errors}")
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    # If authenticated, we show the page but maybe add a notification
    # Actually, the user wants 'index.html' to open FIRST regardless
    return render(request, 'index.html', {'form': form})

@never_cache
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            StudentCounseling.objects.create(
                roll_number=user.username,
                email=user.email,
                student_name=user.username,
                approval_status='Pending'
            )
            messages.success(request, "Registration successful! Please login with your credentials.")
            return redirect('login') 
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('login') 
    return redirect('login')

@login_required
def approval_status_view(request):
    try:
        student = StudentCounseling.objects.get(roll_number=request.user.username)
    except StudentCounseling.DoesNotExist:
        student = None
    return render(request, 'status.html', {'student': student})

@login_required
def grievance_view(request):
    if request.method == 'POST':
        form = GrievanceForm(request.POST, request.FILES)
        if form.is_valid():
            grievance = form.save(commit=False)
            grievance.roll_number = request.user.username
            grievance.save()
            return redirect('grievance_success')
        else:
            print(f"DEBUG: Grievance Form Errors: {form.errors}") # For server logs
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = GrievanceForm()
    
    return render(request, 'grievance.html', {'form': form})

@login_required
def grievance_status_view(request):
    grievances = Grievance.objects.filter(roll_number=request.user.username).order_by('-submission_date')
    return render(request, 'grievance_status.html', {'grievances': grievances})

@login_required
def grievance_success_view(request):
    grievance = Grievance.objects.filter(roll_number=request.user.username).order_by('-submission_date').first()
    return render(request, 'grievance_success.html', {'grievance': grievance})

@login_required
def profile_view(request):
    try:
        student = StudentCounseling.objects.get(roll_number=request.user.username)
    except StudentCounseling.DoesNotExist:
        student = None
    return render(request, 'profile.html', {'student': student})

@login_required
def admin_view_counseling(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    student = get_object_or_404(StudentCounseling, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        target_role = request.POST.get('target_role')
        user_role = request.user.username.upper()
        
        # Superusers can act as any role; others can only act as themselves
        role_to_act_as = target_role if (request.user.is_superuser and target_role) else user_role
        
        updated = False
        if role_to_act_as == 'COUNSELOR':
            student.counselor_approval = action
            updated = True
        elif role_to_act_as == 'HOD':
            student.hod_approval = action
            updated = True
        elif role_to_act_as == 'INCHARGE':
            student.incharge_approval = action
            updated = True
        elif role_to_act_as == 'DIRECTOR':
            student.director_approval = action
            updated = True

        if updated:
            # Automatic Final Approval Logic
            approvals = [
                student.counselor_approval,
                student.hod_approval,
                student.incharge_approval,
                student.director_approval
            ]
            
            if 'Rejected' in approvals:
                student.approval_status = 'Rejected'
            elif all(a == 'Approved' for a in approvals):
                student.approval_status = 'Approved'
            else:
                student.approval_status = 'Pending'
                
            student.save()
            messages.success(request, f"Status updated to {action} successfully.")
        
        return redirect('admin_view_counseling', pk=pk)

    role = request.user.username.upper()
    return render(request, 'admin/view_counseling.html', {'student': student, 'role': role})

@login_required
def admin_view_grievance(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    grievance = get_object_or_404(Grievance, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        target_role = request.POST.get('target_role')
        user_role = request.user.username.upper()

        # Superusers can act as any role; others can only act as themselves
        role_to_act_as = target_role if (request.user.is_superuser and target_role) else user_role

        updated = False
        if role_to_act_as == 'COUNSELOR':
            grievance.counselor_approval = action
            updated = True
        elif role_to_act_as == 'HOD':
            grievance.hod_approval = action
            updated = True
        elif role_to_act_as == 'INCHARGE':
            grievance.incharge_approval = action
            updated = True
        elif role_to_act_as == 'DIRECTOR':
            grievance.director_approval = action
            updated = True

        if updated:
            # Automatic Final Status Logic
            approvals = [
                grievance.counselor_approval,
                grievance.hod_approval,
                grievance.incharge_approval,
                grievance.director_approval,
            ]
            if 'Rejected' in approvals:
                grievance.status = 'Rejected'
            elif all(a == 'Approved' for a in approvals):
                grievance.status = 'Resolved'
            else:
                grievance.status = 'Pending'

            grievance.save()
            messages.success(request, f"Grievance status updated to {action} successfully.")

        return redirect('admin_view_grievance', pk=pk)

    role = request.user.username.upper()
    return render(request, 'admin/view_grievance.html', {'grievance': grievance, 'role': role})

def logout_view(request):
    logout(request)
    return redirect('login')
