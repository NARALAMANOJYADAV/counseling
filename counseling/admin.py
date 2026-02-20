from django.contrib import admin
from django.utils.html import format_html
from .models import StudentCounseling, Grievance

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'grievance_type', 'incident_date', 'submission_date', 'status', 'view_form_button']
    list_filter = ['status', 'grievance_type', 'counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval']
    search_fields = ['roll_number', 'description']
    ordering = ['-submission_date']

    def view_form_button(self, obj):
        from django.urls import reverse
        url = reverse('admin_view_grievance', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank" style="background: #e11d48; color: white;">View Form</a>', url)
    
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
        'residence_hostel', 'residence_days_scholar',
        'counselor_approval', 'hod_approval', 'incharge_approval', 'director_approval'
    ]

    search_fields = [
        'student_name', 'roll_number', 'counselor_name', 'email', 'student_phone', 'father_phone',
        'subject1', 'subject2', 'subject3', 'subject4', 'subject5',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('student_name', 'roll_number'),
                ('email', 'student_phone', 'father_phone'),
                ('counselor_name', 'approval_status'),
                ('academic_year', 'year_sem'),
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
        from django.urls import reverse
        url = reverse('admin_view_counseling', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank" style="background: #6366f1; color: white;">View Form</a>', url)
    
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
        queryset = super().get_queryset(request)
        attendance_search = request.GET.get('attendance_search', '').strip()

        # Store for UI form
        self.attendance_search = attendance_search

        if attendance_search:
            try:
                attendance_val = float(attendance_search)
                filtered_ids = []
                for student in queryset:
                    latest_attendance = None
                    for i in reversed(range(1, 6)):
                        att = getattr(student, f'attendance_percent{i}', None)
                        if att is not None:
                            latest_attendance = float(att)
                            break
                    if latest_attendance is not None and abs(latest_attendance - attendance_val) < 0.05:
                        filtered_ids.append(student.id)
                queryset = queryset.filter(id__in=filtered_ids)
            except ValueError:
                pass  # Ignore if input is not a valid float

        return queryset

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Add attendance search UI to top right
        extra_context['attendance_search_form'] = format_html("""
            <div style="float:right;margin:10px 20px;">
                <form method="get">
                    <input type="text" name="attendance_search" value="{}" placeholder="Search by Attendance">
                    <input type="submit" value="Search">
                    <a href="?" style="margin-left:10px;">Clear</a>
                </form>
                <small style="color:gray;">Matches students with latest attendance ≈ entered value (±0.05)</small>
            </div>
        """, self.attendance_search if hasattr(self, 'attendance_search') else '')

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
