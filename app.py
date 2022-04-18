from __future__ import division
from cProfile import run

from cv2 import convexityDefects
import mysql.connector
import sys
import datetime
from mysql.connector import Error
from flask import Flask, request, jsonify, render_template
from random import randint
import re
import qrcode
from flask import flash
from encodings import utf_8
from ast import And
from email import message
from flask import Flask, url_for, render_template, request, redirect, session, json
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from sqlalchemy import false, true, text
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_recaptcha import ReCaptcha
from flask_wtf import RecaptchaField
from flask_mail import *
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from os import remove
import time
import pymysql
from collections import OrderedDict
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SECRET_KEY'] = "Thisisnotasecret;)"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:adminwebapp@database-1.caqypwmxgqo6.us-east-1.rds.amazonaws.com:3306/theatres'
db = SQLAlchemy(app)
recaptcha = ReCaptcha(app=app)

app.config.update(dict(
    RECAPTCHA_ENABLED=True,
    RECAPTCHA_SITE_KEY="6LcXCoAeAAAAAAtcUkBUt_sRKUifi_M7oeGBdhLM",
    RECAPTCHA_SECRET_KEY="6LcXCoAeAAAAAC4T09HsSL8eTAcT22Zp5OuNe0XM",
))

recaptcha = ReCaptcha()
recaptcha.init_app(app)


class User(UserMixin, db.Model):
    #id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100))
    lname = db.Column(db.String(100))
    email = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100))
    city = db.Column(db.String(30))
    state = db.Column(db.String(10))

    def __init__(self, fname, lname, email, password, city, state):
        self.fname = fname
        self.lname = lname
        self.email = email
        self.password = password
        self.city = city
        self.state = state


class Mgr(UserMixin, db.Model):
    #id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100))
    lname = db.Column(db.String(100))
    email = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(256))

    def __init__(self, fname, lname, email, password):
        self.fname = fname
        self.lname = lname
        self.email = email
        self.password = password


class Theatre(UserMixin, db.Model):
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    email = db.Column(db.String(100), primary_key=True)
    city = db.Column(db.String(30))
    state = db.Column(db.String(20))

    def __init__(self, name, address, email, city, state):
        self.name = name
        self.address = address
        self.email = email
        self.city = city
        self.state = state


class CoupounCode(db.Model):
    #id = db.Column(db.Integer, default=4,  primary_key=True)
    code = db.Column(db.String(6))
    discount = db.Column(db.Integer, default=0)
    dates = db.Column(db.Date)
    extra = db.Column(db.String(100), primary_key=True)

    def __init__(self, code, discount, dates, extra):
        self.code = code
        self.discount = discount
        self.dates = dates
        self.extra = extra


app.config.from_pyfile('config.cfg')
mail = Mail(app)
s = URLSafeTimedSerializer('Thisisasecret!')


@app.route('/')
def renderLoginPage():
    return redirect(url_for('login'))


generate = 0
date, movieName, movieType, time, price, prices = '', '', '', '', 0, 0


@app.route('/login', methods=['GET', 'POST'])
def login():
    global date, movieName, movieType, time, price, prices
    date, movieName, movieType, time, price, prices = '', '', '', '', 0, 0
    if(session.get('logged_in')):
        if(session.get('theatre_name')):
            res = runQuery('call delete_old()')
            return render_template('manager.html', theatre_name=session['theatre_name'], theatre_address=session['theatre_address'])
        else:
            res = runQuery('call delete_old()')
            return render_template('cashier.html', message=session['fname']+" "+session['lname'], location=session['city']+", "+session['state'])
    global generate
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form['email']
        password = request.form['password']
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if(not re.fullmatch(regex, email)):
            return render_template('login.html', message="Please provide proper email")
        elif "'" in password or '"' in password:
            semicolon, colon = "'", '"'
            return render_template('register.html', message="Password cannot contain "+semicolon+" or "+colon)
        elif(len(password) < 8):
            return render_template('login.html', message="Password is less than 8 characters")
        elif(not recaptcha.verify()):
            return render_template('login.html', message="Please verify captcha first")
        try:
            amg = Mgr.query.filter_by(email=email).first()
            if amg:
                if (amg and check_password_hash(amg.password, password)):
                    session['email'] = email
                    session['logged_in'] = True
                    query = text(
                        "select fname, lname from mgr where email = '"+session['email']+"';")
                    data = db.engine.execute(query).first()
                    session['fname'] = data.fname
                    session['lname'] = data.lname
                    query = text(
                        "select * from theatre where email = '"+session['email']+"';")
                    data = db.engine.execute(query).first()
                    session['theatre_name'] = data.name
                    session['theatre_address'] = data.address
                    session['city'] = data.city
                    session['state'] = data.state
                    # session['theatre_pincode']=str(data.pincode)
                    '''query = text("select division_name,district from indian_pincodes where pincode = "+str(data.pincode)+";")
                    data = db.engine.execute(query).first()
                    session['division_name']=data.division_name
                    session['district']=data.district'''
                    return render_template('manager.html', theatre_name=session['theatre_name'], theatre_address=session['theatre_address'])
                elif not (amg and check_password_hash(amg.password, password)):
                    return render_template('login.html', message="Incorrect Password")
                return render_template('login.html', message="Recheck the Field in mgr")

                # if email == 'manager@gmail.com' and password == 'manager':
                #res = runQuery('call delete_old()')
                # return render_template('manager.html')
            else:
                '''elif request.form['register link']=="go to register page":
                return render_template('register.html')'''
                # print("Success")
                email = request.form['email']
                password = request.form['password']
                data = User.query.filter_by(email=email).first()
                #print("flag 1"+data.fname+" "+str(recaptcha.verify()))
                if (data and check_password_hash(data.password, password)):
                    # print("flag2")
                    session['email'] = email
                    otp = randint(1000, 9999)
                    generate = otp
                    msg = Message(
                        'Confirm OTP', sender='playpubg34@gmail.com', recipients=[email])
                    msg.body = str(generate)  # 'Your link is {}'.format(link)
                    mail.send(msg)
                    smail = s.dumps(email)
                    return render_template('verify.html')
                    # return redirect('/confirm')
                    # #session['logged_in'] = True
                    # #return redirect(url_for('index'))
                elif(data == None):
                    return render_template('login.html', message="Email is not registered")
                elif not (data and check_password_hash(data.password, password)):
                    return render_template('login.html', message="Incorrect Password")
                return render_template('login.html', message="Recheck the Field")
            # return render_template('loginfail.html')
        except Exception as e:
            print(e)
            #flash("Issue on Server End")
            # redirect(url_for('login'))
            return render_template('login.html', message="Issue on Server End, please try again later")


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    session.clear()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    state = {}
    res = runQuery("select distinct state,district from indian_pincodes")
    for i in res:
        if i[0] not in state.keys():
            state[i[0]] = []
        #res1=runQuery("select district from indian_pincodes where state = '"+str(i[0])+"'")
        # for j in res1:
        # for j in i[1]:
        state[i[0]].append(i[1].capitalize())
    for i in state.keys():
        state[i] = sorted(state[i])
    if request.method == "GET":
        return render_template('register.html', states=sorted(state.keys()), cities=state)
    else:
        email = request.form['email']
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if(not re.fullmatch(regex, email)):
            return render_template('register.html', message="Please provide proper email", states=sorted(state.keys()), cities=state)
        user = User.query.filter_by(email=email).first()
        if not user:
            fname = request.form['fname']
            lname = request.form['lname']
            email = request.form['email']
            #pincode = request.form['pincode']
            password, cnfpassword = request.form['password'], request.form['cnfpassword']
            state1, city = str(request.form.get('state')), str(
                request.form.get('city'))
            #print(state," ",city)
            #password=request.form['password'], cnfpassword=request.form['cnfpassword']
            if len(fname) == 0 or not fname.isalpha():
                return render_template('register.html', message="First Name should be letters only", states=sorted(state.keys()), cities=state)
            elif len(lname) == 0 or not lname.isalpha():
                return render_template('register.html', message="Last Name should be letters only", states=sorted(state.keys()), cities=state)
            elif len(password) < 8:
                return render_template('register.html', message="Password should be 8 to 15 characters long", states=sorted(state.keys()), cities=state)
            elif ("'" in password or "'" in cnfpassword) or ('"' in password or '"' in cnfpassword):
                semicolon, colon = "'", '"'
                return render_template('register.html', message="Password cannot contain "+semicolon+" or "+colon, states=sorted(state.keys()), cities=state)
            elif len(cnfpassword) < 8:
                return render_template('register.html', message="Please confirm password properly", states=sorted(state.keys()), cities=state)
            elif not state1 or "Select" in state1:
                return render_template('register.html', message="Please Select State properly", states=sorted(state.keys()), cities=state)
            elif not city or "Select" in city:
                return render_template('register.html', message="Please Select City properly", states=sorted(state.keys()), cities=state)
            elif(password == cnfpassword):
                manager = Mgr.query.filter_by(email=email).first()
                if manager:
                    return render_template('register.html', message="User already exists as manager", states=sorted(state.keys()), cities=state)
                password = generate_password_hash(password, method='sha256')
                token = s.dumps(email,  salt='email-confirm')
                tokens = s.dumps(fname)
                tokenss = s.dumps(lname)
                tokensss = s.dumps(password)
                tokenssss = s.dumps(city)
                tokensssss = s.dumps(state1)
                msg = Message(
                    'Confirm Email', sender='playpubg34@gmail.com', recipients=[email])
                link = url_for('confirm_email', fname=tokens, lname=tokenss,
                               password=tokensss, token=token, city=tokenssss, state=tokensssss, _external=True)
                msg.body = 'Your link is {}'.format(link)
                mail.send(msg)
                #db.session.add(User(fname=request.form['fname'], lname=request.form['lname'], email=request.form['email'], password=generate_password_hash(password, method='sha256')))
                # db.session.commit()
                return render_template('login.html')
            else:
                return render_template('register.html', message="Please confirm proper password", states=sorted(state.keys()), cities=state)
        else:
            return render_template('register.html', message="User already exists", states=sorted(state.keys()), cities=state)


