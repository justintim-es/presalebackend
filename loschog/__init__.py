from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
app.config['SECRET_KEY'] = '7addb206591ede6726bb44ee82881f7db434f89b0455e49b6b30f7c61094b100ea149fadbc6108d5b5163cabbeac20388ff0662824e898e506a43716c6161ec9'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://justin:times@localhost:5432/presches'
db = SQLAlchemy(app)


import loschog.routs
