import os
import smtplib
from flask import Flask, redirect, url_for, render_template, send_file, request, session, make_response, flash
from flask_login import LoginManager, UserMixin, login_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


app = Flask(__name__)
app.config.from_pyfile('config.py')

mail = Mail(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class admin_user_table(UserMixin, db.Model):
	id = db.Column("id", db.Integer, primary_key=True)
	username = db.Column(db.String(25), unique=True)
	password = db.Column(db.String(25))

	# def __init__(self, username, password):
	# 	self.username = username
	# 	self.password = password

	# def __repr__(self):
	# 	return '<admin_users %r>' % self.username, self.password

@login_manager.user_loader
def load_user(user_id):
	return admin_user_table.query.get(int(user_id))

class references(db.Model):
	# create model (table), "references" in SQLite db using SQLAlchemy
	_id = db.Column("id", db.Integer, primary_key=True)
	fname = db.Column(db.String(100))
	lname = db.Column(db.String(100))
	title = db.Column(db.String(100))
	email = db.Column(db.String(100))
	relationship = db.Column(db.String(100))
	msg = db.Column(db.String(255))
	approved = db.Column(db.Boolean)

	def __init__(self, fname, lname, title, email, relationship, msg, approved):
		self.fname = fname
		self.lname = lname
		self.title = title
		self.email = email
		self.relationship = relationship
		self.msg = msg
		self.approved = approved

	def __repr__(self):
		return '<references %r>' % self.fname,
		self.lname,
		self.title,
		self.email,
		self.relationship,
		self.msg,
		self.approved

db.create_all()

# create pages

@app.route("/")
def home():
	"""Gets fname from Cookie variable to greet user if we know their first name"""
	cookies = request.cookies
	fn = cookies.get('fn')


	# pass references table from db and first name cookie for use on the homepage
	return render_template("index.html",
		references=references.query.all(),
		fn=fn)

# DOWNLOAD ROUTES

@app.route("/brandon_miller_resume/")
def return_resume():
	return send_file(
		"static/downloads/20210103_Brandon_Miller_Resume.pdf", 
		as_attachment=True,
		attachment_filename="Brandon_Miller_Resume.pdf",
		)

@app.route("/directmail-kit/")
def return_dmkit():
	return send_file(
		"static/downloads/coa.zip",
		as_attachment=True,
		attachment_filename="CoA_DM_Kit.zip")

@app.route("/automation_example/")
def return_automation():
	return send_file(
		"static/downloads/automation.gif",
		as_attachment=True,
		attachment_filename="python_automation.gif",
		)

@app.route("/pwm-download/")
def return_pwm():
	return send_file("static/downloads/pwm.zip",
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
		apr = False

		# write data to refrences database
		ref = references(fname,
			lname,
			title,
			form_email,
			relationship,
			form_msg,
			apr)
		db.session.add(ref)
		db.session.commit()


		# send email using SendGrid API
		msg = Mail(from_email='brandon@brandonlmiller.com',
			to_emails='blmiller0809@gmail.com',
			subject='New Reference!',
			html_content=f"""<p>You recieved a reference from <strong>{fname} {lname}!</strong></p>
		 			<p><strong>Email: </strong>{form_email}</p>
		 			<p><strong>Msg:</strong> {form_msg}</p>""")

		try:
			sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
			response = sg.send(msg)
			print(response.status_code)
			print(response.body)
			print(response.headers)
		except Exception as e:
			print(e.msg)

		# flash thank you message
		flash("Thank you! Your reference has been submitted.", "success")
	
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

		
		# send email using SendGrid API
		msg = Mail(from_email='brandon@brandonlmiller.com',
			to_emails='blmiller0809@gmail.com',
			subject=sbj,
			html_content=f"""<p><strong>Message From: </strong>{fname} {lname}</p>
		 			<p><strong>Company: </strong>{company}</p>
		 			<p>{form_msg}</p>""")

		try:
			sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
			response = sg.send(msg)
			print(response.status_code)
			print(response.body)
			print(response.headers)
		except Exception as e:
			print(e.msg)

		# set first name as cookie to identify user upon return to site
		res = make_response(redirect(url_for("thank_you")))
		res.set_cookie(
			'fn', # cookie name
			value=fname,
			max_age=2592000,
			httponly=True,
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

@app.errorhandler(404)
def not_found(self):
    """Page not found."""
    return make_response(render_template("404.html"), 404)







# admin routes

@app.route("/admin/index", methods=["GET", "POST"])
def admin_home():
	if request.method == "POST":
		"""insert logic for logging in to admin
		probably need to use Flask-Admin or something
		like that for this."""
		username = request.form["username"]
		password = request.form["password"]
		user = admin_user_table.query.filter_by(username=username, password=password).first()

		if user:
			login_user(user)
			flash("Logged In!", "success")
			return render_template("admin/home.html")
		else:
			flash("Unable to login.", "error")
			return render_template("admin/index.html")
	else:
		return render_template("admin/index.html")

@app.route("/admin/users")
@login_required
def admin_users():
	return render_template("admin/admin_users.html",
		users=admin_user_table.query.all(),
		)


@app.route("/admin/references")
@login_required
def admin_references():
	return render_template("admin/admin_references.html",
		references=references.query.all(),
		)

@app.route("/admin/references/approve")
@login_required
def update_record():
	ref_id = request.args.get("ref_id")
	if ref_id:
		ref_id = float(ref_id)
		x = references.query.get(ref_id)
		x.approved = True
		db.session.commit()

	return render_template("admin/admin_references.html",
		references=references.query.all(),
		)

@app.route("/admin/references/delete")
@login_required
def delete_record():
	ref_id = request.args.get("ref_id")
	if ref_id:
		ref_id = float(ref_id)
		x = references.query.get(ref_id)
		db.session.delete(x)
		db.session.commit()

	return render_template("admin/admin_references.html",
		references=references.query.all(),
		)



if __name__ == '__main__':
	app.run()