@app.route('/manregister', methods=['GET', 'POST'])
def manregister():
    state = {}
    res = runQuery("select distinct state,district from indian_pincodes")
    for i in res:
        if i[0] not in state.keys():
            state[i[0]] = []
        #res1=runQuery("select district from indian_pincodes where state = '"+str(i[0])+"'")
        # for j in res1:
        # for j in i[1]:
        state[i[0]].append(i[1].capitalize())
    for i in state.keys():
        state[i] = sorted(state[i])
    if request.method == "GET":
        return render_template('manregister.html', states=sorted(state.keys()), cities=state)
    else:
        email = request.form['email']
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if(not re.fullmatch(regex, email)):
            return render_template('manregister.html', message="Please provide proper email", states=sorted(state.keys()), cities=state)
        user = Mgr.query.filter_by(email=email).first()
        if not user:
            u = User.query.filter_by(email=email).first()
            if u:
                return render_template('manregister.html', message="User already exists as cashier", states=sorted(state.keys()), cities=state)
            #password=request.form['password'], cnfpassword=request.form['cnfpassword']
            #password, cnfpassword = request.form['password'], request.form['cnfpassword']
            fname = request.form['fname']
            lname = request.form['lname']
            email = request.form['email']
            theatre_name = request.form['theatre_name']
            theatre_address = request.form['theatre_address']
            #theatre_pincode = request.form['theatre_pincode']
            city = request.form['city']
            state1 = request.form['state']
            '''fname = request.form['fname']
            lname = request.form['lname']
            email = request.form['email']
            pincode = request.form['theatre_pincode']'''
            password, cnfpassword = request.form['password'], request.form['cnfpassword']
            #password=request.form['password'], cnfpassword=request.form['cnfpassword']
            if len(fname) == 0 or not fname.isalpha():
                return render_template('manregister.html', message="First Name should be letters only", states=sorted(state.keys()), cities=state)
            elif len(lname) == 0 or not lname.isalpha():
                return render_template('manregister.html', message="Last Name should be letters only", states=sorted(state.keys()), cities=state)
            elif len(password) < 8:
                return render_template('manregister.html', message="Password should be 8 to 15 characters long", states=sorted(state.keys()), cities=state)
            elif ("'" in password or "'" in cnfpassword) or ('"' in password or '"' in cnfpassword):
                semicolon, colon = "'", '"'
                return render_template('manregister.html', message="Password cannot contain "+semicolon+" or "+colon, states=sorted(state.keys()), cities=state)
            elif len(cnfpassword) < 8:
                return render_template('manregister.html', message="Please confirm password properly", states=sorted(state.keys()), cities=state)
            elif len(theatre_name) == 0:
                return render_template('manregister.html', message="Theatre Name cannot be left blank", states=sorted(state.keys()), cities=state)
            elif "'" in theatre_name or '"' in theatre_name:
                semicolon = "'"
                colon = '"'
                return render_template('manregister.html', message="Theatre Name cannot contain "+semicolon+" or "+colon, states=sorted(state.keys()), cities=state)
            elif len(theatre_address) == 0:
                return render_template('manregister.html', message="Theatre Address cannot be left blank", states=sorted(state.keys()), cities=state)
            elif "'" in theatre_address or '"' in theatre_address:
                semicolon = "'"
                colon = '"'
                return render_template('manregister.html', message="Theatre Address cannot contain "+semicolon+" or "+colon, states=sorted(state.keys()), cities=state)
            elif not state1 or "Select" in state1:
                return render_template('manregister.html', message="Please Select State properly", states=sorted(state.keys()), cities=state)
            elif not city or "Select" in city:
                return render_template('manregister.html', message="Please Select City properly", states=sorted(state.keys()), cities=state)
            elif(password == cnfpassword):
                password = generate_password_hash(password, method='sha256')
                oken = s.dumps(email,  salt='email-confirms')
                okens = s.dumps(fname)
                okenss = s.dumps(lname)
                okensss = s.dumps(password)
                okenssss = s.dumps(theatre_name)
                okensssss = s.dumps(theatre_address)
                okenssssss = s.dumps(city)
                okensssssss = s.dumps(state1)
                msg = Message(
                    'Confirm Email', sender='playpubg34@gmail.com', recipients=[email])
                link = url_for('man_confirm_email', fname=okens, lname=okenss,
                               password=okensss, oken=oken, theatre_name=okenssss, theatre_address=okensssss, city=okenssssss, state=okensssssss, _external=True)
                msg.body = 'Your link is {}'.format(link)
                mail.send(msg)
                #db.session.add(User(fname=request.form['fname'], lname=request.form['lname'], email=request.form['email'], password=generate_password_hash(password, method='sha256')))
                # db.session.commit()
                return render_template('login.html')
            else:
                return render_template('manregister.html', message="Please confirm proper password", states=sorted(state.keys()), cities=state)
        else:
            return render_template('manregister.html', message="User already exists", states=sorted(state.keys()), cities=state)


generated_otp = 0


@app.route('/resend', methods=['GET', 'POST'])
def resend():
    global generated_otp
    #email = request.args.get('email')
    #if request.method == 'GET':
        #return render_template('resend.html')
        # return render_template('verify.html')
    newotp = randint(1000, 9999)
    generated_otp = newotp
    mails = session['email']
    print('mail',mails)
    #mails = request.form['email']
    #regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    #if(not re.fullmatch(mails)):
        #return render_template('resend.html', message="Please provide proper email")
    msg = Message('Confirm OTP', sender='playpubg34@gmail.com',
                  recipients=[mails])
    msg.body = str(newotp)  # 'Your link is {}'.format(link)
    mail.send(msg)
    return render_template('verify.html')
    # return redirect('/confirm')


@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:

        email = s.loads(token, salt='email-confirm', max_age=120)
        fname = s.loads(request.args.get('fname'))
        #fname = request.args.get('fname')
        lname = s.loads(request.args.get('lname'))
        password = s.loads(request.args.get('password'))
        #pincode = int(s.loads(request.args.get('pincode')))
        city = s.loads(request.args.get('city'))
        state = s.loads(request.args.get('state'))
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    ml = User.query.filter_by(email=email).first()
    if ml:
        return render_template('emailalreadyconfirm.html')
    else:
        #ml.confirmed = True
        new_ml = User(email=email, fname=fname, lname=lname,
                      password=password, city=city, state=state)
        db.session.add(new_ml)
        db.session.commit()
        return render_template('emailverification.html')
        # return '<h1>The token works!</h1>'


