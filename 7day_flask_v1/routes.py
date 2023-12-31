import os
from datetime import datetime
from flask import Blueprint, render_template,request,Flask,redirect,url_for,session
from werkzeug.utils import secure_filename
from models import db,User,Category,Product,Cart,Manufacture
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user,login_required,current_user
from flask import current_app
app = Flask(__name__)
with app.app_context():
    UPLOAD_FOLDER = './static/uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    current_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


### Tạo blueprint ###
bp = Blueprint('routes', __name__)

### định tuyến  chung ###
def is_admin():
    user = current_user
    if user and user.role == 1:
        return True
    return False

@bp.route('/')
def index():
    feature_products = Product.query.filter(Product.feature == 1).limit(3).all()
    cate_of_the_month = Category.query.filter(Category.feature == 1).limit(3).all()
    return render_template('index.html',cate_of_the_month=cate_of_the_month,feature_products=feature_products)

@bp.route('/403')
def view_403():
    return render_template('403.html')

### AUTHENTICATION ###
@bp.route('/login', methods=['GET', 'POST'])
def view_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Lấy người dùng và kiểm tra tồn tại
        user = User.query.filter_by(email=email).first()
        if user is None or not check_password_hash(user.password, password):
            # Thông tin đăng nhập không hợp lệ
            return redirect(url_for('routes.view_login')+ '?message=Email hoặc mật khẩu không chính xác')
        else:
            login_user(user)
            return redirect(url_for('routes.index'))

    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def view_register():
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        created_at = datetime.now()
        #kiem tra tk ton tai
        user = User.query.filter_by(email=email).first()
        if user:
            return redirect(url_for('routes.view_register')+ '?message=Địa chỉ email đã tồn tại!')
        new_user = User(email=email, phone=phone, password=generate_password_hash(password, method='pbkdf2:sha256'), role=0 ,created_at=created_at)
        db.session.add(new_user)
        db.session.commit()
        #dang nhap cho user do luon
        login_user(new_user)
        return redirect(url_for('routes.index'))
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()  
    return redirect(url_for('routes.view_login'))
### contact and about ###
@bp.route('/about')
def view_about():
    return render_template('about.html')
@bp.route('/contact')
def view_contact():
    return render_template('contact.html')


########### SHOP ##########
@bp.route('/shop')
def view_shop():
    #get manufacture limit 4 with feature == 1 
    manufactures = Manufacture.query.all()[:4]
    page = request.args.get('page', 1, type=int)  # Get the page number from the query parameters
    per_page = 4  # Number of products per page

    all_product = Product.query.paginate(page=page, per_page=per_page)  # Paginate the products
    categories = Category.query.all()
    
    return render_template('shop.html', categories=categories, all_product=all_product,manufactures=manufactures)

@bp.route('/shop/<category_id>')
def view_shop_category(category_id):
    #get manufacture limit 4 with feature == 1 
    manufactures = Manufacture.query.all()[:4]
    categories = Category.query.all()
    category = Category.query.filter_by(id=category_id).first()
    products = Product.query.filter_by(category_id=category.id).all()
    return render_template('shop_category.html', category=category, products=products,categories=categories,manufactures=manufactures)

@bp.route('/product/<int:product_id>')
def detail_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('detail_product.html', product=product)

@bp.route('/cart')
@login_required
def view_cart():
    user = current_user
    total_cart = Cart.calculate_total_price(user.id)
    cart_items = Cart.get_all_products(user.id)
    return render_template('cart.html',user=user,cart_items=cart_items,total_cart=total_cart)

@bp.route('/cart/add/<int:product_id>')
@login_required
def add_to_cart(product_id):
    user = current_user
    product = Product.query.get(product_id)
    cart = Cart(user_id=user.id, product_id=product.id, quantity=1, price=product.price)
    db.session.add(cart)
    db.session.commit()
    return redirect(url_for('routes.view_cart'))

@bp.route('/del-cart-item/<int:item_id>')
@login_required
def del_cart_item(item_id):
    #lay cart cua user
    user_cart = Cart.query.filter_by(user_id=current_user.id).first()
    if user_cart:
        # lay san pham trong gio hang theo item_id
        item = Cart.query.filter_by(id=user_cart.id, product_id=item_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
    return redirect(url_for('routes.view_cart',message='success'))
################# SEARCH #################
@bp.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        return redirect(url_for('routes.search_results'))
    return render_template('search.html')

@bp.route('/search/results', methods=['GET'])
def search_results():
    keyword = request.args.get('keyword')
    products = Product.search_products(keyword)
    return render_template('search.html', keyword=keyword, products=products)
################# ADMIN #################
@login_required
@bp.route('/admin')
def admin_view():
    user = current_user
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    return render_template('core/admin/index.html',user=user)
### định tuyến người dùng (User) ###
@login_required
@bp.route('/users')
def user_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    users = User.query.all()
    return render_template('core/user/index.html',users=users)

@login_required
@bp.route('/create-user', methods=['GET', 'POST'])
def create_user_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = 1 if 'role' in request.form else 0
        created_at = datetime.now()
        #check !user ton tai
        user = User.query.filter_by(email=email).first()
        if user:
            return redirect(url_for('routes.create_user_view')+ '?message=User đã tồn tại')
        new_user = User(email=email, phone=phone, password=generate_password_hash(password, method='pbkdf2:sha256'), role=role ,created_at=created_at)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('routes.user_view')+ '?message=create')
    return render_template('core/user/create.html')

