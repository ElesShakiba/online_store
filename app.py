import bcrypt
import sqlite3
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_bcrypt import Bcrypt
import datetime
import os
from flask import render_template, request
from datetime import datetime
from flask import request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from flask import Flask, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = '220034'  # برای سشن

db = 'store.db'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

# فرمت‌های مجاز
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row  # برای دسترسی به داده‌ها به صورت دیکشنری
    return conn

bcrypt = Bcrypt(app)

# --------------- Users ------------------
def create_user_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username,email, password, role):
    conn = get_db()
    cursor = conn.cursor()
    '''
    if role == 'admin':
        password = bcrypt.generate_password_hash('9594508').decode('utf-8')
    '''
    cursor.execute('''
        INSERT INTO users (username ,email, password, role) VALUES (?, ?, ?, ?)
    ''', ( email, password, role,username))
    
    conn.commit()
    conn.close()

# ------------------ Routes ------------------
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # دریافت اطلاعات فرم
        
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        username = request.form.get('username')
        if not username or not email or not password or not role:
            return render_template('home.html', signup_form=True, message="All fields are required!")        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # اضافه کردن کاربر جدید به دیتابیس
            cursor.execute(
                "INSERT INTO users (email, password, role,username) VALUES (?, ?, ?, ?)",
                (email, password, role,username)
            )
            conn.commit()
            success_message = "Registration was successful! Please log in."
        except Exception as e:
            conn.rollback()
            success_message = f"Error during registration: {str(e)}"
        finally:
            conn.close()
        
        # ارسال پیام موفقیت و فرم ورود
        return render_template('home.html', loginform=True, message=success_message)
    
    # نمایش صفحه پیش‌فرض ثبت‌نام
    return render_template('home.html', signupform=True)

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()  # تابعی که به دیتابیس وصل می‌شود
        cursor = conn.cursor()
        print("Username entered:", email)
        print("Password entered:", password)

        # بررسی نام کاربری و رمز عبور
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        print("User from database:", user)

        conn.close()

        if user:
            # ثبت اطلاعات کاربر در سشن
            session['user_id'] = user[0]  # فرض کنیم id در ستون اول است
            session['email'] = user[1]  # فرض کنیم نام کاربری در ستون دوم است
            session['password'] = user[2]
            session['role']=user[3]
            session['username']=user[4]
            print("User role:",session['role'])

            # هدایت به داشبورد ادمین یا کاربر
            if ['role'] == 'admin':
                return redirect('/admin_dashboard')
            else:
                return redirect('/user_dashboard')  # اگر صفحه داشبورد کاربر معمولی دارید
        else:
            return render_template('home.html', login_form=True, message="Invalid username or password!")

    return render_template('home.html',login_form =True)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        # فرض می‌کنیم ID کاربر از سشن خوانده شود
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('user_dashboard'))
    return render_template('change_password.html')

@app.route('/admin/orders')
def admin_orders():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    return str(orders)

# ------------------ Admin Dashboard ------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'].strip().lower() == 'admin' and 'password' in session and session['password'] == '220034':
        return render_template ('admin_dashboard.html')
    else:
        return ('password not correct')


# مدیریت کاربران
@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    conn = get_db()
    cursor = conn.cursor()

    # جستجو
    search_query = request.args.get('search', '')  # دریافت کوئری جستجو
    if search_query:
        cursor.execute('''
            SELECT * FROM users
            WHERE username LIKE ? OR email LIKE ? OR role LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    # افزودن/ویرایش کاربر
    if request.method == 'POST':
        users_id = request.form.get('users_id')  # ID برای ویرایش
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if users_id:  # ویرایش کاربر
            cursor.execute('''
                UPDATE users
                SET username = ?, email = ?, password = ?, role = ?
                WHERE id = ?
            ''', (username, email, password, role, users_id))
        else:  # افزودن کاربر جدید
            cursor.execute('''
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password, role))
        conn.commit()
        return redirect('/manage_users')

    return render_template('manage_users.html', users=users, search_query=search_query)

