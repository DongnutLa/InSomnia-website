import logging

from flask import abort, render_template, request, current_app, redirect, url_for, jsonify, flash
from werkzeug.exceptions import NotFound
from flask_login import current_user, login_required
from .forms import CommentForm, ExchangeForm
from app.models import Post, Comment
from app.dreamcatcher.models import PhotocardDb, PhotocardExchange, Album, AlbumType, Members
from app.auth.models import User
from app.auth.decorators import email_confirm_required
from app.common.mail import send_email
from . import public_bp

logger = logging.getLogger(__name__)

@public_bp.route("/")
def index():
    logger.info('Mostrando la página principal')
    page = int(request.args.get('page', 1))
    per_page = current_app.config['ITEMS_PER_PAGE']
    post_pagination = Post.all_paginated(page, per_page)
    
    return render_template("public/index.html", post_pagination=post_pagination)

@public_bp.route("/p/<string:slug>/", methods=['GET', 'POST'])
def show_post(slug):
    logger.info('Mostrando un post')
    logger.debug(f'Slug: {slug}')
    post = Post.get_by_slug(slug)
    if not post:
        logger.info(f'El post {slug} no existe')
        abort(404)
    form = CommentForm()
    if current_user.is_authenticated and form.validate_on_submit():
        content = form.content.data
        comment = Comment(content=content, user_id=current_user.id,
                          user_username=current_user.username, post_id=post.id)
        comment.save()
        return redirect(url_for('public.show_post', slug=post.title_slug))
    return render_template("public/post_view.html", post=post, form=form)

@public_bp.route("/photocards/", methods=['GET', 'POST'])
def list_photocards():
    photocards = PhotocardDb.get_all()
    albums = PhotocardDb.get_albums()
    pc_types = PhotocardDb.get_type()
    return render_template("public/photocards.html", photocards=photocards, albums=albums, pc_types=pc_types)

@public_bp.route("/albums/")
def list_albums():
    albums = Album.get_all()
    return render_template("public/albums.html", albums=albums)

@public_bp.route("/exchange/", methods=['GET', ])
def show_exchange():
    exchanges = PhotocardExchange.get_all()
    return render_template("public/exchange_view.html", exchanges=exchanges)

@public_bp.route("/exchange/create/", methods=['GET', 'POST'])
@login_required
@email_confirm_required
def exchange_form():
    # Crea un nuevo post
    form = ExchangeForm()

    form.album_from.choices = [(albums.album, albums.album) for albums in Album.get_all()]
    form.album_from.choices.insert(0, ("", "Seleccione"))
    form.album_to.choices = [(albums.album, albums.album) for albums in Album.get_all()]
    form.album_to.choices.insert(0, ("", "Seleccione"))

    form.pc_type_from.choices = [(pc_type.pc_type, pc_type.pc_type) for pc_type in AlbumType.get_all()]
    form.pc_type_from.choices.insert(0, ("", "Seleccione"))
    form.pc_type_to.choices = [(pc_type.pc_type, pc_type.pc_type) for pc_type in AlbumType.get_all()]
    form.pc_type_to.choices.insert(0, ("", "Seleccione"))

    form.member_from.choices = [(member.name, member.name) for member in Members.get_all()]
    form.member_from.choices.insert(0, ("", "Seleccione"))
    form.member_to.choices = [(member.name, member.name) for member in Members.get_all()]
    form.member_to.choices.insert(0, ("", "Seleccione"))

    if form.validate_on_submit():
        album_from = form.album_from.data
        member_from = form.member_from.data
        pc_type_from = form.pc_type_from.data
        album_to = form.album_to.data
        member_to = form.member_to.data
        pc_type_to = form.pc_type_to.data

        # Consultas
        album_f = Album.get_by_album(album_from)
        album_t = Album.get_by_album(album_to)
        member_f = Members.get_by_name(member_from)
        member_t = Members.get_by_name(member_to)
        pc_type_f = AlbumType.get_by_type(pc_type_from)
        pc_type_t = AlbumType.get_by_type(pc_type_to)

        pc_from = PhotocardDb.get_filtered(album_f.id, pc_type_f.id, member_f.id)
        pc_to = PhotocardDb.get_filtered(album_t.id, pc_type_t.id, member_t.id)

        exchange = PhotocardExchange(user_id=current_user.id)
        exchange.pc_from.append(pc_from)
        exchange.pc_to.append(pc_to)
        print(exchange.pc_from)
        print(exchange.pc_to)
        exchange.save()
        logger.info(f'Guardando nueva entrada photocardExchange')
        flash('¡Yujuuu, has creado un nuevo trade!')
        flash('Pronto llegará gente interesada en tu trade ;)')
        return redirect(url_for('public.show_exchange'))
    return render_template("public/post_exchange.html", form=form)

