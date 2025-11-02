from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Users, Hospitals, Beds, Bookings, Vaccines, AuditLogs, Payments
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, datetime
import os
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload
from flask_login import current_user,login_required,login_user, logout_user, LoginManager

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'firstapp')  # session secret

db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASS')
db_host = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all()

from flask_login import LoginManager

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# ------------------ Helpers ------------------
def get_logged_in_user():
    if 'user_id' in session:
        return Users.query.get(session['user_id'])
    return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def log_audit(user_id, table_name, record_id=None, action=None, details=None):
    log = AuditLogs(
        User_ID=user_id,
        Table_Name=table_name,
        Record_ID=record_id,
        Details=f"{action.upper()}: {details}" if details else action.upper(),
        Timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()


# ------------------ Routes ------------------
@app.route('/')
def home():
    return render_template('home.html')  # your homepage with login/signup buttons


# ---------- Register ----------

@app.route('/register', methods=['GET', 'POST'])
def register():
    hospitals = Hospitals.query.all()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        role = request.form.get('role')
        hospital_id = request.form.get('hospital_id') if role == 'staff' else None

        # New address fields
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        pincode = request.form.get('pincode')

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create new user record
        new_user = Users(
            Full_Name=full_name,
            Email=email,
            Password=hashed_password,
            Phone=phone,
            Gender=gender,
            DOB=dob,
            Role=role,
            Hospital_ID=hospital_id,
            Street_Address=street_address,
            City=city,
            State=state,
            Pincode=pincode
        )

        # Add to DB and commit
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    # GET request or failed POST renders registration page
    return render_template('register.html', hospitals=hospitals)


# ---------- Login ----------
from flask_login import login_user, logout_user

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(Email=email).first()
        if user and check_password_hash(user.Password, password):
            # Mark user as logged in for Flask-Login
            login_user(user)

            # Optionally keep your session values if you use them elsewhere
            session['user_id'] = user.User_ID
            session['role'] = user.Role


            flash("Login successful!", "success")

            flash("Login successful!", True)

            if user.Role == 'staff':
                return redirect(url_for('staff_dashboard'))
            return redirect(url_for('dashboard'))
        else:

            flash("Invalid credentials!", "danger")

            flash("Invalid credentials!", "error")

    return render_template('login.html')


# ---------- Logout ----------
@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash("Logged out!")
    return redirect(url_for('login'))


# ---------- Patient Dashboard ----------
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_logged_in_user()
    return render_template('patient_dashboard.html', user=user)

@app.route('/my_bookings')
@login_required
def my_bookings():
    user = get_logged_in_user()
    bookings = Bookings.query.filter_by(User_ID=user.User_ID).all()
    booking_details = []
    for booking in bookings:
        if booking.Booking_Type.lower() == "bed" and booking.Bed_ID:
            bed = Beds.query.get(booking.Bed_ID)
            hospital = Hospitals.query.get(bed.Hospital_ID) if bed else None
            type_name = "Bed"
        elif booking.Booking_Type.lower() == "vaccine" and booking.Vaccine_ID:
            vaccine_slot = Vaccines.query.get(booking.Vaccine_ID)
            hospital = Hospitals.query.get(vaccine_slot.Hospital_ID) if vaccine_slot else None
            type_name = "Vaccine"
        else:
            hospital = None
            type_name = booking.Booking_Type
        booking_details.append({
            "Booking_ID": booking.Booking_ID,
            "Type": type_name,
            "Hospital_Name": hospital.Name if hospital else "N/A",
            "Status": booking.Status if booking.Status else "Pending",
            "Appointment_date": booking.appointment_date.strftime('%Y-%m-%d') if booking.appointment_date else "N/A"
        })
    return render_template('my_bookings.html', bookings=booking_details, user=user)

# ---------- Bed Booking ----------
# Step 1: Select Bed Type and Date
@app.route('/book_bed', methods=['GET', 'POST'])
@login_required
def book_bed_select():
    user = get_logged_in_user()
    bed_types = [b[0] for b in db.session.query(Beds.Bed_Type).distinct().all()]

    if request.method == 'POST':
        session['bed_type'] = request.form.get('bed_type')
        session['selected_date'] = request.form.get('date')
        try:
            selected_date = datetime.strptime(session['selected_date'], "%Y-%m-%d").date()
            if selected_date < date.today():
                flash("⚠️ Please select a valid (future) date — past dates are not allowed.", "warning")
                return redirect(url_for('book_bed_select'))
        except Exception as e:
            flash("Invalid date format. Please select a valid date.", "danger")
            return redirect(url_for('book_bed_select'))
        return redirect(url_for('available_beds'))

    hospitals = Hospitals.query.filter_by(City=user.City).all()
    return render_template('book_bed.html', bed_types=bed_types, hospitals=hospitals)




# Step 2: Show Available Beds (filtered by user's city)
@app.route('/available_beds')
@login_required
def available_beds():
    user = get_logged_in_user()
    bed_type = session.get('bed_type')
    selected_date = session.get('selected_date')

    if not user:
        flash("User not found. Please log in again.")
        return redirect(url_for('login'))

    if not user.City:
        flash("Please update your profile with your city to see available beds.")
        return redirect(url_for('dashboard'))

    if not bed_type:
        flash("Select a bed type first")
        return redirect(url_for('book_bed_select'))

    beds = (
        db.session.query(Beds, Hospitals)
        .join(Hospitals)
        .filter(
            db.func.lower(Beds.Bed_Type) == bed_type.lower(),
            db.func.lower(Beds.Status) == 'available',
            db.func.lower(Hospitals.City) == user.City.lower()
        )
        .all()
    )

    return render_template(
        'available_beds.html',
        beds=beds,
        bed_type=bed_type,
        selected_date=selected_date
    )








# Step 3: Confirm Bed Booking Page (GET)
@app.route('/book_bed/<int:bed_id>/confirm', methods=['GET'])
@login_required
def confirm_bed_booking(bed_id):
    bed = Beds.query.get_or_404(bed_id)
    hospital = Hospitals.query.get(bed.Hospital_ID)
    user = get_logged_in_user()
    return render_template('confirm_bed_booking.html', bed=bed, hospital=hospital, user=user)


# Step 4: Confirm & Save Booking (POST)
@app.route('/book_bed/<int:bed_id>/confirm', methods=['POST'])
@login_required
def confirm_bed_booking_route(bed_id):
    bed = Beds.query.get_or_404(bed_id)
    user = get_logged_in_user()

    # Create a booking but **do not mark it paid yet**
    booking = Bookings(
        User_ID=user.User_ID,
        Bed_ID=bed.Bed_ID,
        Booking_Type='bed',
        Booking_date=date.today(),
        appointment_date=date.today(),
        Status='pending'  # pending until payment
    )
    db.session.add(booking)
    db.session.commit()

    # Store booking ID in session to pass to payment page
    session['current_booking_id'] = booking.Booking_ID
    session['amount'] = 5000  # or fetch from bed type / pricing table

    return redirect(url_for('payment_page'))


# ---------- Vaccine Booking ----------
@app.route('/book_vaccine', methods=['GET', 'POST'])
def book_vaccine():
    if request.method == 'POST':
        vaccine_name = request.form.get('vaccine_name')
        slot_date_str = request.form.get('slot_date')

        from datetime import datetime
        slot_date = datetime.strptime(slot_date_str, '%Y-%m-%d').date()

        # Find vaccines where:
        # 1️⃣ Vaccine name matches (case-insensitive)
        # 2️⃣ Slot date is BEFORE OR EQUAL TO selected date
        # 3️⃣ Available > 0
        vaccines = Vaccines.query.filter(
            db.func.lower(Vaccines.Vaccine_Name) == vaccine_name.lower(),
            Vaccines.Slot_Date <= slot_date,
            Vaccines.Available > 0
        ).all()

        if not vaccines:
            flash(f"No available slots found for {vaccine_name} before or on {slot_date}.")
            return render_template('available_vaccine.html', vaccines=[])

        # ✅ Show available slots (with hospital details)
        return render_template('available_vaccine.html', vaccines=vaccines)

    # GET request — show vaccine name dropdown
    vaccine_names = [v.Vaccine_Name.capitalize() for v in Vaccines.query.all()]
    return render_template(
        'book_vaccine.html',
        vaccine_names=sorted(set(vaccine_names), key=str.lower)
    )





from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user


@app.route('/available_vaccines', methods=['GET', 'POST'])
@login_required
def available_vaccines():
    from datetime import datetime, date

    vaccine_name = request.form.get('vaccine_name')
    slot_date_str = request.form.get('slot_date')

    print("\n🧠 --- DEBUG: Vaccine Availability Check ---")
    print("Raw form data:", vaccine_name, slot_date_str)

    # 🧩 Parse date safely
    try:
        if "-" in slot_date_str and len(slot_date_str.split("-")[0]) == 4:
            slot_date = datetime.strptime(slot_date_str, "%Y-%m-%d").date()
        else:
            slot_date = datetime.strptime(slot_date_str, "%d-%m-%Y").date()
    except Exception as e:
        flash("❌ Invalid date format. Please use YYYY-MM-DD or DD-MM-YYYY.", "danger")
        print("❌ Date parsing failed:", e)
        return redirect(url_for('book_vaccine'))

    print("✅ Parsed slot_date:", slot_date)
    session['selected_date'] = slot_date.strftime("%Y-%m-%d")

    # 🚫 If date is in the past
    if slot_date < date.today():
        flash("⚠️ Please enter a valid (future) date — past dates are not allowed.", "warning")
        return redirect(url_for('book_vaccine'))

    # 👤 Get user city
    user = get_logged_in_user()
    user_city = user.City.strip().lower() if user.City else None
    print(f"🏙️ Filtering by user city: {user_city}")

    # 🧠 Debug: show all vaccines
    all_vaccines = db.session.query(Vaccines).join(Hospitals, Vaccines.Hospital_ID == Hospitals.Hospital_ID).all()
    print("\n📋 DEBUG: Showing all vaccines in DB for reference:")
    for v in all_vaccines:
        print(f"   -> ID:{v.Slot_ID}, Name:{v.Vaccine_Name}, Date:{v.Slot_Date}, City:{v.hospital.City}, Avail:{v.Available}")

    # ✅ Query: same city, same vaccine, available > 0
    vaccines = (
        db.session.query(Vaccines)
        .join(Hospitals, Vaccines.Hospital_ID == Hospitals.Hospital_ID)
        .filter(
            db.func.lower(Vaccines.Vaccine_Name) == vaccine_name.lower(),
            db.func.lower(Hospitals.City) == user_city,
            Vaccines.Available > 0
        )
        .all()
    )

    print(f"\n🔍 Querying for vaccine='{vaccine_name.lower()}', city={user_city}, future date OK")
    print(f"✅ Query result count: {len(vaccines)}")

    if not vaccines:
        flash(f"No available slots for {vaccine_name} in your city ({user_city.title()}).", "info")
        return render_template(
            'available_vaccines.html',
            vaccines=[],
            message=f"No available slots for {vaccine_name} in your city ({user_city.title()})."
        )

    # ✅ Show results
    return render_template('available_vaccines.html', vaccines=vaccines)






@app.route('/confirm_vaccine/<int:slot_id>')
@login_required
def confirm_vaccine(slot_id):
    slot = Vaccines.query.get(slot_id)
    if not slot:
        flash("Invalid vaccine slot selected.", "danger")
        return redirect(url_for('available_vaccines'))

    hospital = Hospitals.query.get(slot.Hospital_ID)

    # ✅ Use selected date from session, fallback to slot date if missing
    selected_date_str = session.get('selected_date')
    if selected_date_str:
        appointment_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    else:
        appointment_date = slot.Slot_Date

    return render_template(
        'confirm_vaccine_booking.html',
        slot=slot,
        hospital=hospital,
        appointment_date=appointment_date  # ✅ send to template
    )


@app.route('/book_vaccine_final/<int:slot_id>', methods=['POST'])
@login_required
def book_vaccine_final(slot_id):
    print(f"🧠 --- DEBUG: Booking Vaccine Slot --- for Slot ID: {slot_id}")

    vaccine_slot = Vaccines.query.get(slot_id)
    user = get_logged_in_user()

    if not vaccine_slot or vaccine_slot.Available <= 0:
        flash("Selected slot is no longer available.", "danger")
        return redirect(url_for('available_vaccines'))

    # ✅ Get appointment date selected by user from session (NOT slot date)
    selected_date_str = session.get('selected_date')
    if selected_date_str:
        try:
            appointment_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            appointment_date = vaccine_slot.Slot_Date
    else:
        appointment_date = vaccine_slot.Slot_Date

    try:
        # 🔻 Reduce available slot count
        vaccine_slot.Available -= 1
        db.session.add(vaccine_slot)

        # ✅ Create booking record
        booking = Bookings(
            User_ID=user.User_ID,
            Vaccine_ID=vaccine_slot.Slot_ID,
            Booking_Type='vaccine',
            Booking_date=date.today(),
            appointment_date=appointment_date,
            Status='pending'
        )

        db.session.add(booking)
        db.session.commit()

        # 💾 Save for payment page
        session['current_booking_id'] = booking.Booking_ID
        session['amount'] = 500  # Example cost

        print(f"✅ Booking saved: ID={booking.Booking_ID}, Date={appointment_date}, Avail now={vaccine_slot.Available}")

        # ✅ Redirect to payment page
        flash("Booking confirmed! Proceed to payment.", "success")
        return redirect(url_for('payment_page'))

    except Exception as e:
        db.session.rollback()
        print(f"❌ DB Error: {e}")
        flash("Something went wrong while booking. Please try again.", "danger")
        return redirect(url_for('available_vaccines'))



# ------------------ Payments Route ------------------
@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment_page():
    user = get_logged_in_user()
    booking_id = session.get('current_booking_id')
    amount = session.get('amount')

    if not booking_id or not amount:
        flash("No booking selected for payment.")
        return redirect(url_for('dashboard'))

    booking = Bookings.query.get_or_404(booking_id)

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')

        # Save payment
        payment = Payments(
            User_ID=user.User_ID,
            Booking_ID=booking.Booking_ID,
            Booking_Type=booking.Booking_Type,
            Amount=amount,
            Payment_Method=payment_method,
            Payment_Status='Paid',
            Payment_Date=datetime.now()
        )
        db.session.add(payment)

        # Update booking
        booking.Status = 'confirmed'
        db.session.commit()

        session.pop('current_booking_id', None)
        session.pop('amount', None)

        flash("Payment successful! Booking confirmed.")
        return redirect(url_for('my_bookings'))

    return render_template('payments.html', booking=booking, user=user, amount=amount)




# ---------- Cancel Booking ----------
@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking_route(booking_id):
    booking = Bookings.query.get_or_404(booking_id)
    booking.Status = "Cancelled"
    db.session.commit()
    log_audit(get_logged_in_user().User_ID, "bookings", booking.Booking_ID, "cancelled", f"Booking cancelled")
    flash("Booking cancelled and logged!")
    return redirect(url_for('my_bookings'))

# ------------------ STAFF ROUTES ------------------
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime, date
from models import db, Users, Hospitals, Beds, Vaccines, Bookings, AuditLogs

# ------------------ Helpers ------------------


def get_logged_in_user():
    if 'user_id' in session:
        return Users.query.get(session['user_id'])
    return None

# ------------------ Audit Logging ------------------
def log_audit(user_id, table_name, record_id=None, action=None, details=None):
    log = AuditLogs(
        User_ID=user_id,
        Table_Name=table_name,
        Record_ID=record_id,
        Details=f"{action.upper()}: {details}" if details else action.upper(),
        Timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()

# ---------- Staff Dashboard ----------
@app.route('/staff/dashboard', endpoint='staff_dashboard')
@login_required
def staff_dashboard():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied")
        return redirect(url_for('dashboard'))

    hospital = Hospitals.query.get(user.Hospital_ID)
    beds_count = Beds.query.filter_by(Hospital_ID=hospital.Hospital_ID).count()
    vaccines_count = Vaccines.query.filter_by(Hospital_ID=hospital.Hospital_ID).count()
    bookings_count = Bookings.query.join(Beds, isouter=True).join(Vaccines, isouter=True)\
        .filter((Beds.Hospital_ID==hospital.Hospital_ID) | (Vaccines.Hospital_ID==hospital.Hospital_ID)).count()

    return render_template('staff/dashboard.html',
                           user=user,
                           hospital=hospital,
                           beds_count=beds_count,
                           vaccines_count=vaccines_count,
                           bookings_count=bookings_count)



# ---------- Manage Beds ----------
@app.route('/staff/beds', endpoint='manage_beds')
@login_required
def manage_beds():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    beds = Beds.query.filter_by(Hospital_ID=user.Hospital_ID).all()
    return render_template('staff/manage_beds.html', beds=beds, user=user)


@app.route('/staff/beds/new', endpoint='new_bed', methods=['GET', 'POST'])
@login_required
def new_bed():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        bed_type = request.form.get('bed_type')
        status = request.form.get('status')
        bed = Beds(Hospital_ID=user.Hospital_ID, Bed_Type=bed_type, Status=status)
        db.session.add(bed)
        db.session.commit()
        log_audit(user.User_ID, 'beds', bed.Bed_ID, 'created', f'Added bed type {bed_type} with status {status}')
        flash("Bed added successfully!")
        return redirect(url_for('manage_beds'))

    return render_template('staff/new_bed.html', user=user)


@app.route('/staff/beds/<int:bed_id>/edit', endpoint='edit_bed', methods=['GET', 'POST'])
@login_required
def edit_bed(bed_id):
    bed = Beds.query.get_or_404(bed_id)
    user = get_logged_in_user()
    if user.Role != 'staff' or bed.Hospital_ID != user.Hospital_ID:
        flash("Access denied.")
        return redirect(url_for('manage_beds'))

    if request.method == 'POST':
        old_type, old_status = bed.Bed_Type, bed.Status
        bed.Bed_Type = request.form.get('bed_type')
        bed.Status = request.form.get('status')
        db.session.commit()
        log_audit(user.User_ID, 'beds', bed.Bed_ID, 'updated', f'Type {old_type}->{bed.Bed_Type}, Status {old_status}->{bed.Status}')
        flash("Bed updated successfully!")
        return redirect(url_for('manage_beds'))

    return render_template('staff/edit_bed.html', bed=bed, user=user)


@app.route('/staff/beds/<int:bed_id>/delete', endpoint='delete_bed', methods=['POST'])
@login_required
def delete_bed(bed_id):
    bed = Beds.query.get_or_404(bed_id)
    user = get_logged_in_user()
    if user.Role != 'staff' or bed.Hospital_ID != user.Hospital_ID:
        flash("Access denied.")
        return redirect(url_for('manage_beds'))

    if bed.Status == 'booked':
        flash("Cannot delete booked beds.", "error")
        return redirect(url_for('manage_beds'))

    db.session.delete(bed)
    db.session.commit()
    log_audit(user.User_ID, 'beds', bed.Bed_ID, 'deleted', f'Deleted bed type {bed.Bed_Type}')
    flash("Bed deleted successfully!")
    return redirect(url_for('manage_beds'))


# ---------- Manage Vaccines ----------
@app.route('/staff/vaccines', endpoint='manage_vaccines')
@login_required
def manage_vaccines():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    vaccines = Vaccines.query.filter_by(Hospital_ID=user.Hospital_ID).all()
    return render_template('staff/manage_vaccines.html', vaccines=vaccines, user=user)


@app.route('/staff/vaccines/new', endpoint='new_vaccine', methods=['GET', 'POST'])
@login_required
def new_vaccine():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('vaccine_name')
        date_slot = request.form.get('slot_date')
        time_slot = request.form.get('slot_time')
        capacity = int(request.form.get('capacity'))
        vaccine = Vaccines(Hospital_ID=user.Hospital_ID,
                           Vaccine_Name=name,
                           Slot_Date=date_slot,
                           Slot_Time=time_slot,
                           Capacity=capacity,
                           Available=capacity)
        db.session.add(vaccine)
        db.session.commit()
        log_audit(user.User_ID, 'vaccines', vaccine.Slot_ID, 'created', f'Added {name} slot on {date_slot} at {time_slot}')
        flash("Vaccine slot added successfully!")
        return redirect(url_for('manage_vaccines'))

    return render_template('staff/new_vaccine.html', user=user)


@app.route('/staff/vaccines/<int:vaccine_id>/edit', endpoint='edit_vaccine', methods=['GET', 'POST'])
@login_required
def edit_vaccine(vaccine_id):
    vaccine = Vaccines.query.get_or_404(vaccine_id)
    user = get_logged_in_user()
    if user.Role != 'staff' or vaccine.Hospital_ID != user.Hospital_ID:
        flash("Access denied.")
        return redirect(url_for('manage_vaccines'))

    if request.method == 'POST':
        old_name, old_date, old_time = vaccine.Vaccine_Name, vaccine.Slot_Date, vaccine.Slot_Time
        vaccine.Vaccine_Name = request.form.get('vaccine_name')
        vaccine.Slot_Date = request.form.get('slot_date')
        vaccine.Slot_Time = request.form.get('slot_time')
        vaccine.Capacity = int(request.form.get('capacity'))
        vaccine.Available = int(request.form.get('available'))
        db.session.commit()
        log_audit(user.User_ID, 'vaccines', vaccine.Slot_ID, 'updated',
                  f'{old_name}({old_date} {old_time})->{vaccine.Vaccine_Name}({vaccine.Slot_Date} {vaccine.Slot_Time})')
        flash("Vaccine updated successfully!")
        return redirect(url_for('manage_vaccines'))

    return render_template('staff/edit_vaccine.html', vaccine=vaccine, user=user)


@app.route('/staff/vaccines/<int:vaccine_id>/delete', endpoint='delete_vaccine', methods=['POST'])
@login_required
def delete_vaccine(vaccine_id):
    vaccine = Vaccines.query.get_or_404(vaccine_id)
    user = get_logged_in_user()
    if user.Role != 'staff' or vaccine.Hospital_ID != user.Hospital_ID:
        flash("Access denied.")
        return redirect(url_for('manage_vaccines'))

    bookings = Bookings.query.filter_by(Vaccine_ID=vaccine_id, Status='confirmed').count()
    if bookings > 0:
        flash("Cannot delete vaccine slot with active bookings.", "error")
        return redirect(url_for('manage_vaccines'))

    db.session.delete(vaccine)
    db.session.commit()
    log_audit(user.User_ID, 'vaccines', vaccine.Slot_ID, 'deleted', f'Deleted {vaccine.Vaccine_Name} slot')
    flash("Vaccine slot deleted successfully!")
    return redirect(url_for('manage_vaccines'))


# ---------- Staff Profile ----------
@app.route('/staff/profile', endpoint='staff_profile')
@login_required
def staff_profile():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    hospital = Hospitals.query.get(user.Hospital_ID)
    return render_template('staff/profile.html', user=user, hospital=hospital)



#-------------- Delete Booking --------------
@app.route('/staff/delete_booking/<int:booking_id>', methods=['POST'], endpoint='delete_booking')
@login_required
def delete_booking(booking_id):
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    booking = Bookings.query.get(booking_id)
    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for('staff_bookings'))

    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted successfully!")
    return redirect(url_for('staff_bookings'))

#---------------Staff Bookings---------
@app.route('/staff/bookings')
@login_required
def staff_bookings():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    hospital = Hospitals.query.get(user.Hospital_ID)

    bookings = Bookings.query.options(
        joinedload(Bookings.bed),
        joinedload(Bookings.vaccine),
        joinedload(Bookings.user)
    ).all()



    
    # Filter bookings that belong to this hospital

    booking_details = []
    for b in bookings:
        # Skip bookings not belonging to this hospital
        if b.bed and b.bed.Hospital_ID != hospital.Hospital_ID:
            continue
        if b.vaccine and b.vaccine.Hospital_ID != hospital.Hospital_ID:
            continue

        booking_details.append({
            "Booking_ID": b.Booking_ID,
            "User_Name": b.user.Full_Name if b.user else "N/A",
            "Item_Name": b.bed.Bed_Type if b.bed else (b.vaccine.Vaccine_Name if b.vaccine else "N/A"),
            "Status": b.Status,
            "Appointment_date": b.appointment_date.strftime('%Y-%m-%d') if b.appointment_date else "N/A"
        })

    return render_template('staff/bookings.html', bookings=booking_details, user=user)

@app.route('/staff/update_bookings/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def update_bookings(booking_id):
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    booking = Bookings.query.get_or_404(booking_id)

    # Ensure staff can only update bookings for their hospital
    if booking.bed and booking.bed.Hospital_ID != user.Hospital_ID:
        flash("Cannot edit bookings from another hospital.", "error")
        return redirect(url_for('staff_bookings'))
    if booking.vaccine and booking.vaccine.Hospital_ID != user.Hospital_ID:
        flash("Cannot edit bookings from another hospital.", "error")
        return redirect(url_for('staff_bookings'))

    if request.method == 'POST':
        old_status = booking.Status
        # Update status
        booking.Status = request.form.get('status')
        db.session.commit()

        # Audit log
        details = f"Status: {old_status} -> {booking.Status}"
        log_audit(user.User_ID, 'bookings', booking.Booking_ID, 'updated', details)

        flash("Booking updated successfully!", "success")
        return redirect(url_for('staff_bookings'))

    # GET request
    return render_template('staff/update_bookings.html', booking=booking, user=user)

# Staff view payments
@app.route('/staff/payments')
@login_required
def staff_payments():
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    # Payments related to this staff's hospital
    payments = Payments.query.options(
        joinedload(Payments.booking).joinedload(Bookings.bed),
        joinedload(Payments.booking).joinedload(Bookings.vaccine),
        joinedload(Payments.booking).joinedload(Bookings.user)
    ).join(Bookings) \
        .outerjoin(Beds, Bookings.Bed_ID == Beds.Bed_ID) \
        .outerjoin(Vaccines, Bookings.Vaccine_ID == Vaccines.Slot_ID) \
        .filter(
        (Beds.Hospital_ID == user.Hospital_ID) |
        (Vaccines.Hospital_ID == user.Hospital_ID)
    ).all()
    

    return render_template('staff/payments.html', payments=payments, user=user)



# ---------- Forgot Password ----------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password functionality"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not email or not new_password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return render_template('forgot_password.html')
        
        # Check if passwords match
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('forgot_password.html')
        
        # Validate password strength
        if not is_strong_password(new_password):
            flash('Password must be at least 8 characters long and contain uppercase, lowercase letters and numbers', 'error')
            return render_template('forgot_password.html')
        
        try:
            # Check if email exists in database
            user = Users.query.filter_by(Email=email).first()
            
            if not user:
                flash('No account found with this email address', 'error')
                return render_template('forgot_password.html')
            
            # Update password
            hashed_password = generate_password_hash(new_password)
            user.Password = hashed_password
            
            # Commit changes to database
            db.session.commit()
            
            flash('Password reset successfully! You can now login with your new password', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error resetting password: {str(e)}")
            flash('An error occurred while resetting your password. Please try again.', 'danger')
            return render_template('forgot_password.html')
    
    # GET request - show forgot password form
    return render_template('forgot_password.html')

def is_strong_password(password):
    """Check if password meets strength requirements"""
    if len(password) < 8:
        return False
    
    # Check for uppercase, lowercase, and numbers
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_digit = any(char.isdigit() for char in password)
    
    return has_upper and has_lower and has_digit


# ------------------ Run ------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