@app.route('/delete_user/<int:users_id>', methods=['DELETE'])
def delete_user(users_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (users_id,))
    conn.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

# مشاهده سفارش‌ها
@app.route('/view_orders', methods=['GET', 'POST'])
def view_orders():
    conn = get_db()
    cursor = conn.cursor()
    # جستجو
    search_query = request.args.get('search', '')  # دریافت کوئری جستجو
    if search_query:
        cursor.execute('''
            SELECT * FROM orders
            WHERE order_id LIKE ? OR username LIKE ? OR status LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute('SELECT * FROM orders')
    orders = cursor.fetchall()

    # در صورت ارسال فرم برای افزودن یا ویرایش سفارش
    if request.method == 'POST':
        order_id = request.form.get('order_id')  # ID برای ویرایش
        status = request.form.get('status')

        if order_id:  # ویرایش وضعیت سفارش
            cursor.execute('''
                UPDATE orders
                SET status = ?
                WHERE order_id = ?
            ''', (status, order_id))
        conn.commit()
        return redirect('/view_orders')

    return render_template('view_orders.html', orders=orders, search_query=search_query)



# مشاهده گزارش‌ها
@app.route('/view_reports', methods=['GET'])
def view_reports():
    conn = get_db()
    cursor = conn.cursor()

    # گزارش فروش
    cursor.execute('''
        SELECT  SUM(total_price) AS total_sales
        FROM orders
        
    ''')
    sales_reports = cursor.fetchall()

    # گزارش کاربران
    cursor.execute('''
        SELECT username, COUNT(*) AS order_count
        FROM orders
        GROUP BY username
        ORDER BY order_count DESC
        LIMIT 5
    ''')
    user_reports = cursor.fetchall()

    # گزارش سفارش‌ها
    cursor.execute('''
        SELECT status, COUNT(*) AS count
        FROM orders
        GROUP BY status
    ''')
    order_status_reports = cursor.fetchall()

    return render_template(
        'view_reports.html',
        sales_reports=sales_reports,
        user_reports=user_reports,
        order_status_reports=order_status_reports
    )

@app.route('/user_dashboard')
def user_dashboard():
    if 'role' in session and session['role'] == 'user':
        username = session.get('username')
        conn = get_db()
        cursor = conn.cursor()

        # دریافت محصولات
        cursor.execute("SELECT id, name, description, price, image_path FROM products")
                # دریافت محصولات با وضعیت علاقه‌مندی
        cursor.execute('''
            SELECT 
                p.id, 
                p.name, 
                p.description, 
                p.price, 
                p.image_path, 
                CASE WHEN w.product_id IS NOT NULL THEN 1 ELSE 0 END AS in_wishlist
            FROM products p
            LEFT JOIN wishlist w ON p.id = w.product_id AND w.user_id = ?
        ''', (username,))
        products = cursor.fetchall()

        # دریافت سفارشات با نام محصول
        cursor.execute('''
            SELECT o.id AS order_id, p.name AS product_name,o.quantity, o.status, p.price AS product_price, p.image_path
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.username = ?
        ''', (username,))
        orders = cursor.fetchall()
        cursor.execute('''
            SELECT COALESCE(SUM(p.price* o.quantity), 0)
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.username = ?
        ''', (username,))
        total_price = cursor.fetchone()[0]

        conn.close()
        return render_template('user_dashboard.html', products=products, orders=orders,total_price=total_price)
    elif 'role' in session and session['role'] == 'admin':
        return redirect('/admin_dashboard')
    return "Access denied!", 403



# ------------------ Products ------------------

def create_product_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category_id INTEGER,
            image_path BLOB
            
        )
    ''')
    conn.commit()
    conn.close()
    
def add_product(name, description, price, stock, category_id,image_path):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, description, price, stock, category_id,image_path) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, price, stock, category_id,image_path))
    conn.commit()
    conn.close()

