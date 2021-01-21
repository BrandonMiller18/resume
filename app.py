import os
import smtplib
from flask import Flask, redirect, url_for, render_template, send_file, request, session, make_response, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.secret_key = 'dev'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEBUG'] = False
app.config['MAIL_USERNAME'] = 'blmiller0809@gmail.com' # change to system variable for prod
app.config['MAIL_PASSWORD'] = 'qpwo1029!' # change to system variable for prod
app.config['MAIL_DEFAULT_SENDER'] = 'blmiller0809@gmail.com'
# app.config['MAIL_MAX_EMAILS'] = None
# app.config['MAIL_SUPPRESS_SEND'] = 
# app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3' # change to system variable
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

mail = Mail(app)
db = SQLAlchemy(app)


class references(db.Model):
	# create model (table), "references" in SQLite db using SQLAlchemy
	_id = db.Column("id", db.Integer, primary_key=True)
	fname = db.Column(db.String(100))
	lname = db.Column(db.String(100))
	title = db.Column(db.String(100))
	email = db.Column(db.String(100))
	relationship = db.Column(db.String(100))
	msg = db.Column(db.String(255))

	def __init__(self, fname, lname, title, email, relationship, msg):
		self.fname = fname
		self.lname = lname
		self.title = title
		self.email = email
		self.relationship = relationship
		self.msg = msg

db.create_all()

# create pages

@app.route("/")
def home():
	"""Gets fname from Cookie variable to greet user if we know their first name"""
	cookies = request.cookies
	fn = cookies.get('fn')

	# pass references table from db and first name cookie for use on the homepage
	return render_template("index.html", references=references.query.all(), fn=fn)

# DOWNLOAD ROUTES

@app.route("/brandon_miller_resume/")
def return_resume():
	return send_file(
		"static/20210103_Brandon_Miller_Resume.pdf", 
		as_attachment=True,
		attachment_filename="Brandon_Miller_Resume.pdf",
		)

@app.route("/pwm-download/")
def return_pwm():
	return send_file("static/pwm.zip",
		as_attachment=True,
		attachment_filename="pwm.zip",
		)

# END DOWNLOADS

@app.route("/resume")
def resume():
	return render_template("resume.html")

@app.route("/portfolio")
def portfolio():
	return render_template("portfolio.html")

@app.route("/portfolio/more-info")
def more_info():
	return render_template("moreinfo.html")

@app.route("/references", methods=["POST", "GET"])
def reference():
	"""check for POST method, get data from form and put it in database
	pass in 'references' variable to render template to display entries
	in database on the front end"""
	if request.method == "POST":
		session['ref'] = True # set session variable, used to remove form from reference page
		
		fname = request.form["fname"]
		lname = request.form["lname"]
		title = request.form["title"]
		form_email = request.form["email"]
		relationship = request.form["relationship"]
		form_msg = request.form["msg"]

		# write data to refrences database
		ref = references(fname, lname, title, form_email, relationship, form_msg)
		db.session.add(ref)
		db.session.commit()

		# notify me I recieved a reference
		msg = Message(
			subject = 'New Reference!',
			recipients = ['blmiller0809@gmail.com'], # replace with evironment variable on prod
			reply_to = form_email,
			)

		msg.html = f"""<p>You recieved a reference from <strong>{fname} {lname}!</strong></p>
					<p><strong>Email: </strong>{form_email}</p>
					<p><strong>Msg:</strong> {form_msg}</p>"""

		mail.send(msg)

		# flash thank you message
		flash("Thank you for your feedback!", "success")
	
	return render_template("references.html", references=references.query.all())


@app.route("/about")
def about_me():
	return render_template("about.html")


@app.route("/contact", methods=["POST", "GET"])
def contact():
	"""check for POST method (contact me form is POSTed here, set first name (fname)
	session variable."""
	if request.method == "POST":
		# Gather form data
		fname = request.form["fname"]
		lname = request.form["lname"]
		form_email = request.form["email"]
		company = request.form["company"]
		sbj = request.form["sbj"]
		form_msg = request.form["msg"]
		session["fname"] = fname # save fname as session variable 'fname'

		# email contact me submission
		msg = Message( # create message to send via flask_mail 
			subject=sbj,
			recipients=['blmiller0809@gmail.com'], # recipients = [list]
			reply_to=form_email
			)
		
		# html format for email
		msg.html = f"""<p><strong>Message From: </strong>{fname} {lname}</p>
					<p><strong>Company: </strong>{company}</p>
					<p>{form_msg}</p>"""
		
		mail.send(msg)

		# set first name as cookie to identify user upon return to site
		res = make_response(redirect(url_for("thank_you")))
		res.set_cookie(
			'fn', # 
			value=fname,
			max_age=2592000,
			)
		
		return res

		# return redirect(url_for("thank_you"))
	
	else:
		return render_template("contact.html")


@app.route("/success")
def thank_you():
	"""looks for fname in session data...uses fname value to present the user's name
	sets 'contact' value to True in session data -> changes footer messaging"""
	if "fname" in session:
		fname = session["fname"]
		session['contact'] = True
		flash("Success! Email sent.", "success")

		return render_template("thankyou.html", fname=fname)
	else:
		return "error"




# ADMIN SECTION (TBD)

# @app.route("/admin", methods=["POST", "GET"])
# def remove_records():
	"""If method is POST, grab the query from the form and use SQLAlchemy to
	execute the query against the db
	requirements:
	- table name
	- record id (or identifier)
	- Create, update, or delete
	- Ability to print and read all tables
	"""

# 	if request.method == "POST":
# 		return "controls"
# 	else:
# 		return render_template("admin/login.html")



if __name__ == '__main__':
	app.run()