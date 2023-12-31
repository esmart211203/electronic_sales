from flask import Flask, render_template, request, url_for, redirect, flash
from flask_mysqldb import MySQL
from datetime import datetime
from flask_migrate import Migrate
from models import db, User, Category, Product
from werkzeug.utils import secure_filename
from routes import bp as routes_bp
from flask_login import LoginManager
from sqlalchemy.orm import relationship
import os

app = Flask(__name__)

### Cấu hình Cơ sở dữ liệu ###
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///electronic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

### Cấu hình Upload ###
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

### Khởi tạo cơ sở dữ liệu ###
db.init_app(app)
migrate = Migrate(app, db)

### Cấu hình secret_key ###
app.secret_key = 'your_secret_key'

### Khởi tạo LoginManager ###
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'routes.view_login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


### Route ###
app.register_blueprint(routes_bp)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)