@app.route('/add_product', methods=['POST'])
def add_product_route():
    product_data = request.get_json()
    file = request.files['image']
    if file:
        filename = file.filename
        filepath = os.path.join('static/uploads', filename)
        file.save(filepath)  # ذخیره فایل در سرور
        image_path = 'uploads/' + filename
    add_product(
        product_data.get('name'),
        product_data.get('description', ''),
        product_data.get('price'),
        product_data.get('stock'),
        product_data.get('category_id'),
        product_data.get('image_path')
    )

    return jsonify({"message": "Product added successfully!"}), 201

@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('user_dashboard.html', products=products)

@app.route('/manage_products', methods=['GET', 'POST'])
def manage_products():
    conn = get_db()
    cursor = conn.cursor()

    # نمایش لیست محصولات
    if request.method == 'GET':
        cursor.execute('SELECT id, name, description, price, image_path FROM products')
        products = cursor.fetchall()
        return render_template('manage_products.html', products=products)

    # افزودن محصول جدید
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock= request.form.get('stock')
        category_id = request.form.get('category_id')
        file = request.files['image_path']  # مسیر تصویر
        # بررسی فرمت فایل
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f'uploads/{filename}'

            cursor.execute('''
                INSERT INTO products (name, description, price,stock, category_id, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
             ''', (name, description, float(price),stock, category_id, image_path))
            conn.commit()
            flash('Product added successfully!', 'success')
        else:
            flash('Invalid file format!', 'danger')
                              
        return redirect('/manage_products')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        return render_template('edit_product.html', product=product)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        file = request.files['image_path']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f'uploads/{filename}'
            cursor.execute('''
                UPDATE products
                SET name = ?, description = ?, price = ?, image_path = ?
                WHERE id = ?
            ''', (name, description, float(price), image_path, product_id))
            conn.commit()
            return redirect('/manage_products')

@app.route('/delete_product/<int:product_id>', methods=['GET'])
def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    return redirect('/manage_products')


# ------------------ Orders ------------------


@app.route('/order', methods=['POST'])
def order():
    if 'role' in session and session['role'] == 'user':
        username = session.get('username')
        product_id = request.form.get('product_id')  # دریافت product_id از فرم
        quantity = int(request.form.get('quantity',1))
        conn = get_db()
        cursor = conn.cursor()

        # دریافت قیمت محصول از جدول products با استفاده از product_id
        cursor.execute('''
            SELECT price 
            FROM products 
            WHERE id = ?
        ''', (product_id,))
        product = cursor.fetchone()
        
        if product is None:
            conn.close()
            return "Product not found!", 404
        
        product_price = product[0]  # قیمت محصول

        # ثبت سفارش در جدول orders
        cursor.execute('''
            INSERT INTO orders (username, product_id, status, total_price,quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, product_id, 'Pending', product_price,quantity))

        conn.commit()
        conn.close()

        return redirect('/user_dashboard')
    return "Access denied!", 403

@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if 'role' in session and session['role'] == 'user':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return redirect('/user_dashboard')  # بازگشت به داشبورد کاربر
    return "Access denied!", 403












def create_order_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_order(email, total_price):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (email, total_price) 
        VALUES (?, ?)
    ''', (email, total_price))
    conn.commit()
    conn.close()

@app.route('/create_order', methods=['POST'])
def create_order_route():
    order_data = request.get_json()
    add_order(
        order_data['username'],
        order_data['total_price']
    )
    

    return jsonify({"message": "Order created successfully!"}), 201


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()  # دریافت داده از درخواست
    product_id = data.get('product_id')
    user_id = session.get('user_id')  # فرض می‌کنیم که شناسه کاربر در session ذخیره شده است

    if not user_id:
        return jsonify({'error': 'User not logged in'}), 400

    # ذخیره کردن سفارش در پایگاه داده
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, product_id)
        VALUES (?, ?)
    ''', (user_id, product_id))
    conn.commit()

    return jsonify({'message': 'Product added to cart'}), 200

@app.route('/cart')
def cart():
    user_id = session.get('user_id')  # شناسه کاربر از session

    if not user_id:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.description, p.price, p.image_path
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
    ''', (user_id,))
    products = cursor.fetchall()

    return render_template('cart.html', products=products)




