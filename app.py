from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Users, Hospitals, Beds, Bookings, Vaccines
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()  # this will load environment variables from .env


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
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

# ------------------ Routes ------------------
@app.route('/')
def home():
    return "Hospital Booking Backend Running!"

# ---------- Register ----------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed = generate_password_hash(password)
        user = Users(Full_Name=full_name, Email=email, Password=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully!")
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------- Login ----------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(Email=email).first()
        if user and check_password_hash(user.Password, password):
            session['user_id'] = user.User_ID
            flash("Login successful!")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials!")
    return render_template('login.html')

# ---------- Dashboard ----------
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_logged_in_user()
    return render_template('patient_dashboard.html', user=user)

# ---------- My Bookings ----------
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

# ------------------ Bed Booking ------------------
@app.route('/book_bed', methods=['GET','POST'])

def book_bed():
    if request.method == 'POST':
        session['bed_type'] = request.form.get('bed_type')
        return redirect(url_for('available_beds'))
    bed_types = db.session.query(Beds.Bed_Type).distinct().all()
    bed_types = [b[0] for b in bed_types]
    return render_template('book_bed.html', bed_types=bed_types)


@app.route('/available_beds')
@login_required
def available_beds():
    bed_type = session.get('bed_type')
    if not bed_type:
        flash("Select a bed type first")
        return redirect(url_for('book_bed'))
    beds = db.session.query(Beds, Hospitals).join(Hospitals).filter(Beds.Bed_Type==bed_type, Beds.Status=='available').all()
    return render_template('available_beds.html', beds=beds, bed_type=bed_type)

@app.route('/book_bed/<int:bed_id>/confirm', methods=['GET','POST'])
@login_required
def confirm_bed_booking(bed_id):
    bed = Beds.query.get_or_404(bed_id)
    user = get_logged_in_user()
    if request.method == 'POST':
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
        flash("Bed booked successfully!")
        return redirect(url_for('my_bookings'))
    return render_template('confirm_bed_booking.html', bed=bed, user=user)

# ------------------ Vaccine Booking ------------------
@app.route('/book_vaccine', methods=['GET','POST'])
@login_required
def book_vaccine():
    if request.method=='POST':
        session['vaccine_name'] = request.form.get('vaccine_name')
        return redirect(url_for('available_vaccines'))
    vaccines = [v.Vaccine_Name for v in Vaccines.query.distinct(Vaccines.Vaccine_Name).all()]
    return render_template('book_vaccine.html', vaccines=vaccines)

# ------------------ Hospital Vaccine Slots ------------------
@app.route('/hospital/<int:hospital_id>/vaccine_slots')
@login_required
def hospital_vaccine_slots(hospital_id):
    vaccine_name = session.get('vaccine_name')
    slots = Vaccines.query.filter_by(Hospital_ID=hospital_id, Vaccine_Name=vaccine_name).filter(Vaccines.Available>0).all()
    hospital = Hospitals.query.get(hospital_id)
    return render_template('hospital_vaccines.html', hospital=hospital, slots=slots)


@app.route('/available_vaccines')
@login_required
def available_vaccines():
    vaccine_name = session.get('vaccine_name')
    if not vaccine_name:
        flash("Select a vaccine first")
        return redirect(url_for('book_vaccine'))
    hospitals = db.session.query(Hospitals, Vaccines).join(Vaccines).filter(Vaccines.Vaccine_Name==vaccine_name, Vaccines.Available>0).all()
    return render_template('available_vaccines.html', hospitals=hospitals, vaccine_name=vaccine_name)

@app.route('/book_vaccine/<int:slot_id>/confirm', methods=['GET','POST'])
@login_required
def confirm_vaccine_booking(slot_id):
    slot = Vaccines.query.get_or_404(slot_id)
    user = get_logged_in_user()
    if request.method=='POST':
        booking = Bookings(
            User_ID=user.User_ID,
            Vaccine_ID=slot.Slot_ID,
            Booking_Type='vaccine',
            Booking_date=date.today(),
            appointment_date=slot.Slot_Date,
            Status='confirmed'
        )
        db.session.add(booking)
        slot.Available -= 1
        db.session.commit()
        flash("Vaccine booked successfully!")
        return redirect(url_for('my_bookings'))
    return render_template('confirm_vaccine_booking.html', slot=slot, user=user)

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out!")
    return redirect(url_for('login'))

# ------------------ Run ------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