@app.route('/man_confirm_email/<oken>')
def man_confirm_email(oken):
    try:

        email = s.loads(oken, salt='email-confirms', max_age=120)
        fname = s.loads(request.args.get('fname'))
        lname = s.loads(request.args.get('lname'))
        password = s.loads(request.args.get('password'))
        theatre_name = s.loads(request.args.get('theatre_name'))
        theatre_address = s.loads(request.args.get('theatre_address'))
        #theatre_pincode = int(s.loads(request.args.get('theatre_pincode')))
        city = s.loads(request.args.get('city'))
        state = s.loads(request.args.get('state'))
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    ml = Mgr.query.filter_by(email=email).first()
    if ml:
        return render_template('emailalreadyconfirm.html')
    else:
        #ml.confirmed = True
        new_mlm = Mgr(fname=fname, lname=lname,
                      email=email, password=password)
        new_theatre = Theatre(
            name=theatre_name, address=theatre_address, city=city, state=state, email=email)
        db.session.add(new_mlm)
        db.session.add(new_theatre)
        db.session.commit()
        res = runQuery('insert into halls values(1, "gold", 35,"'+email+'"), (1, "standard", 75,"'+email+'"), (2, "gold", 27,"' +
                       email+'"), (2, "standard", 97,"'+email+'"), (3, "gold", 26,"'+email+'"), (3, "standard", 98,"'+email+'");')
        res = runQuery('insert into price_listing values(1, "2D", "Monday", 210,"'+email+'"), (2, "3D", "Monday", 295,"'+email+'"),(3, "4DX", "Monday", 380,"'+email+'"),(4, "2D", "Tuesday", 210,"'+email+'"),(5, "3D", "Tuesday", 295,"'+email+'"),(6, "4DX", "Tuesday", 380,"'+email+'"),(7, "2D", "Wednesday", 210,"'+email+'"),(8, "3D", "Wednesday", 295,"'+email+'"),(9, "4DX", "Wednesday", 380,"'+email+'"),(10, "2D", "Thursday", 210,"'+email +
                       '"),(11, "3D", "Thursday", 295,"'+email+'"),(12, "4DX", "Thursday", 380,"'+email+'"),(13, "2D", "Friday", 320,"'+email+'"),(14, "3D", "Friday", 335,"'+email+'"),(15, "4DX", "Friday", 495,"'+email+'"),(16, "2D", "Saturday", 320,"'+email+'"),(17, "3D", "Saturday", 335,"'+email+'"),(18, "4DX", "Saturday", 495,"'+email+'"),(19, "2D", "Sunday", 320,"'+email+'"),(20, "3D", "Sunday", 335,"'+email+'"),(21, "4DX", "Sunday", 495,"'+email+'");')
        return render_template('emailverification.html')
        # return '<h1>The token works!</h1>'


@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    global generated_otp
    global generate
    #email = s.loads(request.args.get('email'))
    # if request.method == 'GET':
    #    return render_template('verify.html')

    userotp = request.form['otp']
    if generate == int(userotp) or generated_otp == int(userotp):
        session['logged_in'] = True
        query = text(
            "select fname, lname, city, state from user where email = '"+session['email']+"'")
        data = db.engine.execute(query).first()
        session['fname'] = data.fname
        session['lname'] = data.lname
        session['city'] = str(data.city)
        session['state'] = str(data.state)
        #query = text("select division_name,district from indian_pincodes where pincode = "+session['pincode']+";")
        #data = db.engine.execute(query).first()
        # session['division_name']=data.division_name
        # session['district']=data.district
        return redirect('/')
    else:
        return render_template('verify.html', message='Wrong OTP')
        # return render_template('home.html')

# Routes for cashier


r = URLSafeTimedSerializer('Thisisasecretkey!')


@app.route('/passreset', methods=['GET', 'POST'])
def passreset():
    if request.method == 'GET':
        return render_template('pass_reset.html')
    email = request.form['email']
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(not re.fullmatch(regex, email)):
        return render_template('pass_reset.html', message="Please provide proper email")
    user = User.query.filter_by(email=email).first()
    man = Mgr.query.filter_by(email=email).first()
    if user:
        token = r.dumps(email,  salt='pass-reset')
        msg = Message('Password reset flask app',
                      sender='playpubg34@gmail.com', recipients=[email])
        link = url_for('pass_reset',  token=token, _external=True)
        msg.body = 'Your link to change password is {}'.format(link)
        mail.send(msg)
        return redirect(url_for('login'))
    elif man:
        token = r.dumps(email,  salt='pass-reset')
        msg = Message('Password reset flask app',
                      sender='playpubg34@gmail.com', recipients=[email])
        link = url_for('pass_reset',  token=token, _external=True)
        msg.body = 'Your link to change password is {}'.format(link)
        mail.send(msg)
        return redirect(url_for('login'))
    else:
        return render_template('pass_reset.html', message='email not found')


