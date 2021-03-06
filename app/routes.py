from flask import render_template, flash, redirect, url_for, jsonify
from app import app, db
from app.forms import RegisterClass, LogIn, InsertStudent
from datetime import datetime, timedelta
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Class, Student, Timetable
from app.algorithms.kmean import kcluster
from werkzeug.urls import url_parse
from flask import request, Response
import redis, io, base64

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def get_current_classes():
	'''
	Variable:
		classes is to store current online class
	If statement is to jundge class is online or not online. If class not browse website beyond
	one minute, it's not online
	'''
	classes = list(r.hgetall("simultaneously").values()) 
	curr_time = datetime.now()
	for class_ in classes:
		curr_class = Class.query.filter_by(class_id=class_.decode('utf-8')).first_or_404()
		last_seen = curr_class.last_seen
		if curr_time - last_seen > timedelta(minutes=1):
			r.hdel("simultaneously", class_)

def decode(key, enc):
	'''
	This decode algorithms is copy from
		https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password
	If you want to learn more, please search Vigenère cipher
	'''
	dec = []
	enc = base64.urlsafe_b64decode(enc).decode()
	for i in range(len(enc)):
		key_c = key[i % len(key)]
		dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
		dec.append(dec_c)
	return "".join(dec)

def record(class_id, student_id, today_format):
	'''
	This record function is to check person sign in or not one day.
		Current day is today_format, current day range is [today_format, today_format + timedelta(hours=24))]
	'''
	return Timetable.query.filter_by(time_class_id=class_id).filter_by(
				time_student_id = student_id
			).filter(Timetable.time_time.between(today_format, today_format + timedelta(hours=24))).first()
	
@app.before_request
def before_request():
	'''
	This function is to trace class last browse time
	'''
	if current_user.is_authenticated:
		current_user.last_seen = datetime.now()
		db.session.commit()

@app.route('/')
@app.route('/index')
@login_required
def index():
	'''
	When a class browse index.html, I will stor it to current online classes use HASH function.
	Why hash?
		Because class maybe browse index page for many times, I don't want to store it for many
		times.
	'''
	key = current_user.class_id
	value = key
	r.hset("simultaneously", key, value)
	currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	return render_template('index.html', currentTime=currentTime)
	
@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LogIn()
	if form.validate_on_submit():
		class_ = Class.query.filter_by(class_token=form.token.data).first()
		if class_ is None or not class_.check_password(form.password.data):
			return redirect(url_for('index'))
		login_user(class_, remember=True)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(next_page)
		return redirect(url_for('index'))
	return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegisterClass()
	if form.validate_on_submit():
		class_ = Class(class_name=form.className.data, class_token=form.classToken.data,
				class_teacher=form.classTeacher.data)
		class_.set_password(form.classPassword.data)
		db.session.add(class_)
		db.session.commit()
		return redirect(url_for('login'))
	return render_template('register.html', form=form)

@app.route('/class/<class_name>')
@login_required
def get_class(class_name):
	'''
	How to show student was log in?
	A day has 24 hours. So I can get current day, and add 24 hours for it to represent
	a day from 0~24.
	'''
	class_ = Class.query.filter_by(class_name=class_name).first_or_404()
	students = class_.get_student().all()
	items = []
	today_str = datetime.now().strftime('%Y-%m-%d')
	today_format = datetime.strptime(today_str, "%Y-%m-%d")
	for student in students:
		curr_log_info = record(class_.class_id, student.student_id, today_format)
		if curr_log_info is None:
			active = False
		else:
			active = curr_log_info.active
		items.append((student, active))
	currentTime = class_.last_seen
	return render_template('class.html', class_=class_, currentTime=currentTime, items=items)

@app.route('/class/<class_name>/submit')
@login_required
def post_result(class_name):
	class_ = Class.query.filter_by(class_name=class_name).first_or_404()
	students = class_.get_student().all()
	today_str = datetime.now().strftime('%Y-%m-%d')
	today_format = datetime.strptime(today_str, "%Y-%m-%d")
	for student in students:
		curr_log_info = record(class_.class_id, student.student_id, today_format)
		if curr_log_info is None:

			write_log_info = Timetable(time_class_name=class_.class_name,
				time_class_id=class_.class_id,
				time_student_id=student.student_id,
				time_time=datetime.now(),
				active=False)

			db.session.add(write_log_info)
			db.session.commit()

	return redirect(url_for('get_class', class_name=current_user.class_name))

@app.route('/insert/<class_name>', methods=['GET', 'POST'])
@login_required
def insert_student(class_name):
	form = InsertStudent()
	class_ = Class.query.filter_by(class_name=class_name).first_or_404()
	if form.validate():
		student = Student.query.filter_by(student_name=form.studentName.data).first()
		if student is None:
			student = Student(rfid_id=form.rfidId.data, student_number=form.studentNumber.data, student_name=form.studentName.data)
			db.session.add(student)
		class_.insert(student)
		db.session.commit()
		return redirect(url_for('get_class', class_name=current_user.class_name))
	return render_template('addStudent.html', form=form)

@app.route('/signin')
def signin():
	'''
	Vigenère cipher algorithm to encode URL.
	How to decode?
	When program request this page, it will carrier key which to use decode.
	'''
	get_current_classes()
	classes = list(r.hgetall("simultaneously").values())
	fake_id = request.args.get('rfid_id')
	secret = request.args.get('secret')
	rfid_id = decode(secret, fake_id)[2:-1]
	for class_ in reversed(classes):
		curr_class = Class.query.filter_by(class_id=class_.decode('utf-8')).first_or_404()
		print(curr_class)
		students = curr_class.get_student().all()
		for student in students:
			if student.rfid_id == rfid_id:
				log_info = Timetable(time_class_name=curr_class.class_name,
					time_class_id=curr_class.class_id,
					time_student_id=student.student_id,
					time_time=datetime.now(),
					active=True)
				db.session.add(log_info)
				db.session.commit()
				return student.student_name
	return rfid_id

@app.route('/online')
def online():
	get_current_classes()
	online_class = []
	for i in r.hgetall("simultaneously").values():
		class_ = Class.query.filter_by(class_id=i.decode('utf-8')).first_or_404()
		online_class.append(class_)
	return render_template('onlineclass.html', online_class=online_class)

@app.route('/student/search')
def student_search():
	return render_template('student_search.html')

@app.route('/class/search')
def class_search():
	return render_template('class_search.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/group/<class_name>')
def group(class_name):
	'''
	Kmean algorithm to Grouping.
	Input is 2D list, return is 1D list.
	Using dict to store index and name, after get result. Using dict to translate index->name.
	'''
	parent = []
	class_ = Class.query.filter_by(class_name=class_name).first_or_404()
	students = class_.get_student().all()
	dict = {}
	for i in range(len(students)):
		child = []
		dict[i] = students[i].student_name
		historys = Timetable.query.filter_by(time_class_id=class_.class_id).filter_by(
			time_student_id=students[i].student_id).all()
		for history in historys:
			time = int(history.time_time.strftime('%Y-%m-%d %H:%M:%S').split(' ')[1].replace(':', '')) \
				/ 100000
			child.append(time)
		parent.append(child)
	result = kcluster(parent)
	for i in range(len(result)):
		for j in range(len(result[i])):
			result[i][j] = dict[result[i][j]]
	return render_template("group.html", result=result)