from django import forms
from .models import StudentCounseling , Grievance
from django.contrib.auth.models import User

class StudentCounselingForm(forms.ModelForm):
    class Meta:
        model = StudentCounseling
        fields = '__all__'
        widgets = {
            'counseling_date1': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date2': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date3': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date4': forms.DateInput(attrs={'type': 'date'}),
            'counseling_date5': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self,*args,**kwargs):
        super(StudentCounselingForm,self).__init__(*args,**kwargs)
        for field in self.fields.values():
            field.required=False

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
