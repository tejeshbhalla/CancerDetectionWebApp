from flask import Flask,render_template,url_for,redirect,request
from flask_wtf import FlaskForm
from wtforms import FileField

from flask_uploads import configure_uploads,IMAGES,UploadSet
import cv2
from werkzeug.exceptions import HTTPException
from tensorflow.keras.models import load_model
import numpy as np


class MyForm(FlaskForm):
	image=FileField("image")




app=Flask(__name__)


app.config['SECRET_KEY']='PASS'
app.config['UPLOADED_IMAGES_DEST']='static/images'

images=UploadSet('images',IMAGES)

configure_uploads(app,images)


@app.route("/home",methods=['GET','POST'])
def home_page():
	form=MyForm()
	if form.validate_on_submit():
		file_name=images.save(form.image.data)
		subpath='static/images'
		final_path=subpath+'/'+file_name
		image=cv2.imread(final_path)
		image=cv2.resize(src=image,dsize=(50,50),interpolation=cv2.INTER_CUBIC)
		print(image.shape)
		model=load_model('model.h5')

		prediction=model.predict_classes(np.array([image]))[0][0]

		if prediction==1:
			prediction='It is likely that the tissue shown has signs of cancer'
		else:
			prediction='Good News !! The cell appears to be NON-Cancerous'
		return redirect(url_for('results',pred=prediction))
	return render_template('home.html',title='home page',form=form)


@app.route("/about")
def about():
	return render_template('about.html',title='about page')



@app.route('/result')
def results():
  return render_template("results.html",
      prediction=request.args.get('pred'))


    

if __name__=='__main__':
	app.run(debug=True)