@app.route('/add_to_order', methods=['POST'])
def add_to_order():
    user_id = session.get('user_id')  # شناسه کاربر از session
    product_id = int(request.form.get('product_id'))  # شناسه محصول از فرم

    if not user_id:
        return jsonify({'error': 'User not logged in'}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    # اضافه کردن سفارش به جدول
    cursor.execute('''
        INSERT INTO orders (user_id, product_id)
        VALUES (?, ?)
    ''', (user_id, product_id))
    conn.commit()
    conn.close()

    return redirect('/user_dashboard')  # بازگشت به داشبورد کاربر

@app.route('/payment_gateway')
def payment_gateway():
    return "Secure Payment Gateway Coming Soon!"

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'role' in session and session['role'] == 'user':
        username = session.get('username')

        conn = get_db()
        cursor = conn.cursor()

        message = None
        # دریافت اطلاعات کاربر قبل از متد POST
        cursor.execute('''
            SELECT username, email FROM users WHERE username = ?
        ''', (username,))
        user_info = cursor.fetchone()

        if request.method == 'POST':
            new_username = request.form.get('username')
            new_email = request.form.get('email')
            new_password = request.form.get('password')

            # به‌روزرسانی اطلاعات کاربر
            cursor.execute('''
                UPDATE users 
                SET username = ?, email = ?, password = ?
                WHERE username = ?
            ''', (new_username, new_email, new_password, username))

            conn.commit()
            session['username'] = new_username  # به‌روزرسانی سشن
            message = "Profile updated successfully!"

            # به‌روزرسانی اطلاعات کاربر برای نمایش
            user_info = (new_username, new_email)

        conn.close()
        return render_template('profile.html', user=user_info, message=message)
    return "Access Denied", 403

@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    if 'user_id' in session:
        user_id = session['user_id']
        product_id = request.form['product_id']

        conn = get_db()
        cursor = conn.cursor()

        # بررسی وجود محصول در wishlist
        cursor.execute('SELECT COUNT(*) FROM wishlist WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'message': 'Product already in wishlist!'})

        # اضافه کردن محصول به wishlist
        cursor.execute('INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)', (user_id, product_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Product added to wishlist!'})
    return jsonify({'error': 'Unauthorized'}), 401


@app.route('/wishlist')
def wishlist():
    if 'role' in session and session['role'] == 'user':
        username = session.get('username')
        
        conn = get_db()
        cursor = conn.cursor()

        # پیدا کردن user_id از نام کاربری
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        username = cursor.fetchone()[0]

        # دریافت محصولات از لیست علاقه‌مندی‌ها
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.price, p.image_path
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_id = ?
        ''', (username,))
        
        wishlist_products = cursor.fetchall()
        conn.close()

        return render_template('wishlist.html', wishlist_products=wishlist_products)
    return "Access denied!", 403

@app.route('/toggle_wishlist/<int:product_id>', methods=['POST'])
def toggle_wishlist(product_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    # بررسی وجود محصول در علاقه‌مندی
    cursor.execute('SELECT 1 FROM wishlist WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    exists = cursor.fetchone()

    if exists:
        # حذف از علاقه‌مندی
        cursor.execute('DELETE FROM wishlist WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    else:
        # اضافه کردن به علاقه‌مندی
        cursor.execute('INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)', (user_id, product_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True})



@app.route('/delete_wishlist/<int:product_id>', methods=['POST'])
def delete_wishlist(product_id):
    if 'role' in session and session['role'] == 'user':
        user_id = session.get('user_id')  # گرفتن نام کاربری از سشن
        conn = get_db()
        cursor = conn.cursor()
        
        # حذف محصول از ویش‌لیست کاربر
        cursor.execute("DELETE FROM wishlist WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        conn.commit()
        conn.close()

        flash("Product removed from wishlist!", "success")
        return redirect(url_for('wishlist'))  # بازگشت به صفحه ویش‌لیست
    else:
        return "Access Denied", 403



if __name__ == '__main__':
    create_user_table()
    create_product_table()
    create_order_table()
    app.run(host="0.0.0.0", port=5000, debug=True)
