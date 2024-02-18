from flask import make_response, request, jsonify
from loschog import app, db
from loschog.models import Shop, Unexpected, Card, CardSchema, CardBuySchema
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeSerializer as sescher
from secrets import token_hex
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import requests as rr

jwt = JWTManager(app)
# import stripe

# stripe.api_key = 'sk_test_51OCjmTAdIrkx8qGcIp0QZAFW86qL8nd5tSLkch4zZvc6N120DxOWbsq5ee9NVHkYCoUMC8lRwiwb26xiJkw8JmCU00PBbGbfMP'

bcrypt = Bcrypt(app)

@app.route('/unexpected', methods=['POST'])
def unexpected():
    jsoschon = request.json
    unexpected = Unexpected(route=jsoschon['route'], explanation=jsoschon['explanation'])
    db.session.add(unexpected)
    db.session.commit()
    return make_response("", 200)


def password_check(passwd):
    SpecialSym =['$', '@', '#', '%', '!']
     
    if len(passwd) < 6:
        return 'Uw wachtwoord heeft 6 characters nodig'
         
    if len(passwd) > 20:
        return 'Uw wachtwoord mag niet langer dan 12 characters zijn'
         
    if not any(char.isdigit() for char in passwd):
        return 'Uw wachtwoord heeft 1 cijfer nodig'
         
    if not any(char.isupper() for char in passwd):
        return 'Uw wachtwoord heeft 1 hoofdletter nodig'
         
    if not any(char.islower() for char in passwd):
        return 'Uw wachtwoord heeft 1 kleine letter nodig'
        
    if not any(char in SpecialSym for char in passwd):
        return 'Uw wachtwoord heeft 1 symbool nodig zoals $@#!'
    return 'valid'

@app.route('/register', methods=['POST'])
def register():
    jsoschon = request.json
    email = jsoschon['e_mail']
    if Shop.query.filter_by(email=email).first():
        return make_response({
            'error': 'e-mail',
            'message': 'Er bestaat al een account met dit e-mail adres'
        }, 400)
    first_password = jsoschon['first_password']
    first_password_validation_result = password_check(first_password)
    if first_password_validation_result != 'valid':
        return make_response({
            'error': 'first-password',
            'message': first_password_validation_result
        }, 400)
    second_password = jsoschon['second_password']
    second_password_validation_result = password_check(second_password)
    if second_password_validation_result != 'valid':
        return make_response({
            'error': 'second-password',
            'message': second_password_validation_result
        }, 400)
    first_hashed_password = bcrypt.generate_password_hash(first_password).decode('utf-8')
    second_hashed_password = bcrypt.generate_password_hash(second_password).decode('utf-8')
    shop = Shop(email=email, company_name=jsoschon['company_name'], first_password=first_hashed_password, second_password=second_hashed_password)
    db.session.add(shop)
    db.session.commit()
    s = sescher(app.config['SECRET_KEY'])
    token = s.dumps({ 'shop_id': shop.id })
    print(token)
    return make_response("", 200)

@app.route('/confirm/<token>', methods=['POST'])
def confirm(token):
    s = sescher(app.config['SECRET_KEY'])
    payload = s.loads(token)
    shop = Shop.query.filter_by(id=payload['shop_id']).first()
    if not shop:
        return make_response("ongeldig token", 400)
    x = rr.get('http://localhost:3000/create/new-account')
    json = x.json()
    if not shop.address and not shop.private_key:    
        shop.address = json['address']
        shop.private_key = json['private']
        db.session.commit() 
    return make_response("", 200)

@app.route('/login-dashboard', methods=['POST'])
def login_dashboard():
    body = request.json
    shop = Shop.query.filter_by(email=body['e_mail']).first()
    if not shop:
        return make_response("Invalid credentials", 400)
    f_p_r = bcrypt.check_password_hash(shop.first_password, body['first_password'])
    s_p_r = bcrypt.check_password_hash(shop.second_password, body['second_password'])
    if shop.locked_untill > datetime.now():
        return make_response("Sorry, account is locked for 20 minutes", 400)
    if shop.failed_login_attemps > 3:
        shop.failed_login_attemps = 0
        shop.locked_untill = datetime.now() + timedelta(minutes=20)
        db.session.commit()
        return make_response("Sorry, account is locked for 20 minutes", 400)
    if not f_p_r  and not s_p_r:
        return make_response("Invalid credentials", 400)
    if f_p_r and not s_p_r or not f_p_r and s_p_r:
        shop.failed_login_attemps += 1
        db.session.commit()
        return make_response("Invalid credentials", 400)
    if f_p_r and s_p_r: 
        access_token = create_access_token(identity=body['e_mail'])
        return make_response(access_token, 200)

@app.route('/create-card', methods=['POST'])
@jwt_required()
def create_card():
    body = request.json
    # print(body)
    current_user = get_jwt_identity()
    shop = Shop.query.filter_by(email=current_user).first()
    if int(body['value']) < int(body['discount']):
        return make_response("Value needs to be greater than discount", 400)
    card = Card(value=body['value'], discount=body['discount'], shop_id=shop.id);
    db.session.add(card)
    db.session.commit()
    return make_response("", 200)

@app.route('/cards', methods=['GET'])
@jwt_required()
def cards():
    current_user = get_jwt_identity()
    shop = Shop.query.filter_by(email=current_user).first()
    schema = CardSchema()
    cards = Card.query.filter_by(shop_id=shop.id).all()
    return make_response(schema.dumps(cards, many=True), 200)

@app.route('/buy/<id>', methods=['GET'])
def buy(id):
    shop = Shop.query.filter_by(id=id).first()
    cards = Card.query.filter_by(shop_id=id).all()
    schema = CardBuySchema()
    return make_response(jsonify({
        'shop': shop.company_name,
        'cards': schema.dump(cards, many=True)
    }), 200)

@app.route('/balance', methods=[])
@jwt_required()
def balance():
    current_user = get_jwt_identity()
    