from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .forms import PatientRegistrationForm, DoctorRegistrationForm, PhoneLoginForm


def patient_register_view(request):
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('doctor_dashboard')
        return redirect('home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to DocPulse, {user.full_name or user.phone_number}! Your account is ready.")
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/patient_register.html', {
        'form': form,
        'next_url': next_url,
    })


def patient_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('doctor_dashboard')
        return redirect('home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = PhoneLoginForm(request.POST)
        if form.is_valid():
            user = form.authenticate_user()
            if user is not None:
                if user.is_doctor:
                    login(request, user)
                    messages.info(request, "Welcome back, Doctor. Redirected to your clinic workspace.")
                    return redirect('doctor_dashboard')
                login(request, user)
                messages.success(request, "Logged in successfully.")
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, "Invalid phone number or password. Please verify and try again.")
        else:
            messages.error(request, "Please provide a valid phone number and password.")
    else:
        form = PhoneLoginForm()

    return render(request, 'accounts/patient_login.html', {
        'form': form,
        'next_url': next_url,
    })


def doctor_register_view(request):
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('doctor_dashboard')
        return redirect('home')

    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            user, profile = form.save()
            login(request, user)
            messages.success(
                request,
                f"Congratulations {profile.full_name}! Your clinic profile has been onboarded and published to DocPulse."
            )
            return redirect('doctor_dashboard')
        else:
            messages.error(request, "Registration could not be completed. Please correct the highlighted errors.")
    else:
        form = DoctorRegistrationForm()

    return render(request, 'accounts/doctor_register.html', {
        'form': form,
    })


def doctor_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_doctor:
            return redirect('doctor_dashboard')
        return redirect('home')

    if request.method == 'POST':
        form = PhoneLoginForm(request.POST)
        if form.is_valid():
            user = form.authenticate_user()
            if user is not None:
                if not user.is_doctor:
                    login(request, user)
                    messages.info(request, "You are logged in as a patient.")
                    return redirect('home')
                login(request, user)
                messages.success(request, f"Welcome back, Dr. {user.full_name or user.phone_number}!")
                return redirect('doctor_dashboard')
            else:
                messages.error(request, "Invalid doctor phone number or password.")
        else:
            messages.error(request, "Please enter valid phone and password credentials.")
    else:
        form = PhoneLoginForm()

    return render(request, 'accounts/doctor_login.html', {
        'form': form,
    })


def logout_view(request):
    """Supports both GET and POST to ensure zero HTTP 405 errors on logout."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out safely.")
    return redirect('home')
