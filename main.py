from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from werkzeug.security import generate_password_hash, check_password_hash


# from itsdangerous import TimedSerializer as ts


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    todos = relationship("Todo", back_populates="user")


class Todo(db.Model):
    __tablename__ = "todo"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    activity: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    time: Mapped[str] = mapped_column(String(250), nullable=False)
    user = relationship("Users", back_populates="todos")


with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(Users, user_id)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
        if user:

            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('todolist'))
            else:
                flash('Wrong password')
        else:
            flash('Email not found')
    return render_template("login.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    emails = db.session.execute(db.select(Users.email)).scalars().all()
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        password = request.form['password']
        secure_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        if email in emails:
            flash('Email exists. Login instead')
            return redirect(url_for('login'))
        else:
            new_user = Users(
                email=email,
                name=name,
                password=secure_password, )

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
        return redirect(url_for('todolist'))

    return render_template("signup.html")


@app.route('/todo-list')
@login_required
def todolist():
    return render_template("list.html", todo=current_user.todos, current_user=current_user)


@app.route('/add-list', methods=["POST", "GET"])
@login_required
def addlist():
    if request.method == 'POST':
        activity = request.form['activity']
        date = request.form['date']
        time = request.form['time']
        new_todo = Todo(
            activity=activity,
            date=date,
            time=time,
            user_id=current_user.id)

        db.session.add(new_todo)
        db.session.commit()
        flash("Activity added successfully")
        return redirect(url_for('todolist'))

    return render_template("addlist.html")


@app.route('/reset-password', methods=['GET', 'POST'])
def passwordreset():
    if request.method == 'POST':
        email = request.form['email']
        newpassword = request.form['newpassword']
        confirmpassword = request.form['confirmpassword']
        if newpassword == confirmpassword:
            user = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
            if user:
                updated_password = generate_password_hash(newpassword, method='pbkdf2:sha256', salt_length=8)
                user.password = updated_password
                db.session.commit()
                flash("Password updated successfully")
                return redirect(url_for('login'))
            else:
                flash("User not found, check the email or create account.")

        else:
            flash("Passwords do not match")
    return render_template("resetpassword.html")


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    activity_to_delete = db.get_or_404(Todo, id)
    db.session.delete(activity_to_delete)
    db.session.commit()
    flash("Deleted Successfully")
    return redirect(url_for('todolist'))


@app.route('/update-list/<int:id>', methods=["GET", "POST"])
@login_required
def update(id):
    list_to_update = db.get_or_404(Todo, id)

    if request.method == 'GET':

        activity_to_update = list_to_update.activity
        date_to_update = list_to_update.date
        time_to_update = list_to_update.time
        return render_template('updatelist.html', activity=activity_to_update, date=date_to_update, time=time_to_update, id=id)

    elif request.method == 'POST':
        activity = request.form['activity']
        date = request.form['date']
        time = request.form['time']
        list_to_update.activity = activity
        list_to_update.date = date
        list_to_update.time = time

        db.session.commit()

        return redirect(url_for('todolist'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
