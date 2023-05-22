# import base64
# from io import BytesIO

from flask import Flask, request, session, redirect, url_for, \
    render_template, flash, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, join
# import ping3
import time
from datetime import timedelta, datetime
import psycopg2
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, join, func
# import matplotlib.pyplot as plt

app = Flask(__name__)

start_time = time.time()
# while True:
#     projekt-flask-uczelnia = time.time() - start_time
#     uptime_str = time.strftime("%H:%M:%S", time.gmtime(projekt-flask-uczelnia))
#     print(uptime_str)n
#     time.sleep(1)



# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:docker@192.168.48.132:5431/postgres'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:docker@192.168.48.132:5431/pyth'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://python:vKmpgzdISLFuVw19jrAXhmd7lgyTMnUn@dpg-chlhfl3hp8uej75mh7kg-a.frankfurt-postgres.render.com/pyth_tn78'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://python:vKmpgzdISLFuVw19jrAXhmd7lgyTMnUn@dpg-chlhfl3hp8uej75mh7kg-a/pyth_tn78'
app.config['SESSION_TYPE'] = 'filesystem'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
Session(app)

class User(db.Model):
    __tablename__ = 'User'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    imie = db.Column(db.String)
    nazwisko = db.Column(db.String)
    email = db.Column(db.String)
    login = db.Column(db.String)
    haslo = db.Column(db.String)

    def __init__(self, imie, nazwisko, email, login, haslo ,id):
        self.id = id
        self.imie = imie
        self.nazwisko = nazwisko
        self.email = email
        self.login = login
        self.haslo = bcrypt.generate_password_hash(haslo).decode("utf-8")


class Logowania(db.Model):
    __tablename__ = 'Logowania'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer)
    data = db.Column(db.Date)

    def __init__(self, id_user, data, id):
        self.id_user = id_user
        self.data = data
        self.id = id

@app.route("/")
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        users = User.query.all()
        return render_template('index.html', users=users, imie=session['imie'], nazwisko=session['nazwisko'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['inputEmail']
        haslo = request.form['inputPassword']
        pass1 = haslo
        user = User.query.filter_by(login=email).first()
        # userid = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.haslo, pass1):
            session['logged_in'] = True
            session['username'] = email
            session['userid'] = user.id
            session['imie'] = user.imie
            session['nazwisko'] = user.nazwisko
            # print(session['imie'])
            # print('zalogowano:', user.imie, user.nazwisko)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logowanie_data = Logowania(id_user=session['userid'], data=current_datetime, id=None)
            db.session.add(logowanie_data)
            db.session.commit()


            return redirect(url_for('index'))
        else:
            flash('Niepoprawna nazwa użytkownika lub hasło')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Wylogowano')
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    # if not session.get('logged_in'):
    #     return redirect(url_for('login'))
    # else:
    if request.method == 'POST':
        imie = request.form['inputFirstName']
        nazwisko = request.form['inputLastName']
        email = request.form['inputEmail']
        login = email
        haslo = request.form['inputPassword']
        hasloc = request.form['inputPasswordConfirm']
        if hasloc == haslo:
            haslo = hasloc
        user = User(imie, nazwisko, email, login, haslo, id=None)
        db.session.add(user)
        db.session.commit()
        # flash('Zarejestrowałeś się')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route("/activity")
def activity():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        # logins = Logowania.query.all()
        # logins1 = db.session.query(User.id, User.imie, User.nazwisko).join(Logowania).filter(User.id == Logowania.id_user).all()

        logins = db.session.query(User.id, User.imie, User.nazwisko, Logowania.data).select_from(
            join(User, Logowania, User.id == Logowania.id_user)).all()
        return render_template('activity.html', logins=logins)

@app.route("/logowania_api", methods=['GET'])
def logowania_api():

        # logins = Logowania.query.all()
        # logins1 = db.session.query(User.id, User.imie, User.nazwisko).join(Logowania).filter(User.id == Logowania.id_user).all()

        logins = db.session.query(User.id, User.imie, User.nazwisko, Logowania.data).select_from(
            join(User, Logowania, User.id == Logowania.id_user)).all()
        logins_dict = [row._asdict() for row in logins]

        return jsonify(logins_dict)

@app.route("/users",methods=['GET', 'POST'])
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        users = User.query.order_by(User.id).all()

        return render_template('users.html', users=users, imie=session['imie'], nazwisko=session['nazwisko'])

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):


    if request.method == 'POST':
        user = User.query.get(user_id)
        user.imie = request.form['imie']
        user.nazwisko = request.form['nazwisko']
        user.email = request.form['email']
        password = request.form['password']
        if password == '':
            pass
        else:
            user.haslo = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.commit()
        return redirect('/users')

@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect('/users')

# @app.route('/chart')
# def plot_login_histogram():
#     login_counts = db.session.query(Logowania.id_user).group_by(Logowania.id_user).count()
#
#     max_name_length = 10  # Maksymalna liczba liter na nazwie użytkownika
#     user_logins = db.session.query(Logowania.id_user, func.string_agg(User.imie, ', '),
#                                    func.string_agg(User.nazwisko, ', ')). \
#         join(User, Logowania.id_user == User.id). \
#         group_by(Logowania.id_user). \
#         having(func.count(Logowania.id_user) > 1).all()
#
#     login_freq = [db.session.query(Logowania).filter_by(id_user=user_id[0]).count() for user_id in user_logins]
#
#     user_names = [f"{user[1][:max_name_length]} {user[2][:max_name_length]}" for user in user_logins]
#
#     plt.bar(range(len(user_logins)), login_freq)
#     plt.xticks(range(len(user_logins)), user_names, rotation='vertical')
#     plt.xlabel('User')
#     plt.ylabel('Login Frequency')
#     plt.title('Most Frequent User Logins')
#
#     # Zapisz wykres w formacie PNG
#     buffer = BytesIO()
#     plt.savefig(buffer, format='png')
#     buffer.seek(0)
#
#     # Konwertuj dane wykresu na kod base64
#     image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
#
#     # Zwróć szablon HTML, który zawiera wykres
#     return render_template('chart1.html', image_base64=image_base64)


if __name__ == "__main__":
    app.secret_key = 'test'
    app.permanent_session_lifetime = timedelta(minutes=10)
    # app.run(port=443, host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'),debug=True)
    app.run(port=80, host='0.0.0.0', debug=True)