@app.route('/pass_reset/<token>')
def pass_reset(token):
    try:
        smail = r.loads(token, salt='pass-reset', max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'

    ps = User.query.filter_by(email=smail).first()
    mps = Mgr.query.filter_by(email=smail).first()
    if ps:
        email = r.dumps(smail)
        return redirect(url_for('password_reset', email=email))
    elif mps:
        email = r.dumps(smail)
        return redirect(url_for('password_reset', email=email))
    else:
        return render_template('emailverification.html')


@app.route('/password_reset/<email>', methods=['GET', 'POST'])
def password_reset(email):
    if request.method == 'GET':
        return render_template('password_reset.html')
    email = r.loads(email)
    #print('email is = ', email)
    # email=request.form['email']
    #password = request.form['password']
    #cnfpassword = request.form['cnfpassword']
    user = User.query.filter_by(email=email).first()
    man = Mgr.query.filter_by(email=email).first()
    if user:
        password, cnfpassword = request.form['password'], request.form['cnfpassword']
        if len(password) < 8:
            return render_template('password_reset.html', message="Password should be 8 to 15 characters long")
        elif ("'" in password or "'" in cnfpassword) or ('"' in password or '"' in cnfpassword):
            semicolon, colon = "'", '"'
            return render_template('password_reset.html', message="Password cannot contain "+semicolon+" or "+colon)
        elif len(cnfpassword) < 8:
            return render_template('password_reset.html', message="Please confirm password properly")
        elif(password == cnfpassword):
            password = generate_password_hash(password, method='sha256')
            user.password = password
            db.session.commit()
            #flash('password has been updated')
            # return redirect(url_for('login'))
            return render_template('passupdated.html')
        else:
            return render_template('password_reset.html', message="Please confirm password properly")
    elif man:
        password, cnfpassword = request.form['password'], request.form['cnfpassword']
        if len(password) < 8:
            return render_template('password_reset.html', message="Password should be 8 to 15 characters long")
        elif ("'" in password or "'" in cnfpassword) or ('"' in password or '"' in cnfpassword):
            semicolon, colon = "'", '"'
            return render_template('password_reset.html', message="Password cannot contain "+semicolon+" or "+colon)
        elif len(cnfpassword) < 8:
            return render_template('password_reset.html', message="Please confirm password properly")
        elif(password == cnfpassword):
            password = generate_password_hash(password, method='sha256')
            man.password = password
            db.session.commit()
            #flash('password has been updated')
            # return redirect(url_for('login'))
            return render_template('passupdated.html')
        else:
            return render_template('password_reset.html', message="Please confirm password properly")
    else:
        return 'hello 3'


@app.route('/getMoviesShowingOnDate', methods=['POST'])
def moviesOnDate():
    global date, movieName
    date = request.form['date']

    res = runQuery("select distinct movie_id,type from shows where date='"+str(date)+"' and email in (select email from theatre where state = '" +
                   session['state']+"' and city = '"+session['city']+"') and (datediff(Date,cast(now() as date))>0 or timediff(cast(time*100 as time),cast(now() as time))>0)")
    if res == []:
        return '<h4>No Movies Showing</h4>\
        <button onclick="spinner_load()">Ok</button>'
    else:
        temp, temp1 = [], []
        for i in res:
            res1 = runQuery("select movie_name,language from movies where movie_id = "+str(
                i[0])+" and state = '"+session['state']+"' and city = '"+session['city']+"'")
            if res1 != []:
                temp.append(i[0])
                temp.append(res1[0][0])
                temp.append(res1[0][1])
                temp.append(i[1])
                temp1.append(temp)
                temp = []
            #res = runQuery("SELECT DISTINCT movies.movie_id,movies.movie_name,movies.language,shows.type from shows natural join movies WHERE shows.Date = '"+date+"' and movies.division_name='"+session['division_name']+"' or movies.district = '"+session['district']+"'")
            #res = runQuery("select movie_id,movie_name,language from movies where movie_id in (select movie_id from shows where date = '"+str(date)+"') and division_name='"+session['division_name']+"' or district = '"+session['district']+"'")
        if temp1 == []:
            return '<h4>No Movies Showing</h4>\
            <button onclick="spinner_load()">Ok</button>'
        return render_template('movies.html', movies=temp1)


@app.route('/getTheatres', methods=['POST'])
def available_theatres():
    global date, movieType, time, movieName
    date = request.form['date']
    movieID = request.form['movieID']
    movieType = request.form['type']
    #manager_email = request.form['manager_email']
    movieName = runQuery("select * from movies where movie_id = "+movieID)
    movieName = list(movieName)
    res = runQuery("select distinct email from shows where movie_id = "+movieID+" and date = '"+str(date)+"' and type = '" +
                   str(movieType)+"' and (datediff(Date,cast(now() as date))>0 or timediff(cast(time*100 as time),cast(now() as time))>0)")
    l = []
    if res != []:
        for i in res:
            manager_email = i[0]
            q = runQuery("select * from theatre where  state = '" +
                         session['state']+"' and city = '"+session['city']+"' and email = '"+manager_email+"'")
            for j in q:
                l.append((manager_email, j[0], j[1], j[2]))
    return render_template('theatre.html', theatre_list=l)


@app.route('/getTimings', methods=['POST'])
def timingsForMovie():
    global date, movieType, time
    date = request.form['date']
    movieID = request.form['movieID']
    movieType = request.form['type']
    manager_email = request.form['manager_email']

    res = runQuery("SELECT time FROM shows WHERE Date='"+date + "' and movie_id = "+movieID+" and type ='"+movieType+"' and email = '" +
                   manager_email+"' and (datediff(Date,cast(now() as date))>0 or timediff(cast(time*100 as time),cast(now() as time))>0)")

    l = []
    for li in res:
        i = list(li)
        temp = i[0]//100
        meridiem = 0
        if(temp == 0):
            temp = 12
        elif(temp >= 12):
            meridiem = 1
            if(temp > 12):
                temp = temp-12
        l.append([i[0], temp, i[0] %
                  100 if i[0] % 100 != 0 else '00', meridiem])
        time = i[0]
    l = sorted(l, key=lambda x: (x[3], x[1], int(x[2])))
    # print(l)
    return render_template('timings.html', timings=l)


@app.route('/getShowID', methods=['POST'])
def getShowID():
    global time
    date = request.form['date']
    movieID = request.form['movieID']
    movieType = request.form['type']
    time = request.form['time']
    manager_email = request.form['manager_email']

    res = runQuery("SELECT show_id FROM shows WHERE Date='"+date +
                   "' and movie_id = "+movieID+" and type ='"+movieType+"' and time = "+time+" and email = '"+manager_email+"';")
    return jsonify({"showID": res[0][0]})


@app.route('/getAvailableSeats', methods=['POST'])
def getSeating():
    showID = request.form['showID']
    manager_email = request.form['manager_email']
    res = runQuery(
        "SELECT class,no_of_seats FROM shows NATURAL JOIN halls WHERE show_id = "+showID)
    res1 = runQuery(
        "select distinct price_id from shows where show_id = "+showID)

    totalGold = 0
    totalStandard = 0

    for i in res:
        if i[0] == 'gold':
            totalGold = i[1]
        if i[0] == 'standard':
            totalStandard = i[1]

    res = runQuery(
        "SELECT seat_no FROM booked_tickets WHERE show_id = "+showID)

    goldSeats = []
    standardSeats = []

    for i in range(1, totalGold + 1):
        goldSeats.append([i, ''])

    for i in range(1, totalStandard + 1):
        standardSeats.append([i, ''])

    for i in res:
        if i[0] > 1000:
            goldSeats[i[0] % 1000 - 1][1] = 'disabled'
        else:
            standardSeats[i[0] - 1][1] = 'disabled'
    #res = runQuery("INSERT INTO halls VALUES(-1,'-1',-1,'"+manager_email+"')")
    #res = runQuery("DELETE FROM halls WHERE hall_id = -1")
    res = runQuery("select price from price_listing where price_id = " +
                   str(res1[0][0])+" and email = '"+manager_email+"' and type = '"+movieType+"'")
    if res == []:
        return '<h5>Prices Have Not Been Assigned To This Show, Try Again Later</h5>\
        <button onclick="spinner_load()">Ok</button>'
    global price
    price = int(res[0][0])

    return render_template('seating.html', goldSeats=goldSeats, standardSeats=standardSeats)


category_seats = {}


@app.route('/getPrice', methods=['POST'])
def getPriceForClass():
    global price, prices
    showID = request.form['showID']
    selected_seats = json.loads(request.form['selected_seats'])
    if(len(selected_seats) == 0):
        return '<h5>No seats selected</h5>'
    #seatClass = request.form['seatClass']
    prices = 0
    for seat in selected_seats.keys():
        if 'gold' in seat:
            prices = prices+(price * 1.5)
        else:
            prices = prices+price
    colon = "'"

    return '<h5>Ticket Price: ₹ '+str(prices)+'</h5>\
	<button id="Cancel-btn" onclick="spinner_load()">Cancel</button><button id="Coupon-btn" onclick="this.disabled=true;document.getElementById('+colon+'Cancel-btn'+colon+').disabled=true;document.getElementById('+colon+'Confirm-btn'+colon+').disabled=true;apply_coupon()">Apply Coupon Code</button><button id="Confirm-btn" onclick="this.disabled=true;document.getElementById('+colon+'Cancel-btn'+colon+').disabled=true;document.getElementById('+colon+'Coupon-btn'+colon+').disabled=true;confirmBooking()">Confirm</button>'


@app.route('/applycoupon', methods=['POST'])
def apply_coupon():
    global prices
    showID = request.form['showID']
    selected_seats = json.loads(request.form['selected_seats'])
    #coupon_code = request.form['coupon_code']
    cpns = request.form['coupon_code']
    coupon_code = CoupounCode.query.filter_by(code=cpns).first()
    session['coupoun'] = cpns
    '''coupon code logic start here'''
    if not coupon_code:
        return '<h5>Invalid coupon code, try booking again</h5>\
        <button onclick="apply_coupon()">Ok</button>'
    else:
        '''calculate new price here'''
        query = text(
            "select discount from coupoun_code where code = '"+session['coupoun']+"'")
        data = db.engine.execute(query).first()
        session['discount'] = data.discount
        discounts = session['discount']
        print('final', discounts)
        discountAmount = (prices * discounts)/100
        prices = prices - discountAmount
        colon = "'"
        return '<h5>New Price after coupon: ₹'+str(prices)+'</h5>\
                <button id="Cancel-btn1" onclick="coupon_cancel_load()">Cancel</button><button onclick="document.getElementById('+colon+'Cancel-btn1'+colon+').disabled=true;this.disabled=true;confirmBooking()">Confirm</button>'


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        return render_template('addcoupoun.html')
    name = request.form['cpn_name']
    discount = request.form['cpn_discount']
    last_date = request.form['cpn_date']
    name_extra = request.form['cpn_extra']

    check = CoupounCode.query.filter_by(code=name).first()

    if check:
        return render_template('addcoupoun.html',  message="coupoun already exist")
    else:
        #ml.confirmed = True
        new_ml = CoupounCode(code=name, discount=discount,
                             dates=last_date, extra=name_extra)
        db.session.add(new_ml)
        db.session.commit()
        return redirect(url_for('login'))


@app.route('/insertBooking', methods=['POST'])
def createBooking():
    global prices
    showID = request.form['showID']
    #seatNo = request.form['seatNo']
    #seatClass = request.form['seatClass']
    selected_seats = json.loads(request.form['selected_seats'])
    tickets, tickets_list, comma = '', [], ''
    global category_seats, price
    ticketNo = randint(0, 2147483646)
    showtype = runQuery("Select type from shows where show_id = "+str(showID))
    movielang = runQuery(
        "Select language from movies where movie_id in (select distinct movie_id from shows where show_id = "+str(showID)+")")[0][0]
    res = runQuery(
        "SELECT ticket_no FROM booked_tickets WHERE ticket_no = "+str(ticketNo))
    res1 = runQuery(
        "SELECT ticket_no FROM cancelled_tickets WHERE ticket_no = "+str(ticketNo))
    while res != [] and res1 != []:
        ticketNo = randint(0, 2147483646)
        res = runQuery(
            "SELECT ticket_no FROM booked_tickets WHERE ticket_no = "+str(ticketNo))
        res1 = runQuery(
            "SELECT ticket_no FROM cancelled_tickets WHERE ticket_no = "+str(ticketNo))
    for seat in sorted(list(selected_seats.keys())):
        if 'gold' in seat:
            seatNo = selected_seats[seat] + 1000
            if 'Gold' not in category_seats.keys():
                category_seats['Gold'] = {}
            category_seats['Gold'][selected_seats[seat]] = price*1.5
        else:
            seatNo = selected_seats[seat]
            if 'Standard' not in category_seats.keys():
                category_seats['Standard'] = {}
            category_seats['Standard'][selected_seats[seat]] = price

        #ticketNo = 0
        res = None
        email = session['email']

        res = runQuery("INSERT INTO booked_tickets VALUES(" +
                       str(ticketNo)+","+showID+","+str(seatNo)+",'"+email+"',"+str(prices)+")")

        if res == []:
            tickets = tickets+comma+" "+str(ticketNo)
            # tickets_list.append(ticketNo)
            comma = ','
    # tickets_list,category_seats
    category_seats
    global movieName, movieType, date, time
    email = session['email']
    for i in category_seats.keys():
        category_seats[i] = sorted(list(category_seats[i].keys()))
    # final_seats=[]
    # for i in category_seats.keys():
    #   key_list=sorted(list(category_seats[i].keys()))
    #    for j in key_list:
    #       final_seats.append(str(i))
    #       final_seats.append(str(j))
    #       final_seats.append(str(category_seats[i][j]))
    proper_time = []
    d = str(date)
    date1 = d
    d = d.split("/")
    date = d[2]+"/"+d[1]+"/"+d[0]
    k = int(time)
    temp = k//100
    meridiem = 0
    if(temp == 0):
        temp = 12
    elif(temp >= 12):
        meridiem = 1
        if(temp > 12):
            temp = temp-12
    proper_time.append(temp)
    proper_time.append(k % 100 if k % 100 != 0 else '00')
    proper_time.append(meridiem)

    msg_strr = ''
    msg_strr = ""+str(proper_time[0]) + ":"+str(proper_time[1])+" "
    if(proper_time[2] == 1):
        msg_strr += "PM"
    else:
        msg_strr += "AM"

    final_time = msg_strr

    for i in movieName:
        movie_name = i[1]

    movie = category_seats
    msg_str = []
    for seat_type in movie:
        if(not movie[seat_type] or movie[seat_type] == None):
            pass
        else:
            hyphen = " ("
            seats = str(seat_type)+":"
            #msg_str.append("Type : "+str(seat_type))
            #msg_str.append(str(seat_type)+": ")
            for seat_num in movie[seat_type]:
                seats = seats+hyphen+str(seat_num)
                hyphen = "-"
            msg_str.append(seats+")")
    seat = ('\n'.join(map(str, msg_str)))
    th = runQuery(
        "select name,address from theatre where email in (select distinct email from shows where show_id = "+str(showID)+")")
    #print(movie_name," ",movielang," ",movieType," ",th," ",date," ",proper_time," ",seat," ",ticketNo," ",email," ",prices)
    '''QR Code program start here'''
    res = runQuery("Insert into completed_tickets values("+str(ticketNo)+","+str(showID)+",'"+str(seat)+"', '"+session['email']+"', "+str(
        prices)+", '"+str(movie_name)+" ("+str(movieType)+") ("+str(movielang)+")', '"+str(date1)+"', "+str(time)+", 'Booked')")
    qr_data = (
        f"Ticket Number: {ticketNo}\nMovie Name: {movie_name}\nLanguage: {movielang}\nScreen Type: {movieType}\nTheatre Name: {th[0][0]}\nTheatre Address: {th[0][1]}\n\nDate: {date}\nTime: {final_time}\n\nSeats:\n{seat}\n\nTotal Amount: ₹{prices}")
    qr_code = qrcode.make(qr_data)

    qr_code.save(str(ticketNo)+".jpg")

    msg = Message('Movie Ticket', sender='playpubg34@gmail.com',
                  recipients=[email])
    msg.body = ('Thank you for using MovieFlix! to book your ticket')
    with app.open_resource(str(ticketNo)+".jpg") as movie:
        msg.attach(str(ticketNo)+".jpg", 'image/jpeg', movie.read())
    remove(str(ticketNo)+".jpg")
    mail.send(msg)

    category_seats, price = {}, 0
    movieName, movieType, date, time = None, None, None, None
    return '<h5>Ticket Successfully Booked.\
        Check your mail for QR Code</h5>\
        <button onclick="spinner_load()">Ok</button>'


@app.route('/getShowsShowing', methods=['POST'])
def getShowsShowing():
    #showID = request.form['showID']
    global category_seats
    category_seats = {}
    movie_name = {}
    res = runQuery(
        "SELECT distinct ticket_no,show_id FROM booked_tickets WHERE email = '"+session['email']+"'")
    res1 = runQuery(
        "SELECT distinct ticket_no,show_id FROM cancelled_tickets WHERE email = '"+session['email']+"'")
    if res == [] and res1 == []:
        return '<h5>No Bookings</h5>\
        <button onclick="this.disabled=true;viewCompleteTickets()">View Complete History</button>\
        <button onclick="spinner_load()">Ok</button>'
    l = []
    for i in res:
        q = runQuery("select distinct seat_no from booked_tickets where email = '" +
                     session['email']+"' and ticket_no = "+str(i[0])+" and show_id = "+str(i[1]))
        if str(i[0]) not in category_seats.keys():
            # ticket_number.append(str(i[0]))
            category_seats[str(i[0])] = {}
        for j in q:
            if j[0] > 1000:
                if "Gold" not in category_seats[str(i[0])].keys():
                    category_seats[str(i[0])]['Gold'] = []
                category_seats[str(i[0])]['Gold'].append(j[0]-1000)
                # category.append('gold')
                # seats.append(j[0]-1000)
            else:
                if "Standard" not in category_seats[str(i[0])].keys():
                    category_seats[str(i[0])]['Standard'] = []
                category_seats[str(i[0])]['Standard'].append(j[0])
                # category.append('standard')
                # seats.append(j[0])
        '''print(category_seats)
        category_seats={}
        return "None"'''
        a = runQuery(
            "select date,time,type from shows where show_id = '"+str(i[1])+"'")
        q = runQuery(
            "select movie_name,movie_id,language from movies where movie_id in (select movie_id from shows where show_id = "+str(i[1])+") ")
        movie_name[str(i[0])] = []
        d = str(a[0][0])
        d = d.split("-")
        k = a[0][1]
        temp = k//100
        meridiem = 0
        if(temp == 0):
            temp = 12
        elif(temp >= 12):
            meridiem = 1
            if(temp > 12):
                temp = temp-12
        l.append(temp)
        l.append(k % 100)
        l.append(meridiem)
        '''if i[1] > 1000:
            tickets.append([i[0],q[0][0] ,i[1] - 1000, 'Gold', d, l])
        else:
            tickets.append([i[0],q[0][0] ,i[1], 'Standard', d, l])'''
        movie_name[str(i[0])].append(q[0][0])
        movie_name[str(i[0])].append(d)
        movie_name[str(i[0])].append(l)
        movie_name[str(i[0])].append(q[0][2])
        movie_name[str(i[0])].append(a[0][2])
        movie_name[str(i[0])].append("Booked")
        l = []

    for i in res1:
        q = runQuery("select seat_no from cancelled_tickets where email = '" +
                     session['email']+"' and ticket_no = "+str(i[0])+" and show_id = "+str(i[1]))
        if str(i[0]) not in category_seats.keys():
            # ticket_number.append(str(i[0]))
            category_seats[str(i[0])] = {}
        for j in q:
            if j[0] > 1000:
                if "Gold" not in category_seats[str(i[0])].keys():
                    category_seats[str(i[0])]['Gold'] = []
                category_seats[str(i[0])]['Gold'].append(j[0]-1000)
                # category.append('gold')
                # seats.append(j[0]-1000)
            else:
                if "Standard" not in category_seats[str(i[0])].keys():
                    category_seats[str(i[0])]['Standard'] = []
                category_seats[str(i[0])]['Standard'].append(j[0])
                # category.append('standard')
                # seats.append(j[0])
        '''print(category_seats)
        category_seats={}
        return "None"'''
        a = runQuery(
            "select date,time,type from shows where show_id = '"+str(i[1])+"'")
        q = runQuery(
            "select movie_name,movie_id,language from movies where movie_id in (select movie_id from shows where show_id = "+str(i[1])+") ")
        movie_name[str(i[0])] = []
        d = str(a[0][0])
        d = d.split("-")
        k = a[0][1]
        temp = k//100
        meridiem = 0
        if(temp == 0):
            temp = 12
        elif(temp >= 12):
            meridiem = 1
            if(temp > 12):
                temp = temp-12
        l.append(temp)
        l.append(k % 100)
        l.append(meridiem)
        '''if i[1] > 1000:
            tickets.append([i[0],q[0][0] ,i[1] - 1000, 'Gold', d, l])
        else:
            tickets.append([i[0],q[0][0] ,i[1], 'Standard', d, l])'''
        movie_name[str(i[0])].append(q[0][0])
        movie_name[str(i[0])].append(d)
        movie_name[str(i[0])].append(l)
        movie_name[str(i[0])].append(q[0][2])
        movie_name[str(i[0])].append(a[0][2])
        movie_name[str(i[0])].append("Cancelled")
        l = []
    # print(category_seats)
    for key in category_seats.keys():
        for sub_key in category_seats[key].keys():
            category_seats[key][sub_key].sort()
    for key in category_seats.keys():
        for sub_key in category_seats[key].keys():
            seats = ""
            hyphen = "("
            for i in category_seats[key][sub_key]:
                seats = seats+hyphen+str(i)
                hyphen = "-"
            category_seats[key][sub_key] = seats+")"
    temp = category_seats
    category_seats = {}
    # print(movie_name)
    #OrderedDict((key, value) for key, value in sorted(my_dict.items(), key=lambda x: x[1]['name']))
    movie_name = dict(OrderedDict((key, value) for key, value in sorted(movie_name.items(), key=lambda x: (
        x[1][5], x[1][1][2], x[1][1][1], x[1][1][0], x[1][2][2], x[1][2][0], x[1][2][1]))))
    '''print(movie_name)'''
    return render_template('bookedtickets.html', category_seats=temp, movie_name=movie_name, res=list(res))
    '''tickets=sorted(tickets, key = lambda x: (int(x[4][0]), int(x[4][1]), int(x[4][2]), int(x[5][2]), int(x[5][1]), int(x[5][0])))
    return render_template('showtickets.html', tickets=tickets)'''
    '''tickets = []
    for i in res:
        a=runQuery("select date,time from shows where show_id = '"+str(i[2])+"'")
        q=runQuery("select movie_name from movies where movie_id in (select movie_id from shows where show_id = "+str(i[2])+") ")
        #for j in q:
            #tickets.append(j)
        l=[]
        d=str(a[0][0])
        d=d.split("-")
        k=a[0][1]
        temp=k//100
        meridiem=0
        if(temp==0):
            temp=12
        elif(temp>=12):
            meridiem=1
            if(temp>12):
                temp=temp-12
        l.append(temp)
        l.append(k %100 if k % 100 != 0 else '00')
        l.append(meridiem)
        if i[1] > 1000:
            tickets.append([i[0],q[0][0] ,i[1] - 1000, 'Gold', d, l])
        else:
            tickets.append([i[0],q[0][0] ,i[1], 'Standard', d, l])
        tickets=sorted(tickets, key = lambda x: (int(x[4][0]), int(x[4][1]), int(x[4][2]), int(x[5][2]), int(x[5][1]), int(x[5][0])))

    return render_template('showtickets.html', tickets=tickets)'''


@app.route('/viewticketdetails', methods=['POST'])
def viewticketdetails():
    movie_no = request.form['movie']
    seats = json.loads(request.form['category_seats'])
    movie_name = json.loads(request.form['movie_name'])
    movie_name = movie_name[movie_no]
    seats = seats[movie_no]
    # print(seats)
    if movie_name[2][2] == 0:
        if movie_name[2][0] == 12:
            temph = 0
        else:
            temph = movie_name[2][0]
    else:
        temph = movie_name[2][0]+12
        if temph == 24:
            temph = 12
    if movie_name[2][1] == 0:
        tempm = "00"
    else:
        tempm = movie_name[2][1]
    valid_cancel_time = runQuery('select timediff("'+str(movie_name[1][0])+"/"+str(movie_name[1][1])+"/"+str(
        movie_name[1][2])+" "+str(temph)+":"+str(tempm)+'",convert_tz(now(),"+00:00","+04:00"))>=0')
    if(int(valid_cancel_time[0][0]) == 0):
        cancel_validator = 0
    else:
        cancel_validator = 1
    if "Booked" in movie_name[5]:
        res = runQuery("select * from theatre where email in (select email from shows where show_id in (select distinct show_id from booked_tickets where ticket_no = "+str(movie_no)+"))")
        price = runQuery(
            "select distinct price from booked_tickets where ticket_no = "+str(movie_no))
    else:
        res = runQuery("select * from theatre where email in (select email from shows where show_id in (select distinct show_id from cancelled_tickets where ticket_no = "+str(movie_no)+"))")
        price = runQuery(
            "select distinct price from cancelled_tickets where ticket_no = "+str(movie_no))
    # print(res)
    return render_template('ticketdetails.html', movie_no=movie_no, seats=seats, movie_name=movie_name, res=res[0], price=price[0][0], cancel_validator=cancel_validator)
    #res = runQuery("SELECT distinct show_id FROM booked_tickets WHERE email = '"+session['email']+"' and ticket_no = "+str(movie_no))


@app.route('/cancelask', methods=['POST'])
def ask():
    colon = "'"
    movie_no = request.form['movie_no']
    return '<h4>Are you sure you want to cancel the ticket?</h4>\
        <button id="ccll" onclick="spinner_load()">Go Back</button><button id="coll" onclick="this.disabled=true;document.getElementById('+colon+'ccll'+colon+').disabled=true;confirm_cancel('+str(movie_no)+')">Confirm</button>'


@app.route('/confirm_cancel', methods=['POST'])
def confirm_cancel():
    movie_no = request.form['movie_no']
    res = runQuery(
        'select * from booked_tickets where ticket_no = '+str(movie_no))
    for i in res:
        res1 = runQuery('insert into cancelled_tickets values (' +
                        str(i[0])+','+str(i[1])+','+str(i[2])+',"'+str(i[3])+'",'+str(i[4])+')')
    res2 = runQuery(
        'delete from booked_tickets where ticket_no = '+str(movie_no))
    res3 = runQuery('update completed_tickets set status="Cancelled" where ticket_no = ' +
                    str(movie_no)+' and email = "'+session['email']+'" ')
    return '<h4>Ticket successfully cancelled</h4>\
        <button onclick="spinner_load()">Ok</button>'


@app.route('/send_qr', methods=['POST'])
def send_qr():
    movie_no = request.form['movie']
    seats = json.loads(request.form['category_seats'])
    movie_name = json.loads(request.form['movie_name'])
    movie_price = runQuery(
        "select distinct price from booked_tickets where ticket_no = "+str(movie_no))
    msg_str = []
    for seat_type in seats.keys():
        if(not seats[seat_type] or seats[seat_type] == None):
            pass
        else:
            '''hyphen=" "
            seats=str(seat_type)+":"'''
            #msg_str.append("Type : "+str(seat_type))
            # msg_str.append(str(seat_type)+": ")'''
            '''for seat_num in movie[seat_type]:
                seats=seats+hyphen+str(seat_num)
                hyphen="-"'''
            msg_str.append(seat_type+": "+seats[seat_type])
    seat = ('\n'.join(map(str, msg_str)))
    th = runQuery("select name,address from theatre where email in (select distinct email from shows where show_id in (select distinct show_id from booked_tickets where ticket_no = "+str(movie_no)+"))")
    #print(movie_name," ",movielang," ",movieType," ",th," ",date," ",proper_time," ",seat," ",ticketNo," ",email," ",prices)
    '''QR Code program start here'''
    final_time, minutes = "", ""
    if movie_name[2][1] == 0:
        minutes = "00"
    else:
        minutes = str(movie_name[2][1])
    final_time = str(movie_name[2][0])+":"+minutes
    if movie_name[2][2] == 0:
        final_time = final_time+" AM"
    else:
        final_time = final_time+" PM"
    qr_data = (
        f"Ticket Number: {movie_no}\nMovie Name: {movie_name[0]}\nLanguage: {movie_name[3]}\nScreen Type: {movie_name[4]}\nTheatre Name: {th[0][0]}\nTheatre Address: {th[0][1]}\n\nDate: {movie_name[1][2]}/{movie_name[1][1]}/{movie_name[1][0]}\nTime: {final_time}\n\nSeats:\n{seat}\n\nTotal Amount: ₹{movie_price[0][0]}")
    qr_code = qrcode.make(qr_data)

    qr_code.save(str(movie_no)+".jpg")
    email = session['email']
    msg = Message('Movie Ticket', sender='playpubg34@gmail.com',
                  recipients=[email])
    msg.body = ('Thank you for using MovieFlix! to book your ticket')
    with app.open_resource(str(movie_no)+".jpg") as movie:
        msg.attach(str(movie_no)+".jpg", 'image/jpeg', movie.read())
    remove(str(movie_no)+".jpg")
    mail.send(msg)

    '''category_seats,price={},0
    movieName,movieType,date,time=None,None,None,None'''
    return '<h4>QR Code sent successfully. Please check your mail</h4>\
        <button onclick="spinner_load()">Ok</button>'


@app.route('/getCompleteTickets', methods=['POST'])
def getcompletetickets():
    res = runQuery(
        "Select * from completed_tickets where email = '"+session['email']+"'")
    if res == []:
        return 'No Bookings\
            <button onclick="spinner_load()">Ok</button>'
    for i in range(len(res)):
        res[i] = list(res[i])
    res.reverse()
    for i in res:
        proper_time = []
        d = str(i[6])
        # date1=d
        d = d.split("-")
        date = d[2]+"/"+d[1]+"/"+d[0]
        k = int(i[7])
        temp = k//100
        meridiem = 0
        if(temp == 0):
            temp = 12
        elif(temp >= 12):
            meridiem = 1
            if(temp > 12):
                temp = temp-12
        proper_time.append(temp)
        proper_time.append(k % 100 if k % 100 != 0 else '00')
        proper_time.append(meridiem)

        msg_strr = ''
        msg_strr = ""+str(proper_time[0]) + ":"+str(proper_time[1])+" "
        if(proper_time[2] == 1):
            msg_strr += "PM"
        else:
            msg_strr += "AM"

        final_time = msg_strr
        i[6] = date
        i[7] = final_time
    return render_template("completetickets.html", tickets=res)


@app.route('/changepincode', methods=['POST'])
def changepincode():
    state = {}
    res = runQuery("select distinct state,district from indian_pincodes")
    for i in res:
        if i[0] not in state.keys():
            state[i[0]] = []
        #res1=runQuery("select district from indian_pincodes where state = '"+str(i[0])+"'")
        # for j in res1:
        # for j in i[1]:
        state[i[0]].append(i[1].capitalize())
    for i in state.keys():
        state[i] = sorted(state[i])
    # print(state)
        # state[i[0]]=[]
    #res=runQuery("select distinct district from indian_pincodes")
    # for i in res:
    return render_template('select_state.html', states=sorted(state.keys()), cities=state)


@app.route('/change_city', methods=['POST'])
def change_city():
    state = request.form['state']
    city = request.form['city']
    print(state, " ", city)
    if "Select" in state or state == '':
        return '<h4>No state selected</h4>\
            <button onclick="spinner_load()">Ok</button>'
    elif "Select" in city or city == '':
        return '<h4>No city selected</h4>\
            <button onclick="spinner_load()">Ok</button>'
    else:
        runQuery('update user set city = "'+city+'", state = "' +
                 state+'" where email = "'+session['email']+'"')
        session['city'] = city
        session['state'] = state
        #print(runQuery('select * from user where email="'+session['email']+'"'))
        return '<h4>City Updated Successfully</h4>\
            <button onclick="spinner_load()">Ok</button>'


'''@app.route('/call_city',methods=['POST'])
def call_city():
    state=request.form['state']
    res=runQuery('select distinct district from indian_pincodes where state = "'+str(state)+'"')
    cities=[]
    for i in res:
        cities.append(i[0].capitalize())
    return render_template('select_city.html',cities=sorted(cities))'''


@app.route('/change_pincode', methods=['POST'])
def change_pincode():
    pincode = request.form['pincode']
    if(len(str(pincode)) == 6):
        res = runQuery(
            'select division_name,district from indian_pincodes where pincode = '+str(pincode))
        if res == []:
            return '<h4>No proper Pincode provided</h4>\
            <button onclick="spinner_load()">Ok</button>'
        res1 = runQuery('update user set pincode='+str(pincode) +
                        ' where email="'+session['email']+'"')
        session['division_name'] = res[0][0]
        session['district'] = res[0][1]
        return '<h4>Pincode changed successfully</h4>\
        <button onclick="spinner_load()">Ok</button>'
    else:
        return '<h4>No proper Pincode provided</h4>\
        <button onclick="spinner_load()">Ok</button>'

# Routes for manager


@app.route('/getShowsShowingOnDate', methods=['POST'])
def getShowsOnDate():
    date = request.form['date']
    # division_name=session['division_name']
    # district=session['district']
    Query = []
    res = runQuery("SELECT show_id,type,time FROM shows WHERE email='" +
                   session['email']+"' and Date = '"+date+"'")

    if res == []:
        return '<h4>No Shows Showing</h4>\
        <button onclick="spinner_load()">Ok</button>'
    else:
        shows = []
        for i in res:
            q = runQuery(
                "select movie_name,language from movies where movie_id in (select distinct movie_id from shows where show_id = "+str(i[0])+")")
            # for i in res:
            l = []
            k = i[2]
            temp = k//100
            meridiem = 0
            if(temp == 0):
                temp = 12
            elif(temp >= 12):
                meridiem = 1
                if(temp > 12):
                    temp = temp-12
            l.append(temp)
            l.append(k % 100 if k % 100 != 0 else '00')
            l.append(meridiem)
            '''x = i[2] % 100
            if i[2] % 100 == 0:
                x = '00' '''
            shows.append([i[0], q[0][0], i[1], l, q[0][1]])
        shows = sorted(shows, key=lambda x: (x[3][2], x[3][0], int(x[3][1])))
        return render_template('shows.html', shows=shows)


@app.route('/getBookedWithShowID', methods=['POST'])
def getBookedTickets():
    showID = request.form['showID']

    res = runQuery(
        "SELECT distinct ticket_no FROM booked_tickets WHERE show_id = "+str(showID)+" order by seat_no")
    res1 = runQuery(
        "SELECT distinct ticket_no FROM cancelled_tickets WHERE show_id = "+str(showID)+" order by seat_no")
    if res == [] and res1 == []:
        return '<h5>No Bookings</h5>\
        <button onclick="spinner_load()">Ok</button>'
    tickets = {}
    emails = {}
    status = {}
    for i in res:
        if i[0] not in tickets.keys():
            tickets[str(i[0])] = {}
        q = runQuery("select seat_no,email from booked_tickets where show_id = " +
                     str(showID)+" and ticket_no = "+str(i[0]))
        for j in q:
            if j[0] > 1000:
                if "Gold" not in tickets[str(i[0])].keys():
                    tickets[str(i[0])]['Gold'] = []
                tickets[str(i[0])]['Gold'].append(j[0]-1000)
            else:
                if "Standard" not in tickets[str(i[0])].keys():
                    tickets[str(i[0])]['Standard'] = []
                tickets[str(i[0])]['Standard'].append(j[0])
            emails[str(i[0])] = j[1]
            status[str(i[0])] = "Booked"
    for i in res1:
        if i[0] not in tickets.keys():
            tickets[str(i[0])] = {}
        q = runQuery("select seat_no,email from cancelled_tickets where show_id = " +
                     str(showID)+" and ticket_no = "+str(i[0]))
        for j in q:
            if j[0] > 1000:
                if "Gold" not in tickets[str(i[0])].keys():
                    tickets[str(i[0])]['Gold'] = []
                tickets[str(i[0])]['Gold'].append(j[0]-1000)
            else:
                if "Standard" not in tickets[str(i[0])].keys():
                    tickets[str(i[0])]['Standard'] = []
                tickets[str(i[0])]['Standard'].append(j[0])
            emails[str(i[0])] = j[1]
            status[str(i[0])] = "Cancelled"
    for key in tickets.keys():
        for sub_key in tickets[key].keys():
            tickets[key][sub_key].sort()
    for key in tickets.keys():
        for sub_key in tickets[key].keys():
            hyphen = ""
            seats_book = ""
            for i in tickets[key][sub_key]:
                seats_book = seats_book+hyphen+str(i)
                hyphen = "-"
            tickets[key][sub_key] = seats_book
    # print(tickets,emails)
    return render_template('bookedticketsmanager.html', tickets=tickets, emails=emails, status=status)

    '''tickets = []
    for i in res:
        if i[1] > 1000:
            tickets.append([i[0], i[1] - 1000, 'Gold'])
        else:
            tickets.append([i[0], i[1], 'Standard'])

    return render_template('bookedtickets.html', tickets=tickets)'''


@app.route('/fetchMovieInsertForm', methods=['GET'])
def getMovieForm():
    return render_template('movieform.html')


@app.route('/insertMovie', methods=['POST'])
def insertMovie():
    movieName = request.form['movieName']
    movieLen = request.form['movieLen']
    movieLang = request.form['movieLang'].capitalize()
    types = request.form['types'].upper()
    startShowing = request.form['startShowing']
    endShowing = request.form['endShowing']
    # print(division_name)
    res = runQuery('SELECT * FROM movies where state = "' +
                   session['state']+'" and city = "'+session['city']+'"')

    for i in res:
        if i[1] == movieName and i[2] == int(movieLen) and i[3] == movieLang \
                and i[4].strftime('%Y/%m/%d') == startShowing and i[5].strftime('%Y/%m/%d') == endShowing:
            return '<h5>The Exact Same Movie Already Exists</h5>\
            <button onclick="spinner_load()">Ok</button>'

    movieID = 0
    res = None

    while res != []:
        movieID = randint(0, 2147483646)
        res = runQuery(
            "SELECT movie_id FROM movies WHERE movie_id = "+str(movieID))

    res = runQuery("INSERT INTO movies VALUES("+str(movieID)+",'"+movieName+"',"+movieLen +
                   ",'"+movieLang+"','"+startShowing+"','"+endShowing+"','"+session['city']+"','"+session['state']+"')")
    if res == []:
        #print("Was able to add movie")
        subTypes = types.split(' ')

        while len(subTypes) < 3:
            subTypes.append('NUL')

        res = runQuery("INSERT INTO types VALUES("+str(movieID) +
                       ",'"+subTypes[0]+"','"+subTypes[1]+"','"+subTypes[2]+"')")

        if res == []:
            return '<h5>Movie Successfully Added</h5>\
			<h6>Movie ID: '+str(movieID)+'</h6>\
            <button onclick="spinner_load()">Ok</button>'
        else:
            print(res)
    else:
        print(res)

    return '<h5>Something Went Wrong</h5>'


@app.route('/getValidMovies', methods=['POST'])
def validMovies():
    showDate = request.form['showDate']
    '''date_given = request.form['date']
    print(date_given)
    y,m,d=(int(x) for x in showDate.split('/'))
    date_given=datetime.date(y,m,d)
    print(date_given.strftime("%A"))'''
    # division_name=session['division_name']

    res = runQuery("SELECT movie_id,movie_name,length,language, show_start, show_end FROM movies WHERE show_start <= '"+showDate +
                   "' and show_end >= '"+showDate+"' and state = '"+session['state']+"' and city = '"+session['city']+"'")

    if res == []:
        return '<h5>No Movies Available for Showing On Selected Date</h5>\
            <button onclick="spinner_load()">Ok</button>'

    movies = []

    for i in res:
        subTypes = runQuery("SELECT * FROM types WHERE movie_id = "+str(i[0]))

        t = subTypes[0][1]

        if subTypes[0][2] != 'NUL':
            t = t + ' ' + subTypes[0][2]
        if subTypes[0][3] != 'NUL':
            t = t + ' ' + subTypes[0][3]
        date1 = str(i[4]).split('-')
        date2 = str(i[5]).split('-')

        movies.append((i[0], i[1], t, i[2], i[3], date1[2]+"/" +
                      date1[1]+"/"+date1[0], date2[2]+"/"+date2[1]+"/"+date2[0]))

    return render_template('validmovies.html', movies=movies)


@app.route('/getHallsAvailable', methods=['POST'])
def getHalls():
    movieID = request.form['movieID']
    showDate = request.form['showDate']
    showTime = request.form['showTime']

    res = runQuery("SELECT length FROM movies WHERE movie_id = "+movieID)

    movieLen = res[0][0]

    showTime = int(showTime)

    showTime = int(showTime / 100)*60 + (showTime % 100)

    endTime = showTime + movieLen
    # division_name=session['division_name']
    email = session['email']
    res = runQuery("SELECT hall_id, time FROM shows NATURAL JOIN movies WHERE Date = '" +
                   showDate+"' and email = '"+email+"'")

    unavailableHalls = set()

    for i in res:

        x = int(i[1] / 100)*60 + (i[1] % 100)

        y = x + movieLen

        if x >= showTime and x <= endTime:
            unavailableHalls = unavailableHalls.union({i[0]})

        if y >= showTime and y <= endTime:
            unavailableHalls = unavailableHalls.union({i[0]})

    res = runQuery(
        "SELECT DISTINCT hall_id FROM halls where email = '"+email+"'")

    availableHalls = set()

    for i in res:

        availableHalls = availableHalls.union({i[0]})

    availableHalls = availableHalls.difference(unavailableHalls)

    if availableHalls == set():

        return '<h5>No Halls Available On Given Date And Time</h5>\
            <button onclick="spinner_load()">Ok</button>'

    return render_template('availablehalls.html', halls=availableHalls)


@app.route('/insertShow', methods=['POST'])
def insertShow():
    hallID = request.form['hallID']
    movieID = request.form['movieID']
    movieType = request.form['movieType']
    showDate = request.form['showDate']
    showTime = request.form['showTime']
    #date_given = request.form['date']
    # print(date_given)
    y, m, d = (int(x) for x in showDate.split('/'))
    date_given = datetime.date(y, m, d)
    print(date_given.strftime("%A"))

    showID = 0
    res = None

    while res != []:
        showID = randint(0, 2147483646)
        res = runQuery(
            "SELECT show_id FROM shows WHERE show_id = "+str(showID))
    email = session['email']
    res1 = runQuery("select price_id from price_listing where day = '"+str(
        date_given.strftime("%A"))+"' and email = '"+email+"' and type = '"+str(movieType)+"'")
    res = runQuery("INSERT INTO shows(show_id,movie_id,hall_id,type,time,date,price_id,email) VALUES("+str(showID)+","+movieID+","+hallID +
                   ",'"+movieType+"',"+showTime+",'"+showDate+"',"+str(res1[0][0])+",'"+email+"')")

    # print(res)

    if res == []:
        return '<h5>Show Successfully Scheduled</h5>\
		<h6>Show ID: '+str(showID)+'</h6>\
        <button onclick="spinner_load()">Ok</button>'

    else:
        print(res)
    return '<h5>Something Went Wrong</h5>'


@app.route('/getPriceList', methods=['GET'])
def priceList():
    email = session['email']
    res = runQuery("SELECT * FROM price_listing where email = '" +
                   email+"' ORDER BY type")

    sortedDays = ['Sunday', 'Monday', 'Tuesday',
                  'Wednesday', 'Thursday', 'Friday', 'Saturday']

    res = sorted(res, key=lambda x: sortedDays.index(x[2]))

    return render_template('currentprices.html', prices=res)


@app.route('/setNewPrice', methods=['POST'])
def setPrice():
    priceID = request.form['priceID']
    newPrice = request.form['newPrice']
    email = session['email']

    res = runQuery("UPDATE price_listing SET price = " +
                   str(newPrice)+" WHERE price_id = "+str(priceID)+" and email = '"+email+"'")

    if res == []:
        return '<h5>Price Successfully Changed</h5>\
			<h6>Standard: ₹ '+newPrice+'</h6>\
			<h6>Gold: ₹ '+str(int(int(newPrice) * 1.5))+'</h6>\
            <button onclick="spinner_load()">Ok</button>'

    else:
        print(res)
    return '<h5>Something Went Wrong</h5>'


def runQuery(query):
    try:
        db = mysql.connector.connect(
            host='database-1.caqypwmxgqo6.us-east-1.rds.amazonaws.com',
            port=3306,
            database='theatres',
            user='admin',
            password='adminwebapp')

        if db.is_connected():
            print("Connected to MySQL, running query: ", query)
            cursor = db.cursor(buffered=True)
            cursor.execute(query)
            db.commit()
            res = None
            try:
                res = cursor.fetchall()
            except Exception as e:
                print("Query returned nothing, ", e)
                return []
            return res

    except Exception as e:
        print(e)
        return e

    finally:
        db.close()

    print("Couldn't connect to MySQL")
    # Couldn't connect to MySQL
    return None


admin = Admin(app)
admin.add_view(ModelView(User, db.session))
#admin.add_view(ModelView(Super, db.session))
admin.add_view(ModelView(Mgr, db.session))
admin.add_view(ModelView(Theatre, db.session))
admin.add_view(ModelView(CoupounCode, db.session))
if __name__ == "__main__":
    app.run(debug=True, port=3434)
