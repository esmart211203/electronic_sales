from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
from sqlalchemy.orm import relationship
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(120),unique=True,)
    phone = db.Column(db.String(11))
    password = db.Column(db.String(25))
    role = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self,email,phone,password,role,created_at):
        self.email = email
        self.phone = phone
        self.password = password
        self.role = role
        self.created_at = created_at
        def __repr__(self):
            return f"{self.email} : {self.role}"
        
    @staticmethod
    def calculate_total_quantity(user_id):
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        total_quantity = 0
        for item in cart_items:
            total_quantity += item.quantity
        return total_quantity
    
    def is_active(self):
        return True
    def get_id(self):
        return str(self.id)
    def is_authenticated(self):
        return True  # Trả về True nếu người dùng đã xác thực thành công
    def is_anonymous(self):
        return False  # Trả về False vì chúng ta không hỗ trợ người dùng ẩn danh
class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    image = db.Column(db.String(100))
    feature = db.Column(db.Integer,default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, image, feature=0, created_at=None):
        self.name = name
        self.image = image
        self.feature = feature
        if created_at is None:
            created_at = datetime.utcnow()
        self.created_at = created_at
    def get_name(cls):
        return cls.name
class Manufacture(db.Model):
    __tablename__ = "manufacture"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(100))
    image = db.Column(db.String(100))
    feature = db.Column(db.Integer,default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, description,image, feature=0, created_at=None):
        self.name = name
        self.description = description
        self.image = image
        self.feature = feature
        if created_at is None:
            created_at = datetime.utcnow()
        self.created_at = created_at
    def get_name(cls):
        return cls.name
class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    manu_id = db.Column(db.Integer, db.ForeignKey('manufacture.id'))
    image = db.Column(db.String(100))
    price = db.Column(db.Integer)
    description = db.Column(db.Text,default='')
    feature = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    ## tao moi quen quan he de tu 1 san pham tro? toi model * dc 
    ## vd tu 1 san pham goi toi model thong qua khoa ngoai goi toi ham {{product.category.get_name()}}
    manufacture = relationship("Manufacture", backref="products")
    category = relationship("Category", backref="products")
    def __init__(self, name, category_id,manu_id , image, price, description , feature=0, created_at=None):
        self.name = name
        self.category_id = category_id
        self.manu_id = manu_id
        self.image = image
        self.price = price
        self.description = description
        self.feature = feature
        if created_at is None:
            created_at = datetime.utcnow()
        self.created_at = created_at
      
    @staticmethod  
    def count_products_by_id(product_id):
        count = Cart.query.filter_by(product_id=product_id).count()
        return count
    def search_products(keyword):
        # Lọc sản phẩm dựa trên từ khóa trong (tên sphaarm, tên danh mục hoặc tên nhà sản xuất)
        products = Product.query.filter(
            db.or_(
                Product.name.ilike(f"%{keyword}%"),  # Tìm từ khóa trong tên sản phẩm
                Product.category.has(Category.name.ilike(f"%{keyword}%")),  # Tìm từ khóa trong tên danh mục
                Product.manufacture.has(Manufacture.name.ilike(f"%{keyword}%"))  # Tìm từ khóa trong tên nhà sản xuất
            )
        ).all()
        return products
class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Integer)

    def __init__(self, user_id, product_id, quantity, price):
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

    @classmethod
    def get_all_products(cls, user_id):
        #lay gio hang cua thg user thong qua userid => cart 
        cart_items = cls.query.filter_by(user_id=user_id).all()
        #lay id san pham truyen vao []
        product_ids = [cart_item.product_id for cart_item in cart_items]
        #lay san pham theo id sp trong [] id san pham truoc do
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        #tra ve list sp cua user do
        return products
    
    #ham tinh tong gio hang
    @classmethod
    def calculate_total_price(cls, user_id):
        #lay tat ca san pham trong gio cua user do
        cart_items = cls.query.filter_by(user_id=user_id).all()
        total_price = 0
        #tinh tong 
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_id)
            total_price += product.price
        return total_price
