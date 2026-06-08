from django.db import models

class StudentCounseling(models.Model):
    # Basic Information
    year_sem = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=20)
    rtf = models.BooleanField(default=False)
    mq = models.BooleanField(default=False)
    any_other = models.BooleanField(default=False)
    counselor_name = models.CharField(max_length=100)
    student_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    student_year = models.CharField(max_length=20, blank=True, null=True, verbose_name="Year")
    branch = models.CharField(max_length=50, blank=True, null=True)
    section = models.CharField(max_length=20, blank=True, null=True)
    approval_status = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    counselor_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    hod_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    incharge_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    director_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    # Meta Information
    last_submission_date = models.DateTimeField(null=True, blank=True)
    added_by_role = models.CharField(max_length=50, blank=True, null=True, verbose_name="Added by Role")
    
    student_phone = models.CharField(max_length=15)
    father_phone = models.CharField(max_length=15)
    
    # Residence Information
    residence_hostel = models.BooleanField(default=False)
    residence_days_scholar = models.BooleanField(default=False)
    residence_college_bus = models.BooleanField(default=False)
    residence_rtc_bus = models.BooleanField(default=False)
    
    hostel_name = models.CharField(max_length=100, blank=True, null=True)
    room_no = models.CharField(max_length=10, blank=True, null=True)
    
    # Roommates
    roommate1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Roommate 1")
    roll_no1 = models.CharField(max_length=10, blank=True, null=True, verbose_name="Roll No 1")
    roommate2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Roommate 2")
    roll_no2 = models.CharField(max_length=10, blank=True, null=True, verbose_name="Roll No 2")
    roommate3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Roommate 3")
    roll_no3 = models.CharField(max_length=10, blank=True, null=True, verbose_name="Roll No 3")
    
    # Transportation
    bus_route = models.CharField(max_length=100, blank=True, null=True)
    bus_no = models.CharField(max_length=10, blank=True, null=True)
    rtc_travel_place = models.CharField(max_length=100, blank=True, null=True)
    vehicle_details = models.CharField(max_length=100, blank=True, null=True)
    
    # Days Scholar Information
    day_scholar_address = models.TextField(blank=True, null=True, verbose_name="Day Scholar Address")
    ds_name1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="DS Name 1")
    ds_roll1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="DS Roll 1")
    ds_name2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="DS Name 2")
    ds_roll2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="DS Roll 2")
    ds_name3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="DS Name 3")
    ds_roll3 = models.CharField(max_length=20, blank=True, null=True, verbose_name="DS Roll 3")
    
    # Monthly Follow-up
    month1 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Month")
    classes_conducted1 = models.IntegerField(blank=True, null=True, verbose_name="Classes Conducted")
    classes_attended1 = models.IntegerField(blank=True, null=True, verbose_name="Classes Attended")
    attendance_percent1 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Attendance %")
    monthly_letter1 = models.CharField(max_length=3, blank=True, null=True, choices=[('Yes', 'Yes'), ('No', 'No')], verbose_name="Monthly Letter")
    followup1 = models.TextField(blank=True, null=True, verbose_name="Follow-up")
    
    month2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Month")
    classes_conducted2 = models.IntegerField(blank=True, null=True, verbose_name="Classes Conducted")
    classes_attended2 = models.IntegerField(blank=True, null=True, verbose_name="Classes Attended")
    attendance_percent2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Attendance %")
    monthly_letter2 = models.CharField(max_length=3, blank=True, null=True, choices=[('Yes', 'Yes'), ('No', 'No')], verbose_name="Monthly Letter")
    followup2 = models.TextField(blank=True, null=True, verbose_name="Follow-up")
    
    month3 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Month")
    classes_conducted3 = models.IntegerField(blank=True, null=True, verbose_name="Classes Conducted")
    classes_attended3 = models.IntegerField(blank=True, null=True, verbose_name="Classes Attended")
    attendance_percent3 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Attendance %")
    monthly_letter3 = models.CharField(max_length=3, blank=True, null=True, choices=[('Yes', 'Yes'), ('No', 'No')], verbose_name="Monthly Letter")
    followup3 = models.TextField(blank=True, null=True, verbose_name="Follow-up")
    
    month4 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Month")
    classes_conducted4 = models.IntegerField(blank=True, null=True, verbose_name="Classes Conducted")
    classes_attended4 = models.IntegerField(blank=True, null=True, verbose_name="Classes Attended")
    attendance_percent4 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Attendance %")
    monthly_letter4 = models.CharField(max_length=3, blank=True, null=True, choices=[('Yes', 'Yes'), ('No', 'No')], verbose_name="Monthly Letter")
    followup4 = models.TextField(blank=True, null=True, verbose_name="Follow-up")
    
    month5 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Month")
    classes_conducted5 = models.IntegerField(blank=True, null=True, verbose_name="Classes Conducted")
    classes_attended5 = models.IntegerField(blank=True, null=True, verbose_name="Classes Attended")
    attendance_percent5 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Attendance %")
    monthly_letter5 = models.CharField(max_length=3, blank=True, null=True, choices=[('Yes', 'Yes'), ('No', 'No')], verbose_name="Monthly Letter")
    followup5 = models.TextField(blank=True, null=True, verbose_name="Follow-up")
    
    # Academic Record
    subject1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Subject")
    mid1_1 = models.IntegerField(blank=True, null=True, verbose_name="Mid 1")
    mid2_1 = models.IntegerField(blank=True, null=True, verbose_name="Mid 2")
    sessional1 = models.IntegerField(blank=True, null=True, verbose_name="Sessional")
    endsem1 = models.IntegerField(blank=True, null=True, verbose_name="Endsem")
    total1 = models.IntegerField(blank=True, null=True, verbose_name="Total")
    result1 = models.CharField(max_length=1, choices=[('P', 'Pass'), ('F', 'Fail')], blank=True, null=True, verbose_name="Result")
    pass_year1 = models.CharField(max_length=4, blank=True, null=True, verbose_name="Pass Year")
    
    subject2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Subject")
    mid1_2 = models.IntegerField(blank=True, null=True, verbose_name="Mid 1")
    mid2_2 = models.IntegerField(blank=True, null=True, verbose_name="Mid 2")
    sessional2 = models.IntegerField(blank=True, null=True, verbose_name="Sessional")
    endsem2 = models.IntegerField(blank=True, null=True, verbose_name="Endsem")
    total2 = models.IntegerField(blank=True, null=True, verbose_name="Total")
    result2 = models.CharField(max_length=1, choices=[('P', 'Pass'), ('F', 'Fail')], blank=True, null=True, verbose_name="Result")
    pass_year2 = models.CharField(max_length=4, blank=True, null=True, verbose_name="Pass Year")
    
    subject3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Subject")
    mid1_3 = models.IntegerField(blank=True, null=True, verbose_name="Mid 1")
    mid2_3 = models.IntegerField(blank=True, null=True, verbose_name="Mid 2")
    sessional3 = models.IntegerField(blank=True, null=True, verbose_name="Sessional")
    endsem3 = models.IntegerField(blank=True, null=True, verbose_name="Endsem")
    total3 = models.IntegerField(blank=True, null=True, verbose_name="Total")
    result3 = models.CharField(max_length=1, choices=[('P', 'Pass'), ('F', 'Fail')], blank=True, null=True, verbose_name="Result")
    pass_year3 = models.CharField(max_length=4, blank=True, null=True, verbose_name="Pass Year")
    
    subject4 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Subject")
    mid1_4 = models.IntegerField(blank=True, null=True, verbose_name="Mid 1")
    mid2_4 = models.IntegerField(blank=True, null=True, verbose_name="Mid 2")
    sessional4 = models.IntegerField(blank=True, null=True, verbose_name="Sessional")
    endsem4 = models.IntegerField(blank=True, null=True, verbose_name="Endsem")
    total4 = models.IntegerField(blank=True, null=True, verbose_name="Total")
    result4 = models.CharField(max_length=1, choices=[('P', 'Pass'), ('F', 'Fail')], blank=True, null=True, verbose_name="Result")
    pass_year4 = models.CharField(max_length=4, blank=True, null=True, verbose_name="Pass Year")
    
    subject5 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Subject")
    mid1_5 = models.IntegerField(blank=True, null=True, verbose_name="Mid 1")
    mid2_5 = models.IntegerField(blank=True, null=True, verbose_name="Mid 2")
    sessional5 = models.IntegerField(blank=True, null=True, verbose_name="Sessional")
    endsem5 = models.IntegerField(blank=True, null=True, verbose_name="Endsem")
    total5 = models.IntegerField(blank=True, null=True, verbose_name="Total")
    result5 = models.CharField(max_length=1, choices=[('P', 'Pass'), ('F', 'Fail')], blank=True, null=True, verbose_name="Result")
    pass_year5 = models.CharField(max_length=4, blank=True, null=True, verbose_name="Pass Year")
    
    # Counseling Sessions
    counseling_date1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Counseling Date")
    counseling_description1 = models.TextField(blank=True, null=True, verbose_name="Counseling Description")
    prizes_participations1 = models.TextField(blank=True, null=True, verbose_name="Prizes & Participations")
    
    counseling_date2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Counseling Date")
    prizes_participations2 = models.TextField(blank=True, null=True, verbose_name="Prizes & Participations")
    
    counseling_date3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Counseling Date")
    prizes_participations3 = models.TextField(blank=True, null=True, verbose_name="Prizes & Participations")
    
    counseling_date4 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Counseling Date")
    prizes_participations4 = models.TextField(blank=True, null=True, verbose_name="Prizes & Participations")
    
    counseling_date5 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Counseling Date")
    prizes_participations5 = models.TextField(blank=True, null=True, verbose_name="Prizes & Participations")
    
    def __str__(self):
        return self.student_name

class Grievance(models.Model):
    GRIEVANCE_TYPES = [
        ('Academic', 'Academic (Marks, Syllabus, etc.)'),
        ('Facility', 'Facilities (Infrastructure, Library, etc.)'),
        ('Administrative', 'Administrative (Fee, ID card, etc.)'),
        ('Ragging', 'Ragging / Harassment'),
        ('Other', 'Other'),
    ]

    roll_number = models.CharField(max_length=20)
    grievance_type = models.CharField(max_length=50, choices=GRIEVANCE_TYPES)
    incident_date = models.DateField()
    description = models.TextField()
    attachment = models.FileField(upload_to='grievance_attachments/', null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    counselor_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    hod_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    incharge_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    director_approval = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    reply = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.roll_number} - {self.grievance_type} ({self.status})"