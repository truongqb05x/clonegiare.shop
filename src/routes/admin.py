from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from ..utils.db import get_db_connection
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/admin-dashboard.html', active_page='dashboard')

@admin_bp.route('/api/stats')
@admin_required
def get_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Total users
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user'")
        total_users = cursor.fetchone()['total']
        
        # 2. New users today
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user' AND DATE(created_at) = CURDATE()")
        new_users_today = cursor.fetchone()['total']
        
        # 3. Total orders
        cursor.execute("SELECT COUNT(*) as total FROM orders")
        total_orders = cursor.fetchone()['total']
        
        # 4. Monthly Revenue (January or Current Month)
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM orders 
            WHERE MONTH(created_at) = MONTH(CURRENT_DATE()) 
            AND YEAR(created_at) = YEAR(CURRENT_DATE())
        """)
        monthly_revenue = cursor.fetchone()['total']
        
        # 5. Recent orders
        cursor.execute("""
            SELECT o.order_code, u.username, o.product_name, o.total_amount, o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            LIMIT 5
        """)
        recent_orders = cursor.fetchall()
        
        # 6. Chart data - Orders last 7 days
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM orders
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at) ASC
        """)
        order_chart_data = cursor.fetchall()

        # 7. Recent user activities
        cursor.execute("""
            SELECT a.action, u.username, a.created_at
            FROM activity_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
            LIMIT 5
        """)
        recent_activities = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'new_users_today': new_users_today,
                'total_orders': total_orders,
                'monthly_revenue': f"{int(monthly_revenue):,}đ"
            },
            'recent_orders': recent_orders,
            'recent_activities': recent_activities,
            'charts': {
                'orders': order_chart_data
            }
        })
        
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/novery')
@admin_required
def novery():
    return render_template('admin/admin-novery.html', active_page='novery')

@admin_bp.route('/products')
@admin_required
def products():
    return render_template('admin/admin-products.html', active_page='products')

@admin_bp.route('/categories')
@admin_required
def categories():
    return render_template('admin/admin-categories.html', active_page='categories')

@admin_bp.route('/api/categories')
@admin_required
def get_categories():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/categories/add', methods=['POST'])
@admin_required
def add_category():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    icon = data.get('icon', 'fas fa-shopping-basket')
    status = data.get('status', 'active')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, description, icon, status) VALUES (%s, %s, %s, %s)",
            (name, description, icon, status)
        )
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/categories/update', methods=['POST'])
@admin_required
def update_category():
    data = request.json
    cat_id = data.get('id')
    name = data.get('name')
    description = data.get('description')
    icon = data.get('icon')
    status = data.get('status')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET name=%s, description=%s, icon=%s, status=%s WHERE id=%s",
            (name, description, icon, status, cat_id)
        )
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/categories/delete/<int:cat_id>', methods=['POST'])
@admin_required
def delete_category(cat_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id=%s", (cat_id,))
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/products')
@admin_required
def get_products():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        # Join with categories to get category name
        # Also count inventory (status = 'live') for each product
        cursor.execute("""
            SELECT p.*, c.name as category_name, 
                   (SELECT COUNT(*) FROM accounts a WHERE a.product_id = p.id AND a.status = 'live') as stock
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.created_at DESC
        """)
        products = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/products/add', methods=['POST'])
@admin_required
def add_product():
    data = request.json
    category_id = data.get('category_id')
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    status = data.get('status', 'active')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (category_id, name, description, price, status) VALUES (%s, %s, %s, %s, %s)",
            (category_id, name, description, price, status)
        )
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/products/update', methods=['POST'])
@admin_required
def update_product():
    data = request.json
    product_id = data.get('id')
    category_id = data.get('category_id')
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    status = data.get('status')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE products SET category_id=%s, name=%s, description=%s, price=%s, status=%s WHERE id=%s",
            (category_id, name, description, price, status, product_id)
        )
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        # Note: If product has accounts, schema says ON DELETE CASCADE for accounts
        # But if accounts are sold (linked to order_items), it might still fail if there's no cascade on order_items -> accounts
        cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/inventory')
@admin_required
def inventory():
    return render_template('admin/admin-inventory.html', active_page='inventory')

@admin_bp.route('/api/inventory')
@admin_required
def get_inventory():
    product_id = request.args.get('product_id')
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.*, p.name as product_name 
            FROM accounts a
            JOIN products p ON a.product_id = p.id
            WHERE a.status = 'live'
        """
        params = []
        if product_id and product_id != 'all':
            query += " AND a.product_id = %s"
            params.append(product_id)
            
        query += " ORDER BY a.created_at DESC LIMIT 100"
        
        cursor.execute(query, params)
        accounts = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'accounts': accounts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/inventory/import', methods=['POST'])
@admin_required
def import_inventory():
    data = request.json
    product_id = data.get('product_id')
    raw_data = data.get('data', '')
    
    if not product_id or product_id == 'all':
        return jsonify({'success': False, 'error': 'Vui lòng chọn sản phẩm'}), 400
        
    lines = [line.strip() for line in raw_data.split('\n') if line.strip()]
    if not lines:
        return jsonify({'success': False, 'error': 'Không có dữ liệu để nhập'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        for line in lines:
            cursor.execute(
                "INSERT INTO accounts (product_id, content, status) VALUES (%s, %s, %s)",
                (product_id, line, 'live')
            )
        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'count': len(lines)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/inventory/delete/<int:account_id>', methods=['POST'])
@admin_required
def delete_account(account_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE id=%s", (account_id,))
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/orders')
@admin_required
def orders():
    return render_template('admin/admin-orders.html', active_page='orders')

@admin_bp.route('/api/orders')
@admin_required
def get_orders():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        # Fetch orders with username
        cursor.execute("""
            SELECT o.*, u.username as customer_name 
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        """)
        orders = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'orders': orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/orders/<int:order_id>/items')
@admin_required
def get_order_items(order_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        # Fetch account details for this order
        cursor.execute("""
            SELECT oi.purchase_price, a.content
            FROM order_items oi
            JOIN accounts a ON oi.account_id = a.id
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/users')
@admin_required
def users():
    return render_template('admin/admin-users.html', active_page='users')

@admin_bp.route('/api/users')
@admin_required
def get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        # Fetch users - omit sensitive password_hash
        cursor.execute("SELECT id, username, email, balance, role, status, created_at FROM users ORDER BY id DESC")
        users = cursor.fetchall()
        cursor.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/users/update', methods=['POST'])
@admin_required
def update_user():
    data = request.json
    user_id = data.get('id')
    balance = data.get('balance')
    role = data.get('role')
    status = data.get('status')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET balance=%s, role=%s, status=%s WHERE id=%s",
            (balance, role, status, user_id)
        )
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/api/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        # Be careful when deleting users (might affect orders/logs)
        # Schema says ON DELETE CASCADE for orders and SET NULL for logs
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

@admin_bp.route('/banks')
@admin_required
def banks():
    return render_template('admin/admin-banks.html', active_page='banks')

@admin_bp.route('/deposits')
@admin_required
def deposits():
    return render_template('admin/admin-deposits.html', active_page='deposits')
