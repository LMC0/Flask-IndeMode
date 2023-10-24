from enum import unique
from flask import Flask
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
#from flask_bootstrap import BOOTSTRAP_VERSION, Bootstrap

from werkzeug.security import generate_password_hash, check_password_hash
import os

from datetime import datetime
import pytz
import folium
from folium.plugins import HeatMap
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
#bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Asia/Tokyo')))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(12))

class Station(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stationname = db.Column(db.String(30), unique=True)
    stationaddress = db.Column(db.String(12))
    stationlon = db.Column(db.String(12))
    stationlat = db.Column(db.String(12))

class Tenant(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenantaddress= db.Column(db.String(30), unique=True)
    tenantprice = db.Column(db.Integer)
    floor = db.Column(db.String(30))
    tenantstationname = db.Column(db.String(30))
    detailurl = db.Column(db.String(30))
    imgurl = db.Column(db.String(30))
    shikikin = db.Column(db.Integer)
    reikin = db.Column(db.Integer)
    hoshokin = db.Column(db.Integer)
    kaiyakukin = db.Column(db.Integer)

class Fav(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, unique=True)
    tenantid = db.Column(db.Integer)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'GET':
        posts = Post.query.all()
        tenants = Tenant.query.all()
        stations = Station.query.all()
        return render_template('index.html', posts=posts, tenants=tenants, stations=stations)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username=username, password=generate_password_hash(password, method='sha256'))

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')

        post = Post(title=title, body=body)

        db.session.add(post)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('create.html')

@app.route('/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update(id):
    post = Post.query.get(id)
    if request.method == 'GET':
        return render_template('update.html', post=post)
    else:
        post.title = request.form.get('title')
        post.body = request.form.get('body')

        db.session.commit()
        return redirect('/')

@app.route('/<int:id>/delete', methods=['GET'])
@login_required
def delete(id):
    post = Post.query.get(id)

    db.session.delete(post)
    db.session.commit()
    return redirect('/')


@app.route('/mypage', methods=['GET'])
@login_required
def mypage():
    id=1
    post = Post.query.get(id)

    return render_template('mypage.html')



@app.route('/result', methods=['GET', 'POST'])
def result():

    # もしPOSTメソッドならresult.htmlに値dfと一緒に飛ばす
    if request.method == 'POST':

        # HTMLでセレクトした駅情報を取得
        select_station = request.form.get('selected_option')
        

        if select_station is not None:
            # Tena_StationIdがStation_Numと一致するテナントデータを取得し、DataFrameに読み込む
            filtered_tenants = Tenant.query.filter(Tenant.tenantstationname.ilike(f"%{select_station}%")).all()
            
            # select_station に格納された駅名をもとにクエリを実行
            station_data = Station.query.filter_by(stationname=select_station).first()

            #Map情報の取得
            station_name = select_station
            station_lat = station_data.stationlat
            station_lon = station_data.stationlon

            print(station_lat)
            print(station_lon)
            print(filtered_tenants)


            map = folium.Map(location=[station_lat, station_lon],zoom_start = 15,tiles='OpenStreetMap') 

            #MapへのCircle表示
            en = folium.Circle(
            location=[station_lat, station_lon], # 中心
            radius=100, # 半径100m
            color='#ff0000', # 枠の色
            fill_color='#0000ff' # 塗りつぶしの色
            )
            en.add_to(map)

            marker = folium.Marker([station_lat, station_lon], popup=station_name)
            marker.add_to(map)

            df_area = pd.DataFrame(station_data)
            df_rent = pd.DataFrame(filtered_tenants)

            if not filtered_tenants:
                # 結果をHTMLテンプレートに渡す
                return render_template('result.html',df_area=df_area, df_rent=filtered_tenants, map_html=map._repr_html_())
            else:
                return 'No tenant data found for the selected station.'+ station_name
        else:
            return f'StationNum for {station_name} not found'
    
    # POSTメソッドカードセレクトとして飛ばす
    else:
        return render_template("index.html")