@login_required
@bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
def edit_user_view(user_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    user = User.query.filter_by(id=user_id).first_or_404()
    if request.method == 'POST':
        # Get information from request
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        new_phone = request.form.get('phone')
        role = 1 if 'role' in request.form else 0
        # Update info user and save
        user.name = new_name
        user.email = new_email
        user.phone = new_phone
        user.role = role
        db.session.commit()
        return redirect(url_for('routes.user_view')+ '?message=update')
    return render_template('core/user/edit.html',user=user)

@login_required
@bp.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    user = User.query.filter_by(id=user_id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('routes.user_view', message='delete'))
### định tuyến Danh muc (Category) ###
@login_required
@bp.route('/categories')
def category_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    categories = Category.query.all()
    return render_template('core/category/index.html',categories=categories)

@login_required
@bp.route('/create-category', methods=['GET', 'POST'])
def create_category_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    if request.method == 'POST':
            name = request.form.get('name')
            image = request.files['image']
            feature = 1 if 'feature' in request.form else 0
            created_at = datetime.now()
            #upload image
            if image:
                print(image)
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_category = Category(name=name,image=filename,feature=feature,created_at=created_at)
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('routes.category_view')+ '?message=create')
    return render_template('core/category/create.html')

@login_required
@bp.route('/edit-category/<int:category_id>', methods=['GET', 'POST'])
def edit_category_view(category_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    category = Category.query.filter_by(id=category_id).first_or_404()
    if request.method == 'POST':
        # Get information from request
        new_name = request.form.get('name')
        new_image = request.files['image']
        new_feature = 1 if 'feature' in request.form else 0
        if new_image:
            filename = secure_filename(new_image.filename)
            new_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            category.image = filename
        # Update info user and save
        category.name = new_name
        category.feature = new_feature
        db.session.commit()
        return redirect(url_for('routes.category_view')+ '?message=update')
    return render_template('core/category/edit.html',category=category)

@login_required
@bp.route('/delete-category/<int:category_id>',methods=['POST'])
def delete_category(category_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    category = Category.query.filter_by(id=category_id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('routes.category_view', message='delete'))

### định tuyến Nha san xuat (Manufacture) ###
@login_required
@bp.route('/manufactures')
def manufacture_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    manufeactures = Manufacture.query.all()
    return render_template('core/manufeacture/index.html',manufeactures=manufeactures)

@login_required
@bp.route('/create-manufacture',methods=['GET','POST'])
def create_manufacture_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            image = request.files['image']
            feature = 1 if 'feature' in request.form else 0
            created_at = datetime.now()
            #upload image
            if image:
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_manufacture = Manufacture(name=name,description=description,image=filename,feature=feature,created_at=created_at)
            db.session.add(new_manufacture)
            db.session.commit()
            return redirect(url_for('routes.manufacture_view')+ '?message=create')
    return render_template('core/manufeacture/create.html')

@login_required
@bp.route('/edit-manufacture/<int:manu_id>',methods=['GET','POST'])
def edit_manufacture_view(manu_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    manufacture = Manufacture.query.filter_by(id=manu_id).first_or_404()
    if request.method == 'POST':
        # Get information from request
        new_name = request.form.get('name')
        new_image = request.files['image']
        new_description = request.form.get('description')
        new_feature = 1 if 'feature' in request.form else 0
        if new_image:
            filename = secure_filename(new_image.filename)
            new_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            manufacture.image = filename
        # Update info user and save
        manufacture.name = new_name
        manufacture.description = new_description
        manufacture.feature = new_feature
        db.session.commit()
        return redirect(url_for('routes.manufacture_view')+ '?message=update')
    return render_template('core/manufeacture/edit.html',manufacture=manufacture)

@login_required
@bp.route('/delete-manufacture/<int:manu_id>',methods=['POST'])
def delete_manufacture(manu_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    manufacture = Manufacture.query.filter_by(id=manu_id).first_or_404()
    db.session.delete(manufacture)
    db.session.commit()
    return redirect(url_for('routes.manufacture_view', message='delete'))

### định tuyến san pham (Product) ###
@login_required
@bp.route('/products')
def product_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    products = Product.query.all()
    return render_template('core/product/index.html',products=products)

@login_required
@bp.route('/create-product',methods=['GET','POST'])
def create_product_view():
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    categories = Category.query.all()
    manufactures = Manufacture.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        manu_id = request.form.get('manu_id')
        image = request.files['image']
        price = request.form.get('price')
        description = request.form.get('description')
        feature = 1 if 'feature' in request.form else 0
        created_at = datetime.now()
        if image:
            print(image)
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_product = Product(name=name,category_id=category_id,manu_id=manu_id,image=filename,price=price,description=description,feature=feature,created_at=created_at)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('routes.product_view')+ '?message=create')
    return render_template('core/product/create.html',categories=categories,manufactures=manufactures)

@login_required
@bp.route('/edit-product/<int:product_id>',methods=['GET','POST'])
def edit_product_view(product_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    product = Product.query.filter_by(id=product_id).first_or_404()
    categories = Category.query.all()
    manufactures = Manufacture.query.all()
    if request.method == 'POST':
        # Get information from request
        new_name = request.form.get('name')
        new_category_id = request.form.get('category_id')
        new_manu_id = request.form.get('manu_id')
        new_image = request.files['image']
        new_price = request.form.get('price')
        new_feature = 1 if 'feature' in request.form else 0
        if new_image:
            filename = secure_filename(new_image.filename)
            new_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            product.image = filename
        # Update info user and save
        product.name = new_name
        product.price = new_price
        product.category_id = new_category_id
        product.manu_id = new_manu_id
        product.feature = new_feature
        db.session.commit()
        return redirect(url_for('routes.product_view')+ '?message=update')
    return render_template('core/product/edit.html',categories=categories,manufactures=manufactures,product=product)

@login_required
@bp.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not is_admin():
        return redirect(url_for('routes.view_403'))
    product = Product.query.filter_by(id=product_id).first_or_404()
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('routes.product_view', message='delete'))