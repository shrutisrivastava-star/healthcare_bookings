from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Users, Hospitals, Beds, Bookings, Vaccines, AuditLogs
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, datetime
import os
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

from models import db, Users, Hospitals, Beds, Bookings, Vaccines, AuditLogs


load_dotenv()  # load environment variables from .env

# ------------------ Flask Setup ------------------
app = Flask(__name__)
db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASS')
db_host = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all()

# ------------------ Helpers ------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_logged_in_user():
    if 'user_id' in session:
        return Users.query.get(session['user_id'])
    return None

def log_audit(user_id, table_name, record_id=None, action=None, details=None):
    """Create an audit log entry."""
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
    return "Hospital Booking Backend Running!"

# ---------- Register ----------
@app.route('/register', methods=['GET','POST'])
def register():
    hospitals = Hospitals.query.all()
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')  # patient/staff
        hospital_id = request.form.get('hospital_id') if role.lower() == 'staff' else None
        gender = request.form.get('gender')
        dob = request.form.get('dob')

        if Users.query.filter_by(Email=email).first():
            flash("Email already registered. Please login.")
            return redirect(url_for('login'))

        user = Users(
            Full_Name=full_name,
            Email=email,
            Phone=phone,
            Password=generate_password_hash(password),
            Role=role.lower(),
            Hospital_ID=hospital_id,
            Gender=gender,
            DOB=dob
        )
        db.session.add(user)
        db.session.commit()
        flash(f"{role.capitalize()} registered successfully!")
        return redirect(url_for('login'))

    return render_template('register.html', hospitals=hospitals)

