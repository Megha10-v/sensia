from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import time
import stripe

app = Flask(__name__)
app.secret_key = "supersecretkey"


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:megha@localhost/timerdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


stripe.api_key = "sk_test_51QaeVFFVCHd51pKJOZfbLZ1J2MmKmZWn9k4RZHm1SsVrONd6qeafVe62RluaAhy6X155FdUDR24JvLY8f1CuQtfr00GZxKXQ5i"


class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    stripe_charge_id = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    session.clear()
    session['start_time'] = time.time()
    session['extra_time'] = 0
    return render_template('timer.html', timer_duration=60)

@app.route('/email', methods=['GET', 'POST'])
def email_form():
    if request.method == 'POST':
        email = request.form['email']
        new_email = Email(email=email)
        db.session.add(new_email)
        db.session.commit()
        session['email_id'] = new_email.id
        session['start_time'] = time.time()
        session['extra_time'] = 0 
        return redirect(url_for('email_submitted'))
    return render_template('email_form.html')

@app.route('/email_submitted')
def email_submitted():
    return render_template('timer.html', timer_duration=300)

@app.route('/payment_successful')
def payment_successful():
    return render_template('payment_success.html')

@app.route('/payment_failure')
def payment_failure():
    return render_template('payment_error.html')

@app.route('/payment_timer')
def payment_timer():
    return render_template('timer.html', timer_duration=1200)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        email_id = session.get('email_id')
        token = request.form['stripeToken']

        try:
            charge = stripe.Charge.create(
                amount=500,
                currency="usd",
                description="Extra 20 minutes payment",
                source=token,
            )

            new_payment = Payment(
                email_id=email_id,
                stripe_charge_id=charge['id'],
                amount=500
            )
            db.session.add(new_payment)
            db.session.commit()

            return redirect(url_for('payment_successful'))

        except stripe.error.StripeError as e:
            return redirect(url_for('payment_failure'))

    return render_template('payment.html')

@app.route('/check_timer/<int:timer_duration>')
def check_timer(timer_duration):
    total_duration = timer_duration + session.get('extra_time', 0)
    
    elapsed_time = time.time() - session.get('start_time', 0)

    if elapsed_time > total_duration:
        if total_duration == 120:
            return redirect(url_for('email_form'))
        elif total_duration == 300 or total_duration==1200:
            return redirect(url_for('payment'))
    remaining_time = total_duration - elapsed_time
    return render_template('timer.html', timer_duration=remaining_time)

if __name__ == '__main__':
    app.run(debug=True)

