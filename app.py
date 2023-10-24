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
import numpy as np

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
@login_required
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

        
            if filtered_tenants:
                # 結果をHTMLテンプレートに渡す
                return render_template('result.html',df_area=station_data, df_rent=filtered_tenants, map_html=map._repr_html_())
            else:
                return 'No tenant data found for the selected station.'+ station_name + str(len(filtered_tenants))
        else:
            return f'StationNum for {station_name} not found'
    
    # POSTメソッドカードセレクトとして飛ばす
    else:
        return render_template("index.html")

# カスタムフィルターを定義
@app.template_filter('len')
def length(obj):
    return len(obj)




@app.route('/rent_info', methods=['GET', 'POST'])
@login_required
def rent_info():

    card_id = card_id = request.form.get('card_info')

    # POSTリクエストから直接値を取得
    card_id = request.form.get('card_info')
    print(card_id)

    # Tena_StationIdがStation_Numと一致するテナントデータを取得し、DataFrameに読み込む
    df_rent = Tenant.query.filter_by(id=card_id).first()
        
    # ここでカード情報を扱う処理を行う

    # レンダリングするHTMLを指定して表示
    return render_template('rent_info.html', df_rent=df_rent)  # GeoInfoページのHTMLテンプレート名を指定
        


@app.route('/geo_info', methods=['GET', 'POST'])
@login_required
def geo_info():
    # POSTリクエストから直接値を取得
    card_id = request.form.get('card_info')
    print(card_id)


    # Tena_StationIdがStation_Numと一致するテナントデータを取得し、DataFrameに読み込む
    df_rent = Tenant.query.filter_by(id=card_id).first()

    station_name = df_rent.tenantstationname
    print(station_name)

    df_area = Station.query.filter_by(stationname=station_name).first()

    #Map情報の取得
    station_name = station_name
    station_lat = df_area.stationlat
    station_lon = df_area.stationlon


    map = folium.Map(location=[station_lat, station_lon],zoom_start = 15,tiles='OpenStreetMap') 

    #MapへのCircle表示
    en = folium.Circle(
    location=[station_lat, station_lon], # 中心
    radius=800, # 半径100m
    color='#ff0000', # 枠の色
    fill_color='#0000ff' # 塗りつぶしの色
    )
    en.add_to(map)

    marker = folium.Marker([station_lat, station_lon], popup=station_name)
    marker.add_to(map)
    
    # ここでカード情報を扱う処理を行う

    # レンダリングするHTMLを指定して表示
    return render_template('geo_info.html', df_rent=df_rent,map_html=map._repr_html_())  # GeoInfoページのHTMLテンプレート名を指定