# ---------- Login ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(Email=email).first()
        if user and check_password_hash(user.Password, password):
            session['user_id'] = user.User_ID
            session['role'] = user.Role
            flash("Login successful!", True)
            if user.Role == 'staff':
                return redirect(url_for('staff_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "error")
    return render_template('login.html')

# ---------- Logout ----------
@app.route('/logout')
def logout():
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
@app.route('/book_bed', methods=['GET','POST'])
@login_required
def book_bed_select():
    if request.method == 'POST':
        session['bed_type'] = request.form.get('bed_type')
        return redirect(url_for('available_beds'))
    bed_types = [b[0] for b in db.session.query(Beds.Bed_Type).distinct().all()]
    return render_template('book_bed.html', bed_types=bed_types)

@app.route('/available_beds')
@login_required
def available_beds():
    bed_type = session.get('bed_type')
    if not bed_type:
        flash("Select a bed type first")
        return redirect(url_for('book_bed_select'))
    beds = db.session.query(Beds, Hospitals).join(Hospitals)\
        .filter(Beds.Bed_Type==bed_type, Beds.Status=='available').all()
    return render_template('available_beds.html', beds=beds, bed_type=bed_type)

@app.route('/book_bed/<int:bed_id>/confirm', methods=['POST'])
@login_required
def confirm_bed_booking_route(bed_id):
    bed = Beds.query.get_or_404(bed_id)
    user = get_logged_in_user()
    booking = Bookings(
        User_ID=user.User_ID,
        Bed_ID=bed.Bed_ID,
        Booking_Type='bed',
        Booking_date=date.today(),
        appointment_date=date.today(),
        Status='confirmed'
    )
    db.session.add(booking)
    bed.Status = 'booked'
    db.session.commit()
    log_audit(user.User_ID, "bookings", booking.Booking_ID, "created", f"Bed {bed.Bed_ID} booked")
    flash("Bed booked successfully and logged!")
    return redirect(url_for('my_bookings'))

# ---------- Vaccine Booking ----------

@app.route('/book_vaccine', methods=['GET', 'POST'])
@login_required
def book_vaccine_select():
    if request.method == 'POST':
        session['vaccine_name'] = request.form.get('vaccine_name')
        return redirect(url_for('available_vaccines'))

    # Get distinct vaccine names
    vaccines = [v.Vaccine_Name for v in Vaccines.query.distinct(Vaccines.Vaccine_Name).all()]
    return render_template('book_vaccine.html', vaccines=vaccines)

@app.route('/available_vaccines')
@login_required
def available_vaccines():
    vaccine_name = session.get('vaccine_name')
    if not vaccine_name:
        flash("Select a vaccine first")
        return redirect(url_for('book_vaccine_select'))

    # Fetch all hospitals that have this vaccine available
    hospitals = Hospitals.query.join(Vaccines)\
        .filter(Vaccines.Vaccine_Name == vaccine_name, Vaccines.Available > 0)\
        .all()

    # Attach slots to each hospital
    for hospital in hospitals:
        hospital.vaccine_slots = Vaccines.query.filter_by(
            Hospital_ID=hospital.Hospital_ID, Vaccine_Name=vaccine_name
        ).filter(Vaccines.Available > 0).all()

    return render_template('available_vaccines.html', hospitals=hospitals, vaccine_name=vaccine_name)

    # ------------------------------------------------------------
    # Vaccine Booking Confirmation and Payment Flow
    # ------------------------------------------------------------


@app.route('/book_vaccine/<int:slot_id>/confirm', methods=['GET'])
@login_required
def confirm_vaccine_booking_route(slot_id):
    slot = Vaccines.query.get(slot_id)
    if not slot:
        flash("Vaccine slot not found.")
        return redirect(url_for('available_vaccines'))

    return render_template('confirm_vaccine_booking.html', slot=slot)



@app.route('/book_vaccine/<int:slot_id>/pay', methods=['POST'])
@login_required
def process_vaccine_payment_route(slot_id):
    slot = Vaccines.query.get(slot_id)
    user = get_logged_in_user()

    if not slot:
        flash("Slot not found.")
        return redirect(url_for('available_vaccines'))

    # Create booking
    booking = Bookings(
        User_ID=user.User_ID,
        Vaccine_ID=slot.Slot_ID,
        Booking_Type='Vaccine',
        Booking_date=date.today(),
        appointment_date=slot.Slot_Date,
        Status='Confirmed'
    )
    db.session.add(booking)

    # Decrease available count
    if slot.Available > 0:
        slot.Available -= 1

    db.session.commit()

    flash("Booking confirmed successfully!")
    return redirect(url_for('my_bookings'))


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
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

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

#---------------Staff Bookings---------
@app.route('/staff/update_bookings/<int:booking_id>', methods=['GET', 'POST'], endpoint='update_bookings')
@login_required
def update_bookings(booking_id):
    user = get_logged_in_user()
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    booking = Bookings.query.get(booking_id)
    if not booking:
        flash("Booking not found.")
        return redirect(url_for('staff_bookings'))

    if request.method == 'POST':
        booking.Status = request.form['status']
        db.session.commit()
        flash("Booking updated successfully!")
        return redirect(url_for('staff_bookings'))

    return render_template('staff/update_bookings.html', booking=booking, user=user)

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
    user = get_logged_in_user()  # assuming you have a helper function
    if user.Role != 'staff':
        flash("Access denied.")
        return redirect(url_for('dashboard'))

    # Get the hospital for this staff
    hospital = Hospitals.query.get(user.Hospital_ID)

    # Load all bookings with their bed/vaccine relationships
    bookings = Bookings.query.options(
        joinedload(Bookings.bed),
        joinedload(Bookings.vaccine),
        joinedload(Bookings.user)  # if you have a relationship to Users
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
            "User_Name": b.user.Full_Name,  # make sure you have a relationship in Booking: user = db.relationship("Users")
            "Item_Name": b.bed.Bed_Type if b.bed else (b.vaccine.Vaccine_Name if b.vaccine else "N/A"),
            "Status": b.Status,
            "Appointment_date": b.appointment_date
        })

    return render_template('staff/bookings.html', bookings=booking_details)

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
