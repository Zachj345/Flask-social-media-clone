from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super secret'
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


'''DATABASES'''


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(111), nullable=False, unique=True)
    username = db.Column(db.String(111), nullable=False, unique=True)
    password = db.Column(db.String(111), nullable=False)
    posts = db.relationship('Post', cascade='all, delete, delete-orphan',
                            backref='user', lazy=True, passive_deletes=True)
    comments = db.relationship(
        'Comment', cascade='all, delete, delete-orphan', backref='user', lazy=True, passive_deletes=True)
    likes = db.relationship('Like', cascade='all, delete, delete-orphan',
                            backref='user', lazy=True, passive_deletes=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deets = db.Column(db.String(220), nullable=False)
    time = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), nullable=False)
    comments = db.relationship(
        'Comment', backref='post', cascade='all, delete, delete-orphan', lazy=True, passive_deletes=True)
    likes = db.relationship('Like', cascade='all, delete, delete-orphan',
                            backref='post', lazy=True, passive_deletes=True)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(380), nullable=False)
    time = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey(
        'post.id', ondelete='CASCADE'), nullable=False)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey(
        'post.id', ondelete='CASCADE'), nullable=False)


'''VIEWS'''


@app.route('/home', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        deets = request.form.get('deets')
        comments = request.form.get('comment')
        print(deets, comments)
        if not deets:
            flash('Can\'t post without any words!', category='error')
        else:
            new_post = Post(deets=deets, author=current_user.id)
            db.session.add(new_post)
            db.session.commit()
            flash('Post successfully added!', category='success')
            return redirect(url_for('home'))

    posts = Post.query.all()
    correct_time = timedelta(hours=4)
    return render_template('homepage.html', user=current_user, posts=posts, correct_time=correct_time)


@app.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Hey! that user does not exist', category='error')
    users_posts = user.posts
    correct_time = timedelta(hours=4)
    username = user.username
    return render_template('profile.html', user=current_user, users_posts=users_posts,
                           correct_time=correct_time, username=username)


@app.route('/delete-acct/<username>', methods=['GET', 'POST'])
@login_required
def delete_acct(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Sorry that user doesn\'t exist.', category='error')
    elif current_user.id != user.id:
        flash('you aren\'t authorized to delete this acct', category='error')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('user successfully deleted!', category='success')
    print([i for i in User.query.all()])
    return redirect(url_for('home'))


@app.route('/delete-post/<post_id>', methods=['GET', 'POST'])
@app.route('/profile/delete-post/<post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if not post:
        return jsonify({'error': 'this post either doesn\'t exist or can\'t be deleted'})

    elif post.author != current_user.id:
        flash('You are not authorized to delete this post', category='error')

    else:
        if post.likes:
            [db.session.delete(i) for i in post.likes]
        if post.comments:
            [db.session.delete(i) for i in post.comments]
        db.session.delete(post)
        db.session.commit()
        flash('Post successfully deleted!', category='success')
    print([i for i in Post.query.all()])
    print([i for i in Comment.query.all()])
    print([i for i in Like.query.all()])
    return jsonify({'success': 'facts',
                    'postId': post_id})


@app.route('/add-comment/<post_id>', methods=['GET', 'POST'])
@login_required
def add_comment(post_id):
    if request.method == 'POST':
        comment = request.form.get('comment')
        if not comment:
            return jsonify({'error': 'No comment to add'}, 400)
        else:
            post = Post.query.filter_by(id=post_id).first()
            if post:
                new_comment = Comment(text=comment,
                                      author=current_user.id, post_id=post_id)
                db.session.add(new_comment)
                db.session.commit()
                flash('Successfully posted comment!', category='success')

            else:
                flash('No post available', category='error')
    post = Post.query.filter_by(id=post_id).first()
    postId = post.id
    return jsonify({'success': 'facts', 'postId': postId})


@app.route('/delete-comment/<comment_id>', methods=['GET', 'POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    if not comment:
        return jsonify({'error': 'Comment doesn\'t exist'}, 400)
        # flash('Comment doesn\'t exist', category='error')

    elif current_user.id != comment.user.id and current_user.id != comment.post.author:
        flash('You are not authorized to delete this post', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment successfully deleted', category='success')
    postId = comment.post_id
    post = Post.query.filter_by(id=postId).first()
    print(postId)
    return jsonify({'success': 'facts',
                    'postId': postId,
                    'commentLen': len(post.comments)})


@app.route('/like-post/<post_id>', methods=['GET', 'POST'])
@login_required
def like_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(
        author=current_user.id, post_id=post_id).first()
    if not post:
        return jsonify({'error': 'Post doesn\'t exist'}, 400)

    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
    print([i for i in Like.query.all()])
    return jsonify({'likes': len(post.likes),
                    'liked': current_user.id in map(lambda n: n.author, post.likes)})


'''AUTHORIZATION'''


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists! Go to the "Sign in" page',
                  category='error')
        elif len(email) < 8:
            flash('Hey! email is too short!', category='error')
        elif len(username) < 4:
            flash('Username is too short!', category='error')
        elif len(password1) < 6:
            flash('Password is too short!', category='error')
        elif password1 != password2:
            flash('Passwords must be the same buddy!', category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Successfully created account!', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('home'))
    return render_template('sign_up.html', user=current_user)


@app.route('/log-in', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully', category='success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                flash('Hey! passwords must match.', category='error')
        else:
            flash('This user does not exist, please try again', category='error')

    return render_template('log_in.html', user=current_user)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login', user=current_user))


if __name__ == '__main__':
    app.run(debug=True, port=8888)
