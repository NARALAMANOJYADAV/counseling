from django import forms
from .models import StudentCounseling, Grievance
from django.contrib.auth.models import User

BRANCH_CHOICES = [
    ('', '-- Select Branch --'),
    ('CSE',   'CSE - Computer Science & Engineering'),
    ('AIDS',  'AIDS - AI & Data Science'),
    ('ECE',   'ECE - Electronics & Communication'),
    ('EEE',   'EEE - Electrical & Electronics'),
    ('MECH',  'MECH - Mechanical Engineering'),
    ('CIVIL', 'CIVIL - Civil Engineering'),
    ('IT',    'IT - Information Technology'),
    ('CHEM',  'CHEM - Chemical Engineering'),
]

SECTION_CHOICES = [('', '-- Select Section --')] + [(s, s) for s in 'ABCDEFGHIJ']

YEAR_SEM_CHOICES = [
    ('', '-- Select Year-Semester --'),
    ('1-1', '1-1  (1st Year, 1st Sem)'),
    ('1-2', '1-2  (1st Year, 2nd Sem)'),
    ('2-1', '2-1  (2nd Year, 1st Sem)'),
    ('2-2', '2-2  (2nd Year, 2nd Sem)'),
    ('3-1', '3-1  (3rd Year, 1st Sem)'),
    ('3-2', '3-2  (3rd Year, 2nd Sem)'),
    ('4-1', '4-1  (4th Year, 1st Sem)'),
    ('4-2', '4-2  (4th Year, 2nd Sem)'),
]

import datetime
_cur = datetime.date.today().year
ACADEMIC_YEAR_CHOICES = [('', '-- Select Academic Year --')] + [
    (f'{y}-{y+1}', f'{y}-{y+1}') for y in range(_cur - 2, _cur + 3)
]


class StudentCounselingForm(forms.ModelForm):
    branch       = forms.ChoiceField(choices=BRANCH_CHOICES, required=False)
    section      = forms.ChoiceField(choices=SECTION_CHOICES, required=False)
    year_sem     = forms.ChoiceField(choices=YEAR_SEM_CHOICES, required=False)
    academic_year = forms.ChoiceField(choices=ACADEMIC_YEAR_CHOICES, required=False)

    class Meta:
        model = StudentCounseling
        exclude = [
            'student_year',
            'approval_status', 'counselor_approval', 'hod_approval',
            'incharge_approval', 'director_approval',
            'added_by_role', 'last_submission_date'
        ]
        widgets = {
            'counseling_date1': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date2': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date3': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date4': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date5': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@nbkrist.org') and email != 'manojnarala245@gmail.com':
            raise forms.ValidationError("Email must belong to @nbkrist.org domain")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Roll Number already registered")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class GrievanceForm(forms.ModelForm):
    class Meta:
        model = Grievance
        fields = ['grievance_type', 'incident_date', 'description', 'attachment']
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date', 'id': 'grievance_date'}),
            'description': forms.Textarea(attrs={'placeholder': 'Please provide a clear and detailed description of your grievance.', 'id': 'grievance_message'}),
            'grievance_type': forms.Select(attrs={'id': 'grievance_type'}),
        }
        labels = {
            'grievance_type': 'Grievance Type*',
            'incident_date': 'Date of Incident / Submission*',
            'description': 'Detailed Grievance Message*',
        }
