from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import StudentCounseling, Grievance

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'grievance_type', 'incident_date', 'submission_date', 'status', 'view_form_button']
    list_filter = ['status', 'grievance_type', 'counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval']
    search_fields = ['roll_number', 'description']
    ordering = ['-submission_date']
    actions = ['approve_grievance', 'reject_grievance']

    @admin.action(description='Approve selected grievances (Set to Resolved)')
    def approve_grievance(self, request, queryset):
        queryset.update(status='Resolved')

    @admin.action(description='Reject selected grievances (Set to Rejected)')
    def reject_grievance(self, request, queryset):
        queryset.update(status='Rejected')

    # Django's native ChangeList automatically handles list_filter fields
    # when they use the '__exact' suffix in the GET request.
    # We do NOT need to override get_queryset for these standard fields.
    def get_queryset(self, request):
        return super().get_queryset(request).distinct()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Determine the currently active filters to persist UI state.
        status_val = (request.GET.get('status__exact') or '').strip()
        type_val = (request.GET.get('grievance_type__exact') or '').strip()
        q_val = request.GET.get('q', '')
        
        from .models import Grievance
        types = Grievance.objects.values_list('grievance_type', flat=True).distinct().order_by('grievance_type')

        type_options = [format_html('<option value="" {}>All Types</option>', 'selected' if not type_val else '')]
        for t in types:
            if not t: continue
            type_options.append(format_html('<option value="{}" {}>{}</option>', t, 'selected' if type_val == t else '', t))
            
        status_options = [format_html('<option value="" {}>All Statuses</option>', 'selected' if not status_val else '')]
        for s in ['Pending', 'In Progress', 'Resolved', 'Rejected']:
            status_options.append(format_html('<option value="{}" {}>{}</option>', s, 'selected' if status_val == s else '', s))

        # IMPORTANT: The select names MUST have the "__exact" suffix.
        # If they don't, Django's native Search Bar and Pagination will consider them
        # invalid parameters and permanently delete them from the URL when you search.
        extra_context['custom_search_form'] = format_html("""
            <div style="background: #fff; padding: 15px; margin-bottom: 20px; border: 1px solid #ccc; display: flex; align-items: center;">
                <form action="." method="get" style="display: flex; gap: 15px; align-items: center; width: 100%; flex-wrap: wrap;">
                    <input type="hidden" name="q" value="{}">
                    <div style="display:flex; align-items:center;">
                        <label style="margin-right: 5px; font-weight:bold;">Grievance Type:</label>
                        <select name="grievance_type__exact" style="padding: 4px; border: 1px solid #ccc;">{}</select>
                    </div>
                    <div style="display:flex; align-items:center;">
                        <label style="margin-right: 5px; font-weight:bold;">Status:</label>
                        <select name="status__exact" style="padding: 4px; border: 1px solid #ccc;">{}</select>
                    </div>
                    <div style="display:flex; align-items:center;">
                        <input type="submit" value="Apply Filters" style="padding: 6px 15px; background:#417690; color:#fff; border:none; border-radius:3px; cursor:pointer;">
                        <a href="?" style="margin-left:15px; color:#ba2121; text-decoration:none; font-weight:bold;">Clear filters</a>
                    </div>
                </form>
            </div>
        """, q_val, mark_safe("".join(type_options)), mark_safe("".join(status_options)))
        return super().changelist_view(request, extra_context=extra_context)

    def view_form_button(self, obj):
        if not obj or not obj.pk:
            return format_html('<span>(Save to view form)</span>')
        from django.urls import reverse
        url = reverse('admin_view_grievance', args=[obj.pk])
        return format_html('<a class="button" href="{}" style="background: #e11d48; color: white;">View Form</a>', url)
    
    view_form_button.short_description = 'Actions'

    fieldsets = (
        ('Grievance Details', {
            'fields': (('roll_number', 'grievance_type'), ('incident_date', 'view_form_button'), 'description', 'attachment', 'status', 'reply')
        }),
        ('Approval Workflow', {
            'fields': ('counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = ['view_form_button']
        if request.user.is_superuser:
            return readonly
        
        all_appr = ['status', 'counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval']
        user_upper = request.user.username.upper()
        
        role_map = {
            'COUNSELOR': 'counselor_approval',
            'HOD': 'hod_approval',
            'INCHARGE': 'incharge_approval',
            'DIRECTOR': 'director_approval'
        }
        
        target_appr = role_map.get(user_upper)
        if target_appr:
            readonly.extend([f for f in all_appr if f != target_appr])
            return readonly
            
        readonly.extend(all_appr)
        return readonly

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

class AttendanceSearchFilter(admin.SimpleListFilter):
    title = 'Attendance'
    parameter_name = 'attendance_search'
    template = 'admin/filter.html'

    def lookups(self, request, model_admin):
        # Hide from sidebar
        return ()

    def queryset(self, request, queryset):
        # Allow get_queryset to handle the actual computation
        return queryset

@admin.register(StudentCounseling)
class StudentCounselingAdmin(admin.ModelAdmin):
    class Media:
        js = ('admin/js/admin_accordion.js',)

    list_display = [
         'student_name', 'roll_number', 'counselor_name',
        'get_pass_count', 'get_fail_count',
        'father_phone', 'get_attendance_display','view_form_button',
    ]
    list_filter = [
        'academic_year', 'year_sem', 'approval_status', 'counselor_name', 
        'residence_hostel', 'residence_days_scholar', AttendanceSearchFilter,
        'counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval'
    ]

    search_fields = [
        'student_name', 'roll_number', 'counselor_name', 'email', 'student_phone', 'father_phone',
        'subject1', 'subject2', 'subject3', 'subject4', 'subject5',
    ]
    
    actions = ['approve_counseling', 'reject_counseling']

    def save_model(self, request, obj, form, change):
        # Automatically tag which role added the record
        if not obj.pk:
            un = request.user.username.upper()
            if request.user.is_superuser:
                obj.added_by_role = "Add by Superadmin"
            elif 'COUNSELOR' in un:
                obj.added_by_role = "Add by Counselor"
            elif 'HOD' in un:
                obj.added_by_role = "Add by HOD"
            elif 'INCHARGE' in un:
                obj.added_by_role = "Add by Incharge"
            elif 'DIRECTOR' in un:
                obj.added_by_role = "Add by Director"
            else:
                obj.added_by_role = "Add by Admin Staff"
        super().save_model(request, obj, form, change)

    @admin.action(description='Approve selected student counselings')
    def approve_counseling(self, request, queryset):
        queryset.update(approval_status='Approved')

    @admin.action(description='Reject selected student counselings')
    def reject_counseling(self, request, queryset):
        queryset.update(approval_status='Rejected')

    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('student_name', 'roll_number'),
                ('email', 'student_phone', 'father_phone'),
                ('counselor_name', 'approval_status'),
                ('academic_year', 'year_sem'),
                ('student_year', 'branch', 'section'),
                ('rtf', 'mq', 'any_other'),
                ('last_submission_date', 'view_form_button')
            ),
            'classes': ('collapse',)
        }),
        ('Residence', {
            'fields': (
                ('residence_hostel', 'residence_days_scholar', 'residence_college_bus', 'residence_rtc_bus'),
                ('hostel_name', 'room_no'),
                ('day_scholar_address', 'bus_route', 'bus_no'),
                ('vehicle_details', 'rtc_travel_place'),
                ('roommate1', 'roll_no1'),
                ('roommate2', 'roll_no2'),
                ('roommate3', 'roll_no3'),
                ('ds_name1', 'ds_roll1'),
                ('ds_name2', 'ds_roll2'),
                ('ds_name3', 'ds_roll3'),
            ),
            'classes': ('collapse',)
        }),
        ('Academic Records', {
            'fields': (
                # Subject 1
                'subject1',
                ('mid1_1', 'mid2_1', 'sessional1', 'endsem1', 'total1'),
                ('result1', 'pass_year1'),
                # Subject 2
                'subject2',
                ('mid1_2', 'mid2_2', 'sessional2', 'endsem2', 'total2'),
                ('result2', 'pass_year2'),
                # Subject 3
                'subject3',
                ('mid1_3', 'mid2_3', 'sessional3', 'endsem3', 'total3'),
                ('result3', 'pass_year3'),
                # Subject 4
                'subject4',
                ('mid1_4', 'mid2_4', 'sessional4', 'endsem4', 'total4'),
                ('result4', 'pass_year4'),
                # Subject 5
                'subject5',
                ('mid1_5', 'mid2_5', 'sessional5', 'endsem5', 'total5'),
                ('result5', 'pass_year5'),
            ),
            'classes': ('collapse',)
        }),
        ('Monthly Follow-up (1)', {
            'fields': (
                ('month1', 'monthly_letter1'),
                ('classes_conducted1', 'classes_attended1', 'attendance_percent1'),
                'followup1'
            ),
            'classes': ('collapse',)
        }),
        ('Monthly Follow-up (2)', {
            'fields': (
                ('month2', 'monthly_letter2'),
                ('classes_conducted2', 'classes_attended2', 'attendance_percent2'),
                'followup2'
            ),
            'classes': ('collapse',)
        }),
        ('Monthly Follow-up (3)', {
            'fields': (
                ('month3', 'monthly_letter3'),
                ('classes_conducted3', 'classes_attended3', 'attendance_percent3'),
                'followup3'
            ),
            'classes': ('collapse',)
        }),
        ('Monthly Follow-up (4)', {
            'fields': (
                ('month4', 'monthly_letter4'),
                ('classes_conducted4', 'classes_attended4', 'attendance_percent4'),
                'followup4'
            ),
            'classes': ('collapse',)
        }),
        ('Monthly Follow-up (5)', {
            'fields': (
                ('month5', 'monthly_letter5'),
                ('classes_conducted5', 'classes_attended5', 'attendance_percent5'),
                'followup5'
            ),
            'classes': ('collapse',)
        }),
        ('Counseling Sessions', {
            'fields': (
                ('counseling_date1', 'counseling_description1'),
            ),
            'classes': ('collapse',)
        }),
        ('Prizes & Certifications', {
            'fields': (
                'prizes_participations1',
                'prizes_participations2',
                'prizes_participations3',
                'prizes_participations4',
                'prizes_participations5',
            ),
            'classes': ('collapse',)
        }),
        ('Approval Workflow', {
            'fields': (
                'counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval'
            ),
        }),
    )

    def view_form_button(self, obj):
        if not obj or not obj.pk:
            return format_html('<span>(Save to view form)</span>')
        from django.urls import reverse
        url = reverse('admin_view_counseling', args=[obj.pk])
        return format_html('<a class="button" href="{}" style="background: #6366f1; color: white;">View Form</a>', url)
    
    view_form_button.short_description = 'Actions'

    def get_readonly_fields(self, request, obj=None):
        readonly = ['view_form_button']
        if request.user.is_superuser:
            return readonly
        
        all_appr = ['approval_status', 'counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval']
        user_upper = request.user.username.upper()
        
        role_map = {
            'COUNSELOR': 'counselor_approval',
            'HOD': 'hod_approval',
            'INCHARGE': 'incharge_approval',
            'DIRECTOR': 'director_approval'
        }
        
        target_appr = role_map.get(user_upper)
        if target_appr:
            readonly.extend([f for f in all_appr if f != target_appr])
            return readonly
            
        readonly.extend(all_appr)
        return readonly

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # 1. Strictly isolate the query to the single most recent active record per student
        latest_ids = []
        seen = set()
        for sc in qs.order_by('roll_number', '-last_submission_date'):
            if sc.roll_number and sc.roll_number not in seen:
                seen.add(sc.roll_number)
                latest_ids.append(sc.id)
        queryset = qs.filter(id__in=latest_ids)
        
        # Explicitly filter by our custom top-bar parameters
        ay = (request.GET.get('academic_year') or request.GET.get('academic_year__exact') or '').strip()
        ys = (request.GET.get('year_sem') or request.GET.get('year_sem__exact') or '').strip()
        st = (request.GET.get('approval_status') or request.GET.get('approval_status__exact') or '').strip()
        
        if ay:
            queryset = queryset.filter(academic_year__iexact=ay)
        if ys:
            queryset = queryset.filter(year_sem__iexact=ys)
        if st:
            queryset = queryset.filter(approval_status__iexact=st)

        attendance_search = request.GET.get('attendance_search', '').strip()

        if attendance_search:
            try:
                # Same cleanup for the user's initial search query
                search_val = attendance_search.replace('%', '').strip()
                attendance_query = float(search_val)
                filtered_ids = []
                for student in queryset:
                    matches = False
                    for i in range(1, 6):
                        att = getattr(student, f'attendance_percent{i}', None)
                        if att:
                            try:
                                # Remove % signs from DB values so python can actually convert it to a float
                                att_clean = str(att).replace('%', '').strip()
                                val_f = float(att_clean)
                                if abs(val_f - attendance_query) < 1.0:
                                    matches = True
                                    break
                            except (ValueError, TypeError): continue
                    if matches:
                        filtered_ids.append(student.id)
                
                queryset = queryset.filter(id__in=filtered_ids)
            except ValueError:
                pass
        return queryset

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Capture ALL possible parameter variations from URL to ensure UI stays persistent
        ay_val = request.GET.get('academic_year') or request.GET.get('academic_year__exact') or ''
        ys_val = request.GET.get('year_sem') or request.GET.get('year_sem__exact') or ''
        status_val = request.GET.get('approval_status') or request.GET.get('approval_status__exact') or ''
        att_val = request.GET.get('attendance_search', '')
        q_val = request.GET.get('q', '')

        from .models import StudentCounseling
        years = StudentCounseling.objects.values_list('academic_year', flat=True).distinct().order_by('academic_year')
        sems = StudentCounseling.objects.values_list('year_sem', flat=True).distinct().order_by('year_sem')

        # Build options with persistent selection
        ay_options = [format_html('<option value="" {}>All</option>', 'selected' if not ay_val else '')]
        for y in years:
            if not y: continue
            selected = 'selected' if ay_val == y else ''
            ay_options.append(format_html('<option value="{}" {}>{}</option>', y, selected, y))
            
        ys_options = [format_html('<option value="" {}>All</option>', 'selected' if not ys_val else '')]
        for y in sems:
            if not y: continue
            selected = 'selected' if ys_val == y else ''
            ys_options.append(format_html('<option value="{}" {}>{}</option>', y, selected, y))
            
        status_options = [format_html('<option value="" {}>All Statuses</option>', 'selected' if not status_val else '')]
        for s in ['Pending', 'Approved', 'Rejected']:
            selected = 'selected' if status_val == s else ''
            status_options.append(format_html('<option value="{}" {}>{}</option>', s, selected, s))

        extra_context['custom_search_form'] = format_html("""
            <div style="background: #fff; padding: 15px; margin-bottom: 20px; border: 1px solid #ccc;">
                <form action="." method="get" style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
                    <div style="display:flex; align-items:center;">
                        <label style="margin-right: 5px; font-weight:bold;">Academic Year:</label>
                        <select name="academic_year__exact" style="padding: 4px; border: 1px solid #ccc;">{}</select>
                    </div>
                    <div style="display:flex; align-items:center;">
                        <label style="margin-right: 5px; font-weight:bold;">Year of study:</label>
                        <select name="year_sem__exact" style="padding: 4px; border: 1px solid #ccc;">{}</select>
                    </div>
                    <div style="display:flex; align-items:center;">
                        <label style="margin-right: 5px; font-weight:bold;">Status:</label>
                        <select name="approval_status__exact" style="padding: 4px; border: 1px solid #ccc;">{}</select>
                    </div>
                    <div style="display:flex; align-items:center; border-left: 1px solid #ddd; padding-left: 15px;">
                        <label style="margin-right: 5px; font-weight:bold;">Attendance %:</label>
                        <input type="text" name="attendance_search" value="{}" placeholder="e.g. 75" style="padding: 4px; width: 60px; border: 1px solid #ccc;">
                    </div>
                    
                    <input type="hidden" name="q" value="{}">
                    
                    <div style="display:flex; align-items:center;">
                        <input type="submit" value="Apply Filters" style="padding: 6px 15px; background:#417690; color:#fff; border:none; border-radius:3px; cursor:pointer; font-weight:bold;">
                        <a href="?" style="margin-left:15px; color:#ba2121; text-decoration:none; font-size:13px;">Clear all</a>
                    </div>
                </form>
            </div>
        """, mark_safe("".join(ay_options)), mark_safe("".join(ys_options)), mark_safe("".join(status_options)), att_val, q_val or '')

        # Subject search-based pass/fail summary
        search_query = request.GET.get('q', '')
        search_query = search_query.strip().lower() if search_query else ''
        if search_query:
            subject_names = set()
            filtered_queryset = self.get_queryset(request)
            for student in filtered_queryset:
                for i in range(1, 6):
                    subject = getattr(student, f'subject{i}', '')
                    subject = subject.strip().lower() if subject else ''
                    if subject:
                        subject_names.add(subject)

            if search_query in subject_names:
                subject_pass = 0
                subject_fail = 0
                for student in filtered_queryset:
                    for i in range(1, 6):
                        subject = getattr(student, f'subject{i}', '')
                        subject = subject.lower() if subject else ''
                        result = getattr(student, f'result{i}', '')
                        result = str(result or '')  # Convert None to empty string
                        if search_query in subject:
                            if result.upper() == 'P':
                                subject_pass += 1
                            elif result.upper() == 'F':
                                subject_fail += 1
                            break
                extra_context['title'] = format_html(
                    'Subject Summary → Passed: <span style="color:green">{}</span> | '
                    'Failed: <span style="color:red">{}</span> | Total: {}',
                    subject_pass, subject_fail, subject_pass + subject_fail
                )

        return super().changelist_view(request, extra_context=extra_context)

    def get_pass_count(self, obj):
        return sum(1 for i in range(1, 6) if (str(getattr(obj, f'result{i}', '') or '')).upper() == 'P')

    get_pass_count.short_description = 'Passes'

    def get_fail_count(self, obj):
        return sum(1 for i in range(1, 6) if (str(getattr(obj, f'result{i}', '') or '')).upper() == 'F')

    get_fail_count.short_description = 'Fails'

    def get_academic_records_table(self, obj):
        """Display all academic records in a compact table format"""
        records = []
        for i in range(1, 6):
            subject = getattr(obj, f'subject{i}', '')
            if subject:  # Only show if subject exists
                records.append({
                    'subject': subject,
                    'mid1': getattr(obj, f'mid1_{i}', '-'),
                    'mid2': getattr(obj, f'mid2_{i}', '-'),
                    'sessional': getattr(obj, f'sessional{i}', '-'),
                    'endsem': getattr(obj, f'endsem{i}', '-'),
                    'total': getattr(obj, f'total{i}', '-'),
                    'result': getattr(obj, f'result{i}', ''),
                    'year': getattr(obj, f'pass_year{i}', '-')
                })
        
        if not records:
            return '-'
        
        # Build HTML table
        table_html = '''
        <table style="border-collapse: collapse; font-size: 11px; width: 100%;">
            <thead>
                <tr style="background: #f0f0f0;">
                    <th style="border: 1px solid #ddd; padding: 4px;">Subject</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">Mid1</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">Mid2</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">Sess</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">End</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">Total</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">Result</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">Year</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for record in records:
            result = str(record['result'] or '')
            result_color = 'green' if result.upper() == 'P' else 'red' if result.upper() == 'F' else 'black'
            table_html += f'''
                <tr>
                    <td style="border: 1px solid #ddd; padding: 4px;">{record['subject']}</td>
                    <td style="border: 1px solid #ddd; padding: 4px; text-align: center;">{record['mid1']}</td>
                    <td style="border: 1px solid #ddd; padding: 4px; text-align: center;">{record['mid2']}</td>
                    <td style="border: 1px solid #ddd; padding: 4px; text-align: center;">{record['sessional']}</td>
                    <td style="border: 1px solid #ddd; padding: 4px; text-align: center;">{record['endsem']}</td>
                    <td style="border: 1px solid #ddd; padding: 4px; text-align: center;"><strong>{record['total']}</strong></td>
                    <td style="border: 1px solid #ddd; padding: 4px; text-align: center; color: {result_color}; font-weight: bold;">{result.upper()}</td>
                    <td style="border: 1px solid #ddd; padding: 4px; text-align: center;">{record['year']}</td>
                </tr>
            '''
        
        table_html += '</tbody></table>'
        return format_html(table_html)
    
    get_academic_records_table.short_description = 'Academic Records'

    def get_subjects_display(self, obj):
        subjects = []
        for i in range(1, 6):
            subject = getattr(obj, f'subject{i}', '')
            result = getattr(obj, f'result{i}', '')
            # Ensure result is not None before calling .upper()
            result = str(result or '')  # Convert None to empty string
            if subject and result:
                color = 'green' if result.upper() == 'P' else 'red' if result.upper() == 'F' else 'black'
                subjects.append(f"{subject}: <strong style='color:{color}'>{result.upper()}</strong>")
        return format_html("<br>".join(subjects) if subjects else 'No subjects')

    get_subjects_display.short_description = 'Subjects & Results'

    def get_attendance_display(self, obj):
        latest_attendance = None
        for i in reversed(range(1, 6)):
            att = getattr(obj, f'attendance_percent{i}', None)
            if att is not None:
                latest_attendance = att
                break
        if latest_attendance is not None:
            color = 'green' if float(latest_attendance) >= 75 else 'orange' if float(latest_attendance) >= 60 else 'red'
            return format_html('<span style="color:{}">{}</span>', color, latest_attendance)
        return '-'

    get_attendance_display.short_description = 'Latest Attendance %'
