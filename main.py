from flask import Flask,render_template,url_for,redirect,request,flash
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from flask_wtf import FlaskForm
from wtforms import FileField,StringField,PasswordField,SubmitField,validators,BooleanField
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 
from flask_uploads import configure_uploads,IMAGES,UploadSet
from tensorflow.keras.backend import manual_variable_initialization 
manual_variable_initialization(True)
import cv2
from werkzeug.exceptions import HTTPException
from tensorflow.keras.models import load_model
import numpy as np
from flask_login import LoginManager,UserMixin,login_user,logout_user,current_user





#forms - 


class MyForm(FlaskForm):
	image=FileField("image")
	username=StringField(label='Patient Name',validators=[validators.DataRequired()])


class RegisterForm(FlaskForm):
	username=StringField(label='Username',validators=[validators.DataRequired()])
	email=StringField(label='Email',validators=[validators.DataRequired(),validators.Email()])
	password=PasswordField(label='Password',validators=[validators.DataRequired()])
	confirm_password=PasswordField(label='Confirm Password',validators=[validators.EqualTo('confirm_password')])
	submit=SubmitField(label='Submit')


class LoginForm(FlaskForm):
	username=StringField(label='Username',validators=[validators.DataRequired()])
	password=PasswordField(label='Password',validators=[validators.DataRequired()])
	remember_me=BooleanField(label='remember_me')
	submit=SubmitField(label='Submit')
	



	
#forms end--- 


#utility function 
def handle_errors(password,confirm_password,username,email):
	if len(Users.query.filter_by(username=username).all())!=0:
		return 'Error Username Already Exists',False
	if password!=confirm_password:
		return 'Password Fields Dont Match ',False

	if len(Users.query.filter_by(email_id=email).all())!=0:
		return 'Error Email Already Exists',False

	else:
		return "Success",True


def handle_login(password,username):
	if len(Users.query.filter_by(username=username).all())==0:
		return 'Error  Username Does Not Exist',False
	user=Users.query.filter_by(username=username).all()[0]
	if user.password!=password:
		return 'Wrong Password Try Again !',False

	return 'Success',True


#utlity end




app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///users.db"

db=SQLAlchemy(app)

login_manager=LoginManager(app)



class Users(db.Model,UserMixin):
	id=db.Column(db.Integer,primary_key=True)
	username=db.Column(db.String(20),unique=True,nullable=False)
	email_id=db.Column(db.String(120),unique=True,nullable=False)
	password=db.Column(db.String(20),nullable=False)
	results=db.relationship('Results',backref='author',lazy=True)


	def __repr__(self):
		return f'username : {self.username} , email: {self.email_id}, password: {self.password}'

class Results(db.Model):
	id=db.Column(db.Integer,primary_key=True)
	patient_name=db.Column(db.String(20),nullable=False)
	date=db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
	user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
	prediction=db.Column(db.String())

	def __repr__(self):
		return f'pateint : {self.patient_name} , date: {self.date}'



@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))









app.config['SECRET_KEY']='PASS'
app.config['UPLOADED_IMAGES_DEST']='static/images'

images=UploadSet('images',IMAGES)

configure_uploads(app,images)


@app.route("/home",methods=['GET','POST'])
def home_page():
	home=True
	form=MyForm()
	if request.method=='POST':
		patient_name=form.username.data

		if len(patient_name)==0:
			flash("Patient Name is Required",'danger')
			return redirect('home_page')

		file_name=images.save(form.image.data)
		subpath='static/images'
		final_path=subpath+'/'+file_name
		image=cv2.imread(final_path)

		model=load_model('model.h5')



		prediction=model.predict_classes(np.array([image/255.0]))[0][0]


		if prediction==1:
			prediction='It is likely that the tissue shown has signs of cancer'

			flash('Cancer Detected in Cell','danger')
		else:
			prediction='Good News !! The cell appears to be NON-Cancerous'
			flash('Cancer Not Detected in Cell','success')
		result=Results(patient_name=patient_name,user_id=current_user.id,prediction=prediction)
		db.session.add(result)
		db.session.commit()
		return redirect(url_for('results',pred=prediction))
	return render_template('home.html',title='home page',form=form,home=home)

@app.route("/about")
def about():
	return render_template('about.html',title='about page')



@app.route('/result')
def results():
  return render_template("results.html",
	  prediction=request.args.get('pred'))



@app.route('/register',methods=['POST','GET'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home_page'))



	form=RegisterForm()

	if request.method=='POST':
		message,resp=handle_errors(form.password.data,form.confirm_password.data,form.username.data,form.email.data)

		if resp==False:
			flash(message,'danger')
			return redirect('register')

		else:
			User=Users(username=form.username.data,email_id=form.email.data,password=form.password.data)
			db.session.add(User)
			db.session.commit()
			flash(message,'success')
			return redirect(url_for('login')) 		
	return render_template('register.html',form=form)



@app.route('/login',methods=['POST','GET'])
def login():

	if current_user.is_authenticated:
		return redirect(url_for('home_page'))

	form=LoginForm()

	if request.method=='POST':
		username=form.username.data
		password=form.password.data
		message,resp=handle_login(password,username)

		if not resp:
			flash(message,'danger')
			return redirect(url_for('login'))
		else:
			flash(message,'success')
			user=Users.query.filter_by(username=username).all()[0]
			login_user(user,form.remember_me.data)
			return redirect(url_for('home_page'))

	return render_template('login.html',form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home_page'))



@app.route('/showresults')
def showresluts():
	if current_user.is_authenticated:
		id=current_user.id

		user=Users.query.filter_by(id=id).all()[0]

		

		return render_template('showresults.html',results=user.results)


	else:
		return redirect(url_for('home_page'))



if __name__=='__main__':
	app.run(debug=True)





