from django.shortcuts import render, redirect, get_object_or_404
from .forms import StudentCounselingForm, UserRegistrationForm, GrievanceForm
from .models import StudentCounseling, Grievance
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
import json
import csv
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
def inline_approve(request):
    """AJAX endpoint — approve or reject a counseling/grievance record inline from the approvals list."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    try:
        data       = json.loads(request.body)
        record_type = data.get('type')       # 'counseling' or 'grievance'
        record_id   = int(data.get('id'))
        action      = data.get('action')     # 'Approved' or 'Rejected'
        target_role = data.get('target_role', '').upper()

        if action not in ('Approved', 'Rejected'):
            return JsonResponse({'success': False, 'error': 'Invalid action'})

        user_role = request.user.username.upper()
        # Superusers can act as any role; others act as themselves
        role_to_act = target_role if (request.user.is_superuser and target_role) else user_role

        if record_type == 'counseling':
            obj = get_object_or_404(StudentCounseling, pk=record_id)
            if role_to_act == 'COUNSELOR':
                obj.counselor_approval = action
            elif role_to_act == 'HOD':
                obj.hod_approval = action
            elif role_to_act == 'INCHARGE':
                obj.incharge_approval = action
            elif role_to_act == 'DIRECTOR':
                obj.director_approval = action
            elif request.user.is_superuser:
                # Superuser with no specific role — approve/reject all stages at once
                obj.counselor_approval = action
                obj.hod_approval = action
                obj.incharge_approval = action
                obj.director_approval = action
            else:
                return JsonResponse({'success': False, 'error': f'Unknown role: {role_to_act}'})

            approvals = [obj.counselor_approval, obj.hod_approval,
                         obj.incharge_approval, obj.director_approval]
            if 'Rejected' in approvals:
                obj.approval_status = 'Rejected'
            elif all(a == 'Approved' for a in approvals):
                obj.approval_status = 'Approved'
            else:
                obj.approval_status = 'Pending'
            obj.save()

            return JsonResponse({
                'success': True,
                'approval_status':    obj.approval_status,
                'counselor_approval': obj.counselor_approval,
                'hod_approval':       obj.hod_approval,
                'incharge_approval':  obj.incharge_approval,
                'director_approval':  obj.director_approval,
            })

        elif record_type == 'grievance':
            obj = get_object_or_404(Grievance, pk=record_id)
            if role_to_act == 'COUNSELOR':
                obj.counselor_approval = action
            elif role_to_act == 'HOD':
                obj.hod_approval = action
            elif role_to_act == 'INCHARGE':
                obj.incharge_approval = action
            elif role_to_act == 'DIRECTOR':
                obj.director_approval = action
            elif request.user.is_superuser:
                obj.counselor_approval = action
                obj.hod_approval = action
                obj.incharge_approval = action
                obj.director_approval = action
            else:
                return JsonResponse({'success': False, 'error': f'Unknown role: {role_to_act}'})

            approvals = [obj.counselor_approval, obj.hod_approval,
                         obj.incharge_approval, obj.director_approval]
            if 'Rejected' in approvals:
                obj.status = 'Rejected'
            elif all(a == 'Approved' for a in approvals):
                obj.status = 'Resolved'
            else:
                obj.status = 'Pending'
            obj.save()

            return JsonResponse({
                'success': True,
                'status':             obj.status,
                'counselor_approval': obj.counselor_approval,
                'hod_approval':       obj.hod_approval,
                'incharge_approval':  obj.incharge_approval,
                'director_approval':  obj.director_approval,
            })

        return JsonResponse({'success': False, 'error': 'Unknown type'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def admin_approvals_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    user_upper = request.user.username.upper()

    # Determine if this user is a named counselor (not a role-based account)
    # Role accounts: COUNSELOR, HOD, INCHARGE, DIRECTOR
    # Named counselors: NATRAJ, natraj@007, etc. — is_staff but not a role keyword
    ROLE_KEYWORDS = {'COUNSELOR', 'HOD', 'INCHARGE', 'DIRECTOR'}
    is_named_counselor = (
        request.user.is_staff and
        not request.user.is_superuser and
        not any(kw in user_upper for kw in ROLE_KEYWORDS)
    )

    # Base queryset
    counseling_qs = StudentCounseling.objects.filter(
        roll_number__isnull=False
    ).exclude(roll_number='')

    grievance_qs = Grievance.objects.all()

    # Named counselors only see their own students
    if is_named_counselor:
        # Match counselor_name case-insensitively against the username
        counseling_qs = counseling_qs.filter(
            counselor_name__iexact=request.user.username
        )
        # For grievances, filter by rolls that belong to this counselor
        counselor_rolls = list(counseling_qs.values_list('roll_number', flat=True))
        grievance_qs = grievance_qs.filter(roll_number__in=counselor_rolls)

    counseling_qs = counseling_qs.order_by('-last_submission_date', 'roll_number')
    grievance_qs  = grievance_qs.order_by('-submission_date')

    # Build filter options for select-by-range modal (superadmin only)
    branches   = sorted(set(v for v in StudentCounseling.objects.values_list('branch', flat=True) if v and v.strip()))
    sections   = sorted(set(v for v in StudentCounseling.objects.values_list('section', flat=True) if v and v.strip()))
    year_sems  = sorted(set(v for v in StudentCounseling.objects.values_list('year_sem', flat=True) if v and v.strip()))
    acad_years = sorted(set(v for v in StudentCounseling.objects.values_list('academic_year', flat=True) if v and v.strip()))

    # Build counselor lookup: branch+section+year_sem → counselor_name
    counselor_map = {}
    for sc in StudentCounseling.objects.exclude(counselor_name='').exclude(counselor_name__isnull=True):
        key = f"{sc.branch or ''}|{sc.section or ''}|{sc.year_sem or ''}"
        if key not in counselor_map and sc.counselor_name:
            counselor_map[key] = sc.counselor_name

    counseling_json = json.dumps([
        {
            'id': s.id,
            'roll_number': s.roll_number or '',
            'student_name': s.student_name or '',
            'counselor_name': s.counselor_name or '',
            'year_sem': s.year_sem or '',
            'branch': s.branch or '',
            'section': s.section or '',
            'approval_status': s.approval_status,
            'counselor_approval': s.counselor_approval,
            'hod_approval': s.hod_approval,
            'incharge_approval': s.incharge_approval,
            'director_approval': s.director_approval,
            'last_submission_date': s.last_submission_date.isoformat() if s.last_submission_date else None,
            'submitted': bool(s.last_submission_date),
        }
        for s in counseling_qs
    ])

    grievance_json = json.dumps([
        {
            'id': g.id,
            'roll_number': g.roll_number or '',
            'grievance_type': g.get_grievance_type_display(),
            'incident_date': str(g.incident_date) if g.incident_date else None,
            'status': g.status,
            'counselor_approval': g.counselor_approval,
            'hod_approval': g.hod_approval,
            'incharge_approval': g.incharge_approval,
            'director_approval': g.director_approval,
            'submission_date': g.submission_date.isoformat() if g.submission_date else None,
        }
        for g in grievance_qs
    ])

    context = {
        'counseling_json': counseling_json,
        'grievance_json': grievance_json,
        'user_role': user_upper,
        'is_superuser': request.user.is_superuser,
        'is_named_counselor': is_named_counselor,
        'filter_opts': json.dumps({
            'branches': branches,
            'sections': sections,
            'year_sems': year_sems,
            'acad_years': acad_years,
            'counselor_map': counselor_map,
        }),
    }
    return render(request, 'admin_approvals.html', context)


@login_required
def student_search_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    roll = request.GET.get('roll', '').strip()
    result = None

    if roll:
        counseling = StudentCounseling.objects.filter(roll_number__iexact=roll).order_by('-last_submission_date').first()
        grievances = list(Grievance.objects.filter(roll_number__iexact=roll).order_by('-submission_date').values(
            'id', 'grievance_type', 'status', 'counselor_approval', 'hod_approval',
            'incharge_approval', 'director_approval', 'submission_date', 'incident_date'
        ))
        for g in grievances:
            if g['submission_date']:
                g['submission_date'] = g['submission_date'].strftime('%d %b %Y')
            if g['incident_date']:
                g['incident_date'] = str(g['incident_date'])

        if counseling:
            result = {
                'found': True,
                'roll': counseling.roll_number,
                'name': counseling.student_name or '',
                'email': counseling.email or '',
                'counselor': counseling.counselor_name or '',
                'branch': counseling.branch or '',
                'section': counseling.section or '',
                'year_sem': counseling.year_sem or '',
                'academic_year': counseling.academic_year or '',
                'submitted': counseling.last_submission_date.strftime('%d %b %Y') if counseling.last_submission_date else None,
                'approval_status': counseling.approval_status,
                'counselor_approval': counseling.counselor_approval,
                'hod_approval': counseling.hod_approval,
                'incharge_approval': counseling.incharge_approval,
                'director_approval': counseling.director_approval,
                'counseling_id': counseling.id,
                'grievances': grievances,
            }
        else:
            # Check if user exists at all
            from django.contrib.auth.models import User as AuthUser
            user_exists = AuthUser.objects.filter(username__iexact=roll).exists()
            result = {
                'found': False,
                'roll': roll,
                'user_exists': user_exists,
                'grievances': grievances,
            }

    context = {
        'roll_query': roll,
        'result_json': json.dumps(result) if result else 'null',
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_student_search.html', context)


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
    if not request.user.is_staff:
        return redirect('dashboard')
    
    from django.contrib.auth.models import User
    from .models import StudentCounseling
    import json
    
    # Capture filters
    roll_filter = request.GET.get('roll_number', '').strip()
    ys_filter = request.GET.get('year_sem', '')
    att_filter = request.GET.get('attendance_search', '').strip()
    br_filter = request.GET.get('branch', '').strip()
    sec_filter = request.GET.get('section', '').strip()
    sty_filter = request.GET.get('student_year', '').strip()
    
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
    
    if roll_filter:
        sc_qs = sc_qs.filter(roll_number__icontains=roll_filter)
    if ys_filter:
        sc_qs = sc_qs.filter(year_sem__iexact=ys_filter.strip())
    if br_filter:
        sc_qs = sc_qs.filter(branch__iexact=br_filter)
    if sec_filter:
        sc_qs = sc_qs.filter(section__iexact=sec_filter)
    if sty_filter:
        sc_qs = sc_qs.filter(student_year__iexact=sty_filter)
        
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
            
    filtered_student_rolls_upper = {roll.upper() for roll in sc_qs.values_list('roll_number', flat=True) if roll}
    counselor_map = {str(sc.roll_number).upper(): getattr(sc, 'counselor_name', '') or '' for sc in sc_qs if sc.roll_number}
    
    users_list = users_qs.values('id', 'username', 'email', 'is_staff', 'is_superuser')
    processed_users = []
    registered_usernames_upper = set()
    
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
        # If no filters are active, we show all.
        username_upper = u['username'].upper()
        if (roll_filter or ys_filter or att_filter or br_filter or sec_filter or sty_filter) and is_student:
            if username_upper not in filtered_student_rolls_upper:
                continue
        
        u['role_label'] = role
        u['counselor_name'] = counselor_map.get(username_upper, '')
        processed_users.append(u)
        registered_usernames_upper.add(username_upper)

    # 3. Handle manual records that match the filters
    all_manual = sc_qs.values('roll_number', 'student_name', 'email', 'added_by_role', 'counselor_name')
    for record in all_manual:
        identifier = str(record['roll_number'] or record['student_name']).upper()
        if identifier in registered_usernames_upper:
            continue
            
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
    student_years_opts = list(StudentCounseling.objects.values_list('student_year', flat=True).distinct().order_by('student_year'))
    branches = list(StudentCounseling.objects.values_list('branch', flat=True).distinct().order_by('branch'))
    sections = list(StudentCounseling.objects.values_list('section', flat=True).distinct().order_by('section'))

    context = {
        'all_students_json': json.dumps(processed_users),
        'is_superuser': request.user.is_superuser,
        'filter_data': json.dumps({
            'years': [y for y in years if y],
            'sems': [s for s in sems if s],
            'student_years': [sy for sy in student_years_opts if sy],
            'branches': [b for b in branches if b],
            'sections': [sec for sec in sections if sec],
            'current': {
                'roll': roll_filter,
                'ys': ys_filter,
                'sy': sty_filter,
                'br': br_filter,
                'sec': sec_filter,
                'att': att_filter
            }
        })
    }
    return render(request, 'admin_users.html', context)

@login_required
def admin_bulk_manage_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    
    all_qs = StudentCounseling.objects.all().order_by('roll_number', '-last_submission_date')
    latest_ids = []
    seen = set()
    for sc in all_qs:
        if sc.roll_number and sc.roll_number not in seen:
            seen.add(sc.roll_number)
            latest_ids.append(sc.id)
            
    sc_qs = StudentCounseling.objects.filter(id__in=latest_ids)
    
    users_qs = User.objects.filter(is_superuser=False, is_staff=False)
    users_list = users_qs.values('id', 'username', 'email')
    processed_users = list(users_list)

    # Build filter options for assign counselor card
    branches   = sorted(set(v for v in sc_qs.values_list('branch', flat=True) if v and v.strip()))
    sections   = sorted(set(v for v in sc_qs.values_list('section', flat=True) if v and v.strip()))
    year_sems  = sorted(set(v for v in sc_qs.values_list('year_sem', flat=True) if v and v.strip()))
    acad_years = sorted(set(v for v in sc_qs.values_list('academic_year', flat=True) if v and v.strip()))

    # Build student list with counselor info for the assign card
    students_with_info = json.dumps([
        {
            'username': sc.roll_number,
            'branch': sc.branch or '',
            'section': sc.section or '',
            'year_sem': sc.year_sem or '',
            'academic_year': sc.academic_year or '',
            'counselor_name': sc.counselor_name or '',
        }
        for sc in sc_qs if sc.roll_number
    ])

    context = {
        'all_students_json': json.dumps(processed_users),
        'students_with_info': students_with_info,
        'is_superuser': request.user.is_superuser,
        'filter_opts': json.dumps({
            'branches': branches,
            'sections': sections,
            'year_sems': year_sems,
            'acad_years': acad_years,
        }),
    }
    return render(request, 'admin_bulk_manage.html', context)

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
            StudentCounseling.objects.filter(roll_number__iexact=roll).delete()
            messages.success(request, f"Manual student record {roll} removed from registry.")
        else:
            # Standard User account and associated data deletion
            try:
                user = User.objects.get(id=user_id)
                username = user.username
                # Clean up all related student data
                StudentCounseling.objects.filter(roll_number__iexact=username).delete()
                Grievance.objects.filter(roll_number__iexact=username).delete()
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
            year_sem = data.get('year_sem', '').strip()
            academic_year = data.get('academic_year', '').strip()
            action = data.get('action', 'assign')
            student_rolls_upper = [str(r).upper() for r in student_rolls]
            
            if action == 'assign':
                update_dict = {}
                if counselor_name: update_dict['counselor_name'] = counselor_name
                if student_year:   update_dict['student_year'] = student_year
                if branch:         update_dict['branch'] = branch
                if section:        update_dict['section'] = section
                if year_sem:       update_dict['year_sem'] = year_sem
                if academic_year:  update_dict['academic_year'] = academic_year
                
                if not update_dict:
                    return JsonResponse({'success': False, 'error': 'No fields provided for update'})
                    
                updated_count = 0
                for roll in student_rolls_upper:
                    try:
                        obj = StudentCounseling.objects.get(roll_number__iexact=roll)
                        for k, v in update_dict.items():
                            setattr(obj, k, v)
                        obj.save()
                        updated_count += 1
                    except StudentCounseling.DoesNotExist:
                        StudentCounseling.objects.create(
                            roll_number=roll.upper(),
                            student_name=roll.upper(),
                            added_by_role=request.user.username.upper(),
                            **update_dict
                        )
                        updated_count += 1
                return JsonResponse({'success': True, 'updated': updated_count})
                
            elif action == 'remove':
                updated_count = 0
                for roll in student_rolls_upper:
                    count = StudentCounseling.objects.filter(roll_number__iexact=roll).update(counselor_name='')
                    if count > 0: updated_count += 1
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
            student_rolls_upper = [str(r).upper() for r in student_rolls]
            
            if not student_rolls_upper:
                return JsonResponse({'success': False, 'error': 'No students selected'})
                
            sc_deleted = 0
            # Iterate case-insensitively to ensure solid deletion
            for roll in student_rolls_upper:
                User.objects.filter(username__iexact=roll).delete()
                deleted, _ = StudentCounseling.objects.filter(roll_number__iexact=roll).delete()
                Grievance.objects.filter(roll_number__iexact=roll).delete()
                if deleted: sc_deleted += 1
            
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
                
                from django.contrib.auth.models import User
                
                def b36(n, l):
                    import string
                    a, b = string.digits + string.ascii_uppercase, ''
                    if n == 0: return '0'.zfill(l)
                    while n: n, i = divmod(n, 36); b = a[i] + b
                    return b.zfill(l)
                    
                s_val = e_val = None
                if s_suf.isdigit() and e_suf.isdigit():
                    s_val, e_val = int(s_suf), int(e_suf)
                else:
                    try:
                        s_val, e_val = int(s_suf, 36), int(e_suf, 36)
                    except ValueError:
                        pass
                
                if s_val is not None and e_val is not None and 0 <= e_val - s_val <= 1000:
                    for i in range(s_val, e_val + 1):
                        roll = prefix + (str(i).zfill(len(s_suf)) if s_suf.isdigit() else b36(i, len(s_suf)))
                        
                        # Create User and Profile
                        if not User.objects.filter(username__iexact=roll).exists():
                            User.objects.create_user(username=roll, password=roll)
                            
                        if not StudentCounseling.objects.filter(roll_number__iexact=roll).exists():
                            StudentCounseling.objects.create(roll_number=roll, student_name=roll, email="", counselor_name=counselor, student_year=student_year, branch=branch, section=section, added_by_role=request.user.username.upper())
                            created_count += 1
            else:
                students = data.get('students', [])
                student_year = str(data.get('student_year', '')).strip()
                branch = str(data.get('branch', '')).strip()
                section = str(data.get('section', '')).strip()
                from django.contrib.auth.models import User
                
                for st in students:
                    roll = str(st.get('roll_number', '')).strip().upper()
                    name = str(st.get('student_name', '')).strip()
                    counselor = str(st.get('counselor_name', '')).strip()
                    if not name: name = roll
                    
                    if roll:
                        if not User.objects.filter(username__iexact=roll).exists():
                            User.objects.create_user(username=roll, password=roll)
                            
                        if not StudentCounseling.objects.filter(roll_number__iexact=roll).exists():
                            StudentCounseling.objects.create(roll_number=roll, student_name=name, email=str(st.get('email', '')).strip(), counselor_name=counselor, student_year=student_year, branch=branch, section=section, added_by_role=request.user.username.upper())
                            created_count += 1
                        
            return JsonResponse({'success': True, 'created': created_count})
        except Exception as e:
            import traceback
            traceback.print_exc()
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

    from .forms import BRANCH_CHOICES, SECTION_CHOICES, YEAR_SEM_CHOICES, ACADEMIC_YEAR_CHOICES
    return render(request, 'student_counseling.html', {
        'form': form,
        'branch_choices': BRANCH_CHOICES[1:],        # skip blank placeholder
        'section_choices': SECTION_CHOICES[1:],
        'year_sem_choices': YEAR_SEM_CHOICES[1:],
        'academic_year_choices': ACADEMIC_YEAR_CHOICES[1:],
    })

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

@login_required
def admin_export_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    # Build filter options from DB
    sems          = sorted(set(v for v in StudentCounseling.objects.values_list('year_sem', flat=True) if v and v.strip()))
    student_years = sorted(set(v for v in StudentCounseling.objects.values_list('student_year', flat=True) if v and v.strip()))
    branches      = sorted(set(v for v in StudentCounseling.objects.values_list('branch', flat=True) if v and v.strip()))
    sections      = sorted(set(v for v in StudentCounseling.objects.values_list('section', flat=True) if v and v.strip()))
    acad_years    = sorted(set(v for v in StudentCounseling.objects.values_list('academic_year', flat=True) if v and v.strip()))

    filter_data = json.dumps({
        'sems':          sems,
        'student_years': student_years,
        'branches':      branches,
        'sections':      sections,
        'acad_years':    acad_years,
    })

    def _build_rows(req):
        roll_filter  = req.GET.get('roll_number', '').strip()
        ys_filter    = req.GET.get('year_sem', '').strip()
        br_filter    = req.GET.get('branch', '').strip()
        sec_filter   = req.GET.get('section', '').strip()
        sty_filter   = req.GET.get('student_year', '').strip()
        acad_filter  = req.GET.get('academic_year', '').strip()

        all_qs = StudentCounseling.objects.all().order_by('roll_number', '-last_submission_date')
        seen, latest_ids = set(), []
        for sc in all_qs:
            if sc.roll_number and sc.roll_number not in seen:
                seen.add(sc.roll_number)
                latest_ids.append(sc.id)
        sc_qs = StudentCounseling.objects.filter(id__in=latest_ids)

        if roll_filter: sc_qs = sc_qs.filter(roll_number__icontains=roll_filter)
        if ys_filter:   sc_qs = sc_qs.filter(year_sem__iexact=ys_filter)
        if br_filter:   sc_qs = sc_qs.filter(branch__iexact=br_filter)
        if sec_filter:  sc_qs = sc_qs.filter(section__iexact=sec_filter)
        if sty_filter:  sc_qs = sc_qs.filter(student_year__iexact=sty_filter)
        if acad_filter: sc_qs = sc_qs.filter(academic_year__iexact=acad_filter)

        registered = {u.username.upper(): u for u in User.objects.filter(is_staff=False, is_superuser=False)}
        rows = []
        for sc in sc_qs.order_by('roll_number'):
            roll_up = (sc.roll_number or '').upper()
            user = registered.get(roll_up)
            rows.append({
                'roll':         sc.roll_number or '',
                'name':         sc.student_name or '',
                'email':        sc.email or (user.email if user else ''),
                'counselor':    sc.counselor_name or '',
                'branch':       sc.branch or '',
                'year':         sc.student_year or '',
                'section':      sc.section or '',
                'year_sem':     sc.year_sem or '',
                'academic_year': sc.academic_year or '',
            })
        return rows

    # JSON preview mode (AJAX call from the page)
    if request.GET.get('preview') == '1':
        rows = _build_rows(request)
        return JsonResponse({'rows': rows, 'count': len(rows)})

    total_count = User.objects.filter(is_staff=False, is_superuser=False).count()

    context = {
        'preview_json': '[]',   # empty on load — user must apply filters first
        'filter_data':  filter_data,
        'total_count':  total_count,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'admin_export.html', context)


@login_required
def export_students_csv(request):
    if not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)
        
    # Capture filters
    roll_filter  = request.GET.get('roll_number', '').strip()
    ys_filter    = request.GET.get('year_sem', '').strip()
    att_filter   = request.GET.get('attendance_search', '').strip()
    br_filter    = request.GET.get('branch', '').strip()
    sec_filter   = request.GET.get('section', '').strip()
    sty_filter   = request.GET.get('student_year', '').strip()
    acad_filter  = request.GET.get('academic_year', '').strip()
    
    # 1. Fetch relevant users
    users_qs = User.objects.filter(is_superuser=False, is_staff=False)
    
    # 2. Extract counseling filters exactly like admin_users_view
    all_qs = StudentCounseling.objects.all().order_by('roll_number', '-last_submission_date')
    latest_ids = []
    seen = set()
    for sc in all_qs:
        if sc.roll_number and sc.roll_number not in seen:
            seen.add(sc.roll_number)
            latest_ids.append(sc.id)
            
    sc_qs = StudentCounseling.objects.filter(id__in=latest_ids)
    
    if roll_filter:  sc_qs = sc_qs.filter(roll_number__icontains=roll_filter)
    if ys_filter:    sc_qs = sc_qs.filter(year_sem__iexact=ys_filter)
    if br_filter:    sc_qs = sc_qs.filter(branch__iexact=br_filter)
    if sec_filter:   sc_qs = sc_qs.filter(section__iexact=sec_filter)
    if sty_filter:   sc_qs = sc_qs.filter(student_year__iexact=sty_filter)
    if acad_filter:  sc_qs = sc_qs.filter(academic_year__iexact=acad_filter)
        
    if att_filter:
        try:
            search_val = att_filter.replace('%', '').strip()
            att_query = float(search_val)
            match_rolls = []
            for sc in sc_qs:
                for i in range(1, 6):
                    val = getattr(sc, f'attendance_percent{i}', None)
                    if val:
                        try:
                            val_clean = str(val).replace('%', '').strip()
                            if abs(float(val_clean) - att_query) < 1.0:
                                match_rolls.append(sc.roll_number)
                                break
                        except (ValueError, TypeError): continue
            sc_qs = sc_qs.filter(roll_number__in=match_rolls)
        except ValueError:
            pass
            
    filtered_student_rolls_upper = {roll.upper() for roll in sc_qs.values_list('roll_number', flat=True) if roll}
    
    # Counselor/Branch mappings
    sc_details = {
        str(sc.roll_number).upper(): {
            'counselor': getattr(sc, 'counselor_name', '') or '',
            'branch': getattr(sc, 'branch', '') or '',
            'year': getattr(sc, 'student_year', '') or '',
            'section': getattr(sc, 'section', '') or ''
        } for sc in sc_qs if sc.roll_number
    }
    
    export_list = []
    
    # If any filter is active, only show students passing criteria
    has_filter = bool(roll_filter or ys_filter or att_filter or br_filter or sec_filter or sty_filter)
    
    for u in users_qs:
        username_upper = u.username.upper()
        if has_filter:
            if username_upper not in filtered_student_rolls_upper:
                continue
                
        details = sc_details.get(username_upper, {})
        export_list.append({
            'Roll Number': u.username,
            'Name': getattr(u, 'first_name', '') or getattr(u, 'last_name', '') or '',
            'Email': u.email,
            'Counselor': details.get('counselor', ''),
            'Branch': details.get('branch', ''),
            'Year': details.get('year', ''),
            'Section': details.get('section', '')
        })
        
    all_manual = sc_qs.values('roll_number', 'student_name', 'email', 'counselor_name', 'branch', 'student_year', 'section')
    registered_rolls = {u.username.upper() for u in users_qs}
    
    for record in all_manual:
        identifier = str(record['roll_number'] or record['student_name']).upper()
        if identifier in registered_rolls: continue
        # if filter is enabled, this query already handles manuals!
        export_list.append({
            'Roll Number': identifier,
            'Name': record['student_name'] or '',
            'Email': record['email'] or '',
            'Counselor': record['counselor_name'] or '',
            'Branch': record['branch'] or '',
            'Year': record['student_year'] or '',
            'Section': record['section'] or ''
        })
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_students_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Roll Number', 'Name', 'Email', 'Counselor', 'Branch', 'Year', 'Section'])
    
    for student in export_list:
        writer.writerow([
            student['Roll Number'],
            student['Name'],
            student['Email'],
            student['Counselor'],
            student['Branch'],
            student['Year'],
            student['Section']
        ])
        
    return response
