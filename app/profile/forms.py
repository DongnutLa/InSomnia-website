from flask import current_app
from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.core import SelectField, SelectMultipleField, StringField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import DataRequired, Email, Length

class AddProfilePic(FlaskForm):
    profile_pic = FileField('Foto de perfil', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Sólo se permiten imágenes'), DataRequired()
    ])
    submit = SubmitField('Subir')

class AddAlbums(FlaskForm):
    albums = SelectMultipleField('Agregar álbumes', choices=[])
    submitA = SubmitField('Guardar')

class AddPhotocards(FlaskForm):
    album = SelectField('Seleccione álbum', choices=[])
    album_type = SelectField('Seleccione la versión de photocard', choices=[])
    members = SelectMultipleField('Seleccione las miembros', choices=[])
    submitP = SubmitField('Guardar')

class EditPersonalInfo(FlaskForm):    
    name = StringField('Nombres', validators=[DataRequired(), Length(max=64)])
    lastname = StringField('Apellidos', validators=[DataRequired(), Length(max=64)])
    city = SelectField('Ciudad', choices=[], validators=[DataRequired()])
    phone = StringField('Celular', validators=[DataRequired(), Length(min=10,max=10,message="El número de celular debe ser de 10 dígitos")])
    birthday = DateField('Fecha de nacimiento', format='%Y-%m-%d', validators=[DataRequired()])
    bias = SelectMultipleField('Bias', choices=[], validators=[DataRequired()])
    facebook = StringField('Usuario de facebook')
    twitter = StringField('Usuario de Twitter')
    instagram = StringField('Usuario de Instagram')
    submitI = SubmitField('Guardar')