@public_bp.route("/exchange/me-interesa/<exchange_id>/<user_id>", methods=['GET', 'POST'])
def interested_exchange(user_id, exchange_id):
    user = User.get_by_id(user_id)
    exchange = PhotocardExchange.get_by_id(exchange_id)
    exchange.users_interested.append(user)
    exchange.save()
    return redirect(url_for('public.show_exchange'))

@public_bp.route("/exchange/no-me-interesa/<exchange_id>/<user_id>", methods=['GET', 'POST'])
def not_interested_exchange(user_id, exchange_id):
    user = User.get_by_id(user_id)
    exchange = PhotocardExchange.get_by_id(exchange_id)
    exchange.users_interested.remove(user)
    exchange.save()
    return redirect(url_for('public.show_exchange'))

@public_bp.route("/exchange/delete/<int:exchange_id>", methods=['GET', 'POST'])
def delete_exchange(exchange_id):
    exchange = PhotocardExchange.get_by_id(exchange_id)
    if exchange.user_id != current_user.id:
        abort(403)
    else:
        exchange.delete()
        flash('¡Ohh, tu trade ha sido borrado!')
    return redirect(url_for('public.show_exchange'))

@public_bp.route("/contact_us/", methods=['POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('nombre')
        email = request.form.get('email')
        subject = request.form.get('asunto')
        message = request.form.get('mensaje')

        print('correo: ', email)
        print('nombre: ', name)
        print('asunto: ', subject)
        print('mensaje: ', message)

        send_email(subject = 'Contacto Insomnia Colombia',
            sender=current_app.config['DONT_REPLY_FROM_EMAIL'],
            recipients=[email, ],
            text_body=f'Hola {name}, recibimos tu mensaje.',
            html_body=f'<p>Hola {name}, recibimos tu mensaje.</p><p>A continuación verás una copia de tu mensaje:</p><br><hr><br>   <h4>Nombre: {name}</h4> <h4>Correo: {email}</h4> <h4>Asunto: {subject}</h4> <h4>Mensaje:</h4> <p>{message}</p>')

        send_email(subject = 'Contact Us Form',
                sender=current_app.config['DONT_REPLY_FROM_EMAIL'],
                recipients=[current_app.config['MAIL_USERNAME'], ],
                text_body=f'{name} envió un mensaje.',
                html_body=f'<p>¡Ha llegado un nuevo mensaje desde el formulario de contacto!</p><br><hr><br><h4>Nombre: {name}</h4> <h4>Correo: {email}</h4> <h4>Asunto: {subject}</h4> <h4>Mensaje:</h4> <p>{message}</p>')
        flash('¡Listo, hemos recibido tu mensaje!')
        flash('A ' + str(email) + ' llegará un mensaje de confirmación de tu mensaje')
    return redirect(url_for('public.index'))

# Jsonify
@public_bp.route("/list_interested/<exchangeId>/")
def list_interested(exchangeId):
    exchanges = PhotocardExchange.get_all()
    usersArray = []
    for exchange in exchanges:
        for user in exchange.users_interested:
            if (exchange.id == int(exchangeId)):
                usersObj = {}
                usersObj['username'] = user.username
                usersObj['city'] = user.city.name
                usersObj['tel'] = str(user.phone)
                usersArray.append(usersObj)
    print(usersArray)
    return jsonify({'users' : usersArray})