@app.route('/calc', methods=['GET', 'POST'])
@login_required
def calc():

    # POSTリクエストから直接値を取得
    card_id = request.form.get('card_info')
    print(card_id)
    if card_id is None:
        card_id = request.form.get('card_id')

    # テナントデータを取得し、DataFrameに読み込む
    df_rent = Tenant.query.filter_by(id=card_id).first()

    initial_investment = request.form.get('initial_investment')
    if initial_investment is None or initial_investment.strip() == '':
        initial_investment = 2000000
        print("デフォルト値を設定しましたInvest")
    else:
        initial_investment = float(request.form.get('initial_investment'))
        initial_investment = initial_investment * 10000

    bussiness_hour = request.form.get('bussiness_hour')
    if  bussiness_hour is None or bussiness_hour.strip() == '':
        bussiness_hour = 10
        print("デフォルト値を設定しましたbusinessh")
    else:
        bussiness_hour = int(request.form.get('bussiness_hour'))
    
    ave_time = request.form.get('ave_time')
    if ave_time is None or ave_time.strip() == '':
        ave_time = 90
        print("デフォルト値を設定しましたtime")
    else:
        ave_time = int(request.form.get('ave_time'))
        
    chair = request.form.get('chair') 
    if chair is None or chair.strip() == '':
        chair = 2
        print("デフォルト値を設定しましたchair")
    else:
        chair = int(request.form.get('chair'))
    
    booking_rate = request.form.get('booking_rate') 
    if booking_rate is None or booking_rate.strip() == '':
        booking_rate = 60
        print("デフォルト値を設定しましたrate")
    else:    
        booking_rate = int(request.form.get('booking_rate'))

    days = request.form.get('days')
    if  days is None or days.strip() == '':
        days = 25
        print("デフォルト値を設定しましたdays")
    else:
        days = int(request.form.get('days'))

    customer_price = request.form.get('customer_price')
    if customer_price is None or customer_price.strip() == '':
        customer_price = 5000
        print("デフォルト値を設定しましたprice")
    else:
        customer_price = int(request.form.get('customer_price'))
    
    movingin_cost = request.form.get(' movingin_cost')
    if movingin_cost is None or movingin_cost.strip() == '':
        movingin_cost = 6
        print("デフォルト値を設定しましたin")
    else:
        movingin_cost = int(request.form.get(' movingin_cost'))
    
    moving_cost = request.form.get('moving_cost')
    if moving_cost is None or moving_cost.strip() == '':
        moving_cost = 500000
        print("デフォルト値を設定しましたmove")
    else:
        moving_cost = int(request.form.get('moving_cost'))
    
    rent_cost = request.form.get('rent_cost')
    if rent_cost is None or rent_cost.strip() == '':
        rent_cost = int(df_rent.tenantprice)
        print("デフォルト値を設定しましたrent")
    else:
        rent_cost = int(df_rent.tenantprice)
    
    hire_cost = request.form.get('hire_cost')
    if hire_cost is None or hire_cost.strip() == '':
        hire_cost = 3
        print("デフォルト値を設定しましたhire")
    else:
        hire_cost = int(request.form.get('hire_cost'))

    utility_cost = request.form.get('utility_cost')
    if utility_cost is None or utility_cost.strip() == '':
        utility_cost = 5000
        print("デフォルト値を設定しましたutil")
    else:
        utility_cost = float(request.form.get('utility_cost'))
    
    material_cost = request.form.get('material_cost')
    if material_cost is None or material_cost.strip() == '':
        material_cost = .2
        print("デフォルト値を設定しましたmeter")
    else:
        material_cost = float(request.form.get('material_cost'))
    
    ad_cost = request.form.get('ad_cost')
    if ad_cost is None or ad_cost.strip() == '':
        ad_cost = 100000
        print("デフ入れるADno")
    else:
        ad_cost = int(request.form.get('ad_cost'))

    bussiness_minutes = 60

    max_turnover = float(bussiness_hour) * float(bussiness_minutes) / float(ave_time)

    if max_turnover is not None:
        max_turnover_str = str(max_turnover)
        print("回転計さんturn" + max_turnover_str)
    else:
        print("max_turnoverはNoneです。")

    servicenum = chair * max_turnover * (booking_rate/100)
    print("回転計さん"+  str(servicenum))
    benefit = servicenum * customer_price * days
    benefit = int(benefit)
    print("回転計さん"+  str(benefit))

    initial_cost =  movingin_cost + moving_cost
    print("回転計さんinitial"+  str(initial_cost))
    print("回転計さんInvest"+  str(initial_investment))

    if ( (initial_investment - initial_cost) >= 0 ):
        initial_check =  "Clear"
    else:
        initial_check = int(initial_investment) - int(initial_cost)
    

    fixed_cost =   rent_cost + (hire_cost * 350000) + utility_cost
    print("回転計さん"+  str(fixed_cost))
    variable_cost = ( benefit * (material_cost/100)) + ad_cost
    variable_cost = int(variable_cost)
    print("回転計さん"+  str(variable_cost))

    final_benefit = benefit - (fixed_cost + variable_cost)
    final_benefit = int(final_benefit)
    print("Final:--------------------"+ str(final_benefit))

    initial_investment = initial_investment /10000

    #計算のデータをディクショナリにまとめる
    result_data = {
        'initial_investment': initial_investment,
        'bussiness_hour': bussiness_hour,
        'bussiness_minutes': bussiness_minutes,
        'ave_time':ave_time,
        'max_turnover': max_turnover,
        'servicenum':servicenum,
        'chair':chair,
        'booking_rate':booking_rate,
        'benefit':benefit,
        'customer_price':customer_price,
        'days':days,
        'initial_cost':initial_cost,
        'movingin_cost':movingin_cost,
        'moving_cost':moving_cost,
        
        'initial_check':initial_check,
        
        'fixed_cost':fixed_cost,
        'rent_cost':rent_cost,
        'hire_cost':hire_cost,
        'utility_cost':utility_cost,
        'variable_cost':variable_cost,
        'material_cost':material_cost,
        'ad_cost':ad_cost,
        'final_benefit': final_benefit,  # ここに最終結果を追加
    }

    # レンダリングするHTMLを指定して表示
    return render_template('calc.html', df_rent=df_rent, df_calc=result_data)  # GeoInfoページのHTMLテンプレート名を指定




