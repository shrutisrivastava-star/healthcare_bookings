from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class Users(db.Model):
    __tablename__ = 'users'
    User_ID = db.Column(db.Integer, primary_key=True)
    Full_Name = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Phone = db.Column(db.String(20))
    Gender = db.Column(db.String(10))
    DOB = db.Column(db.Date)
    Role = db.Column(db.String(20), default='patient')

    # Link staff users to a hospital (nullable for patients)
    Hospital_ID = db.Column(db.Integer, db.ForeignKey('hospitals.Hospital_ID'), nullable=True)
    hospital = db.relationship("Hospitals", backref="staff")


class Hospitals(db.Model):
    __tablename__ = 'hospitals'
    Hospital_ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    Street_Address = db.Column(db.String(100))
    City = db.Column(db.String(30))
    State = db.Column(db.String(30))
    Postal_Code = db.Column(db.String(20))
    Phone = db.Column(db.String(20))

class Beds(db.Model):
    __tablename__ = 'beds'
    Bed_ID = db.Column(db.Integer, primary_key=True)
    Hospital_ID = db.Column(db.Integer, db.ForeignKey('hospitals.Hospital_ID'))
    Bed_Type = db.Column(db.String(20))
    Status = db.Column(db.String(20))
    hospital = db.relationship("Hospitals", backref="beds")


class Vaccines(db.Model):
    __tablename__ = 'vaccines'
    Slot_ID = db.Column(db.Integer, primary_key=True)
    Hospital_ID = db.Column(db.Integer, db.ForeignKey('hospitals.Hospital_ID'))
    Vaccine_Name = db.Column(db.String(50))
    Slot_Date = db.Column(db.Date)
    Slot_Time = db.Column(db.Time)
    Capacity = db.Column(db.Integer)
    Available = db.Column(db.Integer)
    hospital = db.relationship("Hospitals", backref="vaccines")

class Bookings(db.Model):
    __tablename__ = 'bookings'
    Booking_ID = db.Column(db.Integer, primary_key=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('users.User_ID'))
    Bed_ID = db.Column(db.Integer, db.ForeignKey('beds.Bed_ID'), nullable=True)
    Vaccine_ID = db.Column(db.Integer, db.ForeignKey('vaccines.Slot_ID'), nullable=True)
    Booking_Type = db.Column(db.String(10))
    Booking_date = db.Column(db.Date)
    appointment_date = db.Column(db.Date)
    Status = db.Column(db.String(20))
    bed = db.relationship("Beds", backref="bookings", foreign_keys=[Bed_ID])
    vaccine = db.relationship("Vaccines", backref="bookings", foreign_keys=[Vaccine_ID])
    user = db.relationship("Users", backref="bookings", foreign_keys=[User_ID])

class Payments(db.Model):
    __tablename__ = 'payments'
    Payment_ID = db.Column(db.Integer, primary_key=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('users.User_ID'))
    Booking_ID = db.Column(db.Integer, db.ForeignKey('bookings.Booking_ID'))
    Booking_Type = db.Column(db.String(10))
    Amount = db.Column(db.Numeric(10,2))
    Payment_Method = db.Column(db.String(20))
    Payment_Status = db.Column(db.String(20))
    Payment_Date = db.Column(db.DateTime)





class AuditLogs(db.Model):
    __tablename__ = "audit_logs"  # matches your MySQL table

    Log_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('users.User_ID'), nullable=False)
    Table_Name = db.Column(db.String(30), nullable=True)
    Record_ID = db.Column(db.Integer, nullable=True)
    Details = db.Column(db.String(100), nullable=True)
    Timestamp = db.Column(db.DateTime, default=datetime.utcnow)



