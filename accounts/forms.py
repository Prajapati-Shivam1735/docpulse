import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from doctors.models import Department, DoctorProfile

User = get_user_model()


def clean_phone(phone):
    if not phone:
        return ""
    # Normalize phone: keep digits and leading plus
    cleaned = re.sub(r"[^\d+]", "", phone.strip())
    if len(re.sub(r"[^\d]", "", cleaned)) < 10:
        raise forms.ValidationError("Please enter a valid phone number (at least 10 digits).")
    return cleaned


class PatientRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Create strong password"}),
        min_length=6,
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm password"}),
        min_length=6,
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ["full_name", "phone_number", "gender", "age"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter patient's full name"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 9876543210"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "age": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Age in years", "min": "1", "max": "120"}),
        }

    def clean_phone_number(self):
        phone = clean_phone(self.cleaned_data.get("phone_number"))
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("A user with this phone number already exists.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class DoctorRegistrationForm(forms.Form):
    # User Details
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Dr. Firstname Lastname"}),
        label="Doctor Full Name"
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 9876543211"}),
        label="Mobile Phone Number (Primary Login)"
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "doctor@hospital.com"}),
        label="Email Address (Optional)"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Create a strong password"}),
        min_length=6,
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm password"}),
        min_length=6,
        label="Confirm Password"
    )

    # Professional Profile Details
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label="Select Specialty / Department",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Medical Department"
    )
    qualification = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. MBBS, MD - Cardiology"}),
        label="Qualifications & Degrees"
    )
    specialization = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Interventional Cardiologist"}),
        label="Specialization Focus"
    )
    experience_years = forms.IntegerField(
        min_value=0,
        max_value=70,
        initial=5,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Years of experience"}),
        label="Experience (Years)"
    )
    consultation_fee = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        initial=500.00,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Fee in INR"}),
        label="Consultation Fee (₹)"
    )
    clinic_name = forms.CharField(
        max_length=200,
        initial="DocPulse Care Clinic",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Clinic / Hospital Name"}),
        label="Clinic / Hospital Name"
    )
    clinic_address = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Full clinic physical address"}),
        label="Clinic Address"
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Brief professional overview..."}),
        label="Professional Bio / Summary"
    )

    def clean_phone_number(self):
        phone = clean_phone(self.cleaned_data.get("phone_number"))
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("A doctor or user with this phone number already exists.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            phone_number=data["phone_number"],
            password=data["password"],
            full_name=data["full_name"],
            email=data.get("email", ""),
            role=User.Role.DOCTOR
        )
        profile = DoctorProfile.objects.create(
            user=user,
            department=data["department"],
            qualification=data["qualification"],
            specialization=data["specialization"],
            experience_years=data["experience_years"],
            consultation_fee=data["consultation_fee"],
            clinic_name=data["clinic_name"],
            clinic_address=data["clinic_address"],
            bio=data.get("bio", ""),
            is_verified=True
        )
        return user, profile


class PhoneLoginForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Registered Phone Number", "autofocus": "autofocus"}),
        label="Phone Number"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Your Password"}),
        label="Password"
    )

    def clean_phone_number(self):
        return clean_phone(self.cleaned_data.get("phone_number"))

    def authenticate_user(self):
        phone = self.cleaned_data.get("phone_number")
        password = self.cleaned_data.get("password")
        if phone and password:
            user = authenticate(username=phone, password=password)
            if not user:
                # Also check direct phone_number
                user = authenticate(phone_number=phone, password=password)
            return user
        return None
