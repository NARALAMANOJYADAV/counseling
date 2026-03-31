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
from django.http import JsonResponse

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
    
    # Logic for pending counts based on role
    user_upper = request.user.username.upper()
    if user_upper == 'COUNSELOR':
        pending_counseling = StudentCounseling.objects.filter(counselor_approval='Pending', last_submission_date__isnull=False).count()
        pending_grievances = Grievance.objects.filter(counselor_approval='Pending').count()
        
        # Recent items (all submitted, for visibility)
        recent_counseling = StudentCounseling.objects.filter(last_submission_date__isnull=False).order_by('-last_submission_date')[:10]
        recent_grievances = Grievance.objects.all().order_by('-submission_date')[:10]
    elif user_upper == 'HOD':
        pending_counseling = StudentCounseling.objects.filter(hod_approval='Pending', last_submission_date__isnull=False).count()
        pending_grievances = Grievance.objects.filter(hod_approval='Pending').count()
        recent_counseling = StudentCounseling.objects.filter(last_submission_date__isnull=False).order_by('-last_submission_date')[:10]
        recent_grievances = Grievance.objects.all().order_by('-submission_date')[:10]
    elif user_upper == 'INCHARGE':
        pending_counseling = StudentCounseling.objects.filter(incharge_approval='Pending', last_submission_date__isnull=False).count()
        pending_grievances = Grievance.objects.filter(incharge_approval='Pending').count()
        recent_counseling = StudentCounseling.objects.filter(last_submission_date__isnull=False).order_by('-last_submission_date')[:10]
        recent_grievances = Grievance.objects.all().order_by('-submission_date')[:10]
    elif user_upper == 'DIRECTOR':
        pending_counseling = StudentCounseling.objects.filter(director_approval='Pending', last_submission_date__isnull=False).count()
        pending_grievances = Grievance.objects.filter(director_approval='Pending').count()
        recent_counseling = StudentCounseling.objects.filter(last_submission_date__isnull=False).order_by('-last_submission_date')[:10]
        recent_grievances = Grievance.objects.all().order_by('-submission_date')[:10]
    else: # Superadmin
        pending_counseling = StudentCounseling.objects.filter(approval_status='Pending', last_submission_date__isnull=False).count()
        pending_grievances = Grievance.objects.filter(status='Pending').count()
        recent_counseling = StudentCounseling.objects.filter(last_submission_date__isnull=False).order_by('-last_submission_date')[:10]
        recent_grievances = Grievance.objects.all().order_by('-submission_date')[:10]

    all_students_json = '[]'
    if request.user.is_superuser:
        from django.contrib.auth.models import User
        students = User.objects.filter(is_staff=False, is_superuser=False).values('id', 'username', 'email')
        all_students_json = json.dumps(list(students))

    context = {
        'total_students': total_students,
        'pending_counseling': pending_counseling,
        'pending_grievances': pending_grievances,
        'recent_counseling_json': json.dumps([
            {'id': s.id, 'name': s.student_name, 'roll': s.roll_number, 'link': f"/view-form/counseling/{s.id}/", 'status': s.approval_status}
            for s in recent_counseling
        ]),
        'recent_grievances_json': json.dumps([
            {'id': g.id, 'roll': g.roll_number, 'type': g.grievance_type, 'link': f"/view-form/grievance/{g.id}/", 'status': g.status}
            for g in recent_grievances
        ]),
        'all_students_json': all_students_json,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def admin_users_view(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import StudentCounseling
    import json
    
    # Capture filters
    ay_filter = request.GET.get('academic_year', '')
    ys_filter = request.GET.get('year_sem', '')
    att_filter = request.GET.get('attendance_search', '').strip()
    
    # 1. Fetch all registered users (Students ONLY)
    users_qs = User.objects.filter(is_superuser=False, is_staff=False)
    
    # 2. Pre-filter StudentCounseling records based on criteria
    # Get the single most recent active record for each roll number
    all_qs = StudentCounseling.objects.all().order_by('roll_number', '-last_submission_date')
    latest_ids = []
    seen = set()
    for sc in all_qs:
        if sc.roll_number and sc.roll_number not in seen:
            seen.add(sc.roll_number)
            latest_ids.append(sc.id)
            
    sc_qs = StudentCounseling.objects.filter(id__in=latest_ids)
    
    if ay_filter:
        sc_qs = sc_qs.filter(academic_year__iexact=ay_filter.strip())
    if ys_filter:
        sc_qs = sc_qs.filter(year_sem__iexact=ys_filter.strip())
        
    if att_filter:
        try:
            # Clean up query
            search_val = att_filter.replace('%', '').strip()
            att_query = float(search_val)
            match_rolls = []
            for sc in sc_qs:
                for i in range(1, 6):
                    val = getattr(sc, f'attendance_percent{i}', None)
                    if val:
                        try:
                            # Clean up DB value
                            val_clean = str(val).replace('%', '').strip()
                            if abs(float(val_clean) - att_query) < 1.0:
                                match_rolls.append(sc.roll_number)
                                break
                        except (ValueError, TypeError): continue
            sc_qs = sc_qs.filter(roll_number__in=match_rolls)
        except ValueError:
            pass
            
    filtered_student_rolls = set(sc_qs.values_list('roll_number', flat=True))
    counselor_map = {sc.roll_number: getattr(sc, 'counselor_name', '') or '' for sc in sc_qs}
    
    users_list = users_qs.values('id', 'username', 'email', 'is_staff', 'is_superuser')
    processed_users = []
    registered_usernames = set()
    
    for u in users_list:
        role = "Student"
        is_student = True
        if u['is_superuser']:
            role = "Super Admin"
            is_student = False
        elif u['is_staff']:
            un = u['username'].upper()
            if 'COUNSELOR' in un: role = "Counselor"
            elif 'HOD' in un: role = "HOD"
            elif 'INCHARGE' in un: role = "Incharge"
            elif 'DIRECTOR' in un: role = "Director"
            else: role = "Staff member"
            is_student = False
        
        # Apply filtering: If it's a student, they must be in the filtered_student_rolls
        # If no filters are active (ay, ys, att all empty), we show all.
        if (ay_filter or ys_filter or att_filter) and is_student:
            if u['username'] not in filtered_student_rolls:
                continue
        
        u['role_label'] = role
        u['counselor_name'] = counselor_map.get(u['username'], '')
        processed_users.append(u)
        registered_usernames.add(u['username'])

    # 3. Handle manual records that match the filters
    all_manual = sc_qs.exclude(roll_number__in=registered_usernames).values('roll_number', 'student_name', 'email', 'added_by_role', 'counselor_name')
    for record in all_manual:
        identifier = record['roll_number'] or record['student_name']
        source_role = record['added_by_role'] or 'Add by Admin'
        processed_users.append({
            'id': f"manual_{identifier}", 
            'username': identifier,
            'email': record['email'],
            'role_label': f"Student({source_role})",
            'is_staff': False,
            'is_superuser': False,
            'is_manual': True,
            'counselor_name': record['counselor_name'] or ''
        })

    # Options for filters
    years = list(StudentCounseling.objects.values_list('academic_year', flat=True).distinct().order_by('academic_year'))
    sems = list(StudentCounseling.objects.values_list('year_sem', flat=True).distinct().order_by('year_sem'))

    context = {
        'all_students_json': json.dumps(processed_users),
        'is_superuser': request.user.is_superuser,
        'filter_data': json.dumps({
            'years': [y for y in years if y],
            'sems': [s for s in sems if s],
            'current': {
                'ay': ay_filter,
                'ys': ys_filter,
                'att': att_filter
            }
        })
    }
    return render(request, 'admin_users.html', context)

@login_required
def delete_student_view(request, user_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from django.contrib.auth.models import User
        from .models import StudentCounseling, Grievance
        
        user_id_str = str(user_id)
        if user_id_str.startswith('manual_'):
            # Manual record deletion (no User account)
            roll = user_id_str.replace('manual_', '')
            StudentCounseling.objects.filter(roll_number=roll).delete()
            messages.success(request, f"Manual student record {roll} removed from registry.")
        else:
            # Standard User account and associated data deletion
            try:
                user = User.objects.get(id=user_id)
                username = user.username
                # Clean up all related student data
                StudentCounseling.objects.filter(roll_number=username).delete()
                Grievance.objects.filter(roll_number=username).delete()
                user.delete()
                messages.success(request, f"User {username} and all records deleted successfully.")
            except (User.DoesNotExist, ValueError):
                messages.error(request, "User or record not found.")
                
    return redirect('admin_users')

@login_required
def bulk_assign_counselor(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_rolls = data.get('roll_numbers', [])
            counselor_name = data.get('counselor_name', '').strip()
            student_year = data.get('student_year', '').strip()
            branch = data.get('branch', '').strip()
            section = data.get('section', '').strip()
            action = data.get('action', 'assign') # 'assign' or 'remove'
            
            if action == 'assign':
                update_dict = {}
                if counselor_name: update_dict['counselor_name'] = counselor_name
                if student_year: update_dict['student_year'] = student_year
                if branch: update_dict['branch'] = branch
                if section: update_dict['section'] = section
                
                if not update_dict:
                    return JsonResponse({'success': False, 'error': 'No fields provided for update'})
                    
                updated_count = StudentCounseling.objects.filter(roll_number__in=student_rolls).update(**update_dict)
                return JsonResponse({'success': True, 'updated': updated_count})
                
            elif action == 'remove':
                updated_count = StudentCounseling.objects.filter(roll_number__in=student_rolls).update(counselor_name='')
                return JsonResponse({'success': True, 'updated': updated_count})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def bulk_delete_students(request):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Only Super Admins can bulk delete'}, status=403)
        
    if request.method == 'POST':
        try:
            from django.contrib.auth.models import User
            data = json.loads(request.body)
            student_rolls = data.get('roll_numbers', [])
            
            if not student_rolls:
                return JsonResponse({'success': False, 'error': 'No students selected'})
                
            # Delete associated User accounts
            User.objects.filter(username__in=student_rolls).delete()
            # Delete student counseling records
            sc_deleted, _ = StudentCounseling.objects.filter(roll_number__in=student_rolls).delete()
            # Delete grievances
            Grievance.objects.filter(roll_number__in=student_rolls).delete()
            
            return JsonResponse({'success': True, 'deleted': sc_deleted})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def bulk_add_students(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mode = data.get('mode', 'list')
            created_count = 0
            
            if mode == 'range':
                start = str(data.get('start', '')).strip().upper()
                end = str(data.get('end', '')).strip().upper()
                counselor = str(data.get('counselor_name', '')).strip()
                student_year = str(data.get('student_year', '')).strip()
                branch = str(data.get('branch', '')).strip()
                section = str(data.get('section', '')).strip()
                
                prefix_len = 0
                while prefix_len < len(start) and prefix_len < len(end) and start[prefix_len] == end[prefix_len]:
                    prefix_len += 1
                
                prefix = start[:prefix_len]
                s_suf = start[prefix_len:]
                e_suf = end[prefix_len:]
                
                if s_suf.isdigit() and e_suf.isdigit():
                    s_val, e_val = int(s_suf), int(e_suf)
                    if 0 <= e_val - s_val <= 1000:
                        for i in range(s_val, e_val + 1):
                            roll = prefix + str(i).zfill(len(s_suf))
                            if not StudentCounseling.objects.filter(roll_number=roll).exists():
                                StudentCounseling.objects.create(roll_number=roll, student_name=roll, email="", counselor_name=counselor, student_year=student_year, branch=branch, section=section, added_by_role=request.user.username.upper())
                                created_count += 1
                else:
                    try:
                        s_val, e_val = int(s_suf, 36), int(e_suf, 36)
                        if 0 <= e_val - s_val <= 1000:
                            import string
                            def b36(n, l):
                                a, b = string.digits + string.ascii_uppercase, ''
                                if n == 0: return '0'.zfill(l)
                                while n: n, i = divmod(n, 36); b = a[i] + b
                                return b.zfill(l)
                            for i in range(s_val, e_val + 1):
                                roll = prefix + b36(i, len(s_suf))
                                if not StudentCounseling.objects.filter(roll_number=roll).exists():
                                    StudentCounseling.objects.create(roll_number=roll, student_name=roll, email="", counselor_name=counselor, student_year=student_year, branch=branch, section=section, added_by_role=request.user.username.upper())
                                    created_count += 1
                    except ValueError:
                        pass
            else:
                students = data.get('students', [])
                student_year = str(data.get('student_year', '')).strip()
                branch = str(data.get('branch', '')).strip()
                section = str(data.get('section', '')).strip()
                
                for st in students:
                    roll = str(st.get('roll_number', '')).strip().upper()
                    name = str(st.get('student_name', '')).strip()
                    counselor = str(st.get('counselor_name', '')).strip()
                    if not name: name = roll
                    if roll and not StudentCounseling.objects.filter(roll_number=roll).exists():
                        StudentCounseling.objects.create(roll_number=roll, student_name=name, email=str(st.get('email', '')).strip(), counselor_name=counselor, student_year=student_year, branch=branch, section=section, added_by_role=request.user.username.upper())
                        created_count += 1
                        
            return JsonResponse({'success': True, 'created': created_count})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

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
            form = StudentCounselingForm(initial={
                'roll_number': request.user.username,
                'email': request.user.email,
                'student_name': '' # Leave blank for student to fill their actual name
            })

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

from django.core.mail import send_mail
from django.http import HttpResponse

from django.conf import settings

def test_email_view(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=403)
    try:
        send_mail(
            'Test Email from Student Counseling',
            'If you are reading this, your settings are working correctly!',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        return HttpResponse(f"Email sent successfully from {settings.DEFAULT_FROM_EMAIL} to {request.user.email}! Check your inbox (and spam folder).")
    except Exception as e:
        return HttpResponse(f"Failed to send email: {str(e)}", status=500)
