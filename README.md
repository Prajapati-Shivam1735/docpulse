# DocPulse - Practo-Inspired Healthcare Discovery & Queue Management Platform

DocPulse is a clean, consumer-facing healthcare discovery and appointment management platform built on Django 5/6 MVC architecture. It empowers patients to search verified medical specialists, view transparent consultation fees, and receive real-time queue tokens that eliminate physical clinic waiting lines. Doctors receive a self-service onboarding workspace, slot generator, and live patient consultation desk.

---

## 🚀 Key Features

1. **Practo-Style Healthcare Discovery**:
   - Instant search by Doctor Name, Specialty, Clinic, and Qualifications.
   - Dynamic Category Pills (Cardiologist, General Physician, Dermatologist, Pediatrician, Orthopedic, Neurologist, etc.).
   - Preserves search and filter state via URL query parameters (`?dept=...&q=...`).

2. **Dual-Track Phone Authentication**:
   - Frictionless authentication using mobile phone numbers as the primary credential.
   - Separate patient onboarding and dedicated doctor self-registration (`/doctor/register/`).
   - Role-based login redirection: Doctors to `/doctor/dashboard/` and Patients to discovery/booking.
   - Zero admin clutter on public templates; hidden moderation at `/admin/`.

3. **Collision-Proof Slot Booking Engine**:
   - Atomic database transactions with `select_for_update()` to prevent race condition double-bookings.
   - Sequential daily queue token generation (`#01`, `#02`, etc.) per doctor.
   - Past date booking prevention.
   - Instant digital appointment pass/slip with print-friendly layout and queue instructions.

4. **Doctor Workspace & Queue Desk**:
   - Live roster tracking: `Pending` / `Confirmed` -> `In-Consultation` -> `Completed` / `Cancelled`.
   - Real-time revenue and daily consultation metrics.
   - Automated 30-minute consultation slot generator.
   - Practice profile settings and consultation fee updates.

5. **Patient Live Queue Tracker (`/track/`)**:
   - Real-time lookup by mobile number or booking reference (e.g. `DP-20260914-XXXX`).
   - Instant visibility into whether the doctor is currently consulting prior patients.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12/3.13, Django 5.x / 6.0
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, FontAwesome 6, Google Fonts Plus Jakarta Sans
- **Static Assets**: WhiteNoise
- **Database**: SQLite (Dev) / PostgreSQL (Production)
- **Production Server**: Gunicorn WSGI

---

## 🏃 Getting Started

### 1. Setup Environment & Install Dependencies
```bash
cd docpulse
pip install -r requirements.txt
```

### 2. Apply Database Migrations
```bash
python manage.py migrate
```

### 3. Seed Platform Data
DocPulse includes a custom management command to seed departments, verified specialists, slots, and active sample appointments:
```bash
python manage.py seed_data
```

### 4. Run Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Running Automated Tests

Run the comprehensive 24-test suite validating authentication, collision rules, token increments, and doctor queue flows:
```bash
python manage.py test accounts doctors booking.tests booking.tests_advanced --verbosity=2
```

---

## 🔑 Demo Credentials

| Role | Phone Number | Password | Access URL |
|------|--------------|----------|------------|
| **Doctor (Cardiologist)** | `9820011221` | `doctor123` | `/doctor/login/` |
| **Doctor (General Physician)** | `9820011222` | `doctor123` | `/doctor/login/` |
| **Doctor (Dermatologist)** | `9820011223` | `doctor123` | `/doctor/login/` |
| **Patient** | `9876543210` | `patient123` | `/patient/login/` |
| **Platform Administrator** | `9999999999` | `admin123` | `/admin/` |
