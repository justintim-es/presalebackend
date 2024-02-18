from loschog import db
import datetime as dt
from marshmallow import Schema, fields

class Unexpected(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(256), nullable=False)
    explanation = db.Column(db.String(256), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow())

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    first_password = db.Column(db.String(256), nullable=False)
    second_password = db.Column(db.String(256), nullable=False)
    locked_untill = db.Column(db.DateTime(), nullable=False, default=dt.datetime.now())
    address = db.Column(db.String(256), nullable=True)
    private_key = db.Column(db.String(256), nullable=True)
    # stripe = db.Column(db.String(256), nullable=True)
    # recognition = db.Column(db.String(256), nullable=True)
    failed_login_attemps = db.Column(db.Integer(), default=0)
    cards = db.relationship('Card')
 

class Card(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.Integer(), nullable=False) 
    discount = db.Column(db.Integer(), nullable=False)  
    shop_id = db.Column(db.Integer(), db.ForeignKey('shop.id'), nullable=False)

class CardSchema(Schema):
    value = fields.Int()
    discount = fields.Int()
    
class CardBuySchema(Schema):
    id = fields.Int()
    value = fields.Int()
    discount = fields.Int()
