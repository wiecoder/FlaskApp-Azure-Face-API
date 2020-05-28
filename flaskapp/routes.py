import os
import json
import secrets
import requests
import time
from collections import Counter
from PIL import Image
from flask import render_template, url_for, flash,redirect, request, abort
from flaskapp import app, db, bcrypt
from flaskapp.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, BlockForm
from flaskapp.models import User, Post, Block
from flask_login import login_user, current_user, logout_user, login_required

db.create_all()

@app.route("/")
def base():
    return render_template('base.html')

@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html',posts=posts)

@app.route("/pomodoro")
def pomodoro():
    style='pomodoro'
    return render_template('pomodoro.html',title='about', style=style)

@app.route("/camera")
def camera():
    return render_template('camera.html', title='camera')

@app.route("/tips")
def tips():
    return render_template('tips.html', title='tips')

@app.route("/register", methods=["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!','success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)

@app.route("/login", methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful - check email and password', 'danger')
    return render_template('login.html',title='Login',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics',picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route('/account', methods=["GET","POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route('/post/new',methods=["GET","POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author = current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend = 'New Post')

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route('/post/<int:post_id>/update',methods=["GET","POST"])
@login_required
def update_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend = 'Update Post')


@app.route('/post/<int:post_id>/delete',methods=["POST"])
@login_required
def delete_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html',posts=posts, user=user)

### FACE API
subscription_key = 'c5a2dd0e0f474af294c630bb8a463176'
assert subscription_key

face_api_url = 'https://ailionsfaceapi.cognitiveservices.azure.com/face/v1.0/detect'

headers = {
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': subscription_key,
}

params = {
    'returnFaceId': 'true',
    'returnFaceLandmarks': 'false',
    'returnFaceAttributes': 'age,gender,smile,emotion',
}

def face_recognition(image_url):
    response = requests.post(face_api_url,params=params, headers=headers, data=image_url)
    return response.json()[0]

def save_picture_normal(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/block_pics',picture_fn)
    form_picture.save(picture_path)
    return picture_fn

@app.route('/new/block', methods=["GET","POST"])
@login_required
def new_block():
    form = BlockForm()
    if form.validate_on_submit():
        picture_file=save_picture_normal(form.picture.data)
        image_path = app.root_path + url_for('static', filename='block_pics/' + picture_file)
        with open(image_path, 'rb') as f:
            img_data = f.read()
        emotion = face_recognition(img_data)
        block = Block(title=form.title.data, content=form.content.data, session=form.session.data, image_file=picture_file, output=emotion,author = current_user)
        db.session.add(block)
        db.session.commit()        
        flash('Block has been created!', 'success')
        return redirect(url_for('blocks'))
    return render_template('create_block.html', title='New Block', form=form, legend='New Block')


@app.route("/blocks")
def blocks():
    # blocks = Block.query.all()
    page = request.args.get('page', 1, type=int)
    blocks = Block.query.order_by(Block.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('blocks.html', blocks=blocks)

@app.route("/block/<int:block_id>")
def block(block_id):
    block=Block.query.get_or_404(block_id)
    return render_template('block.html',title=block.title,block=block)

@app.route('/block/<int:block_id>/delete',methods=["POST"])
@login_required
def delete_block(block_id):
    block=Block.query.get_or_404(block_id)
    if block.author != current_user:
        abort(403)
    db.session.delete(block)
    db.session.commit()
    flash('Your block has been deleted!', 'success')
    return redirect(url_for('blocks'))

def all_times(blocks):
    dts=[]
    for block in blocks:
        dts.append(block.date_posted.strftime('%H:%M') )
    return dts

@app.route("/stats")
def stats():
    all_blocks = Block.query.order_by(Block.date_posted.desc())
    times=all_times(all_blocks)
    return render_template('stats.html',all_blocks=all_blocks, times=times)



