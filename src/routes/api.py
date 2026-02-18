from flask import Blueprint, jsonify, session, request
from ..utils.db import get_db_connection

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/bank/active', methods=['GET'])
def get_active_bank():
    """Public endpoint - returns the first active bank for deposit page"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, bank_name, bank_code, account_number, account_name, qr_url FROM banks WHERE status = 'active' ORDER BY id ASC LIMIT 1")
        bank = cursor.fetchone()
        cursor.close()
        conn.close()
        if bank:
            return jsonify({'success': True, 'bank': bank})
        return jsonify({'success': False, 'error': 'No active bank configured'})
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/status', methods=['GET'])
def user_status():
    if 'user_id' in session:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT username, balance, role, fullname FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                return jsonify({
                    'logged_in': True,
                    'user': user
                })
    return jsonify({'logged_in': False})

@api_bp.route('/user/profile', methods=['GET'])
def get_user_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user details
        cursor.execute("""
            SELECT id, username, email, balance, role, fullname, phone, telegram_id, created_at 
            FROM users WHERE id = %s
        """, (user_id,))
        user_info = cursor.fetchone()
        
        if not user_info:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
        # Get wallet stats
        # Total Deposited
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total 
            FROM deposits 
            WHERE user_id = %s AND status = 'completed'
        """, (user_id,))
        deposit_stats = cursor.fetchone()
        total_deposited = deposit_stats['total']
        
        # Total Used (Completed purchases)
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total 
            FROM orders 
            WHERE user_id = %s
        """, (user_id,))
        usage_stats = cursor.fetchone()
        total_used = usage_stats['total']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'profile': user_info,
            'stats': {
                'total_deposited': float(total_deposited),
                'total_used': float(total_used)
            }
        })
        
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/user/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    fullname = data.get('fullname', '').strip()
    phone = data.get('phone', '').strip()
    telegram_id = data.get('telegram_id', '').strip()
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET fullname = %s, phone = %s, telegram_id = %s 
            WHERE id = %s
        """, (fullname, phone, telegram_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Cập nhật thông tin thành công'})
        
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

from werkzeug.security import check_password_hash, generate_password_hash

@api_bp.route('/user/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Vui lòng nhập đầy đủ thông tin'}), 400
        
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Mật khẩu mới phải có ít nhất 6 ký tự'}), 400
        
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password_hash'], current_password):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Mật khẩu hiện tại không đúng'}), 400
            
        new_hash = generate_password_hash(new_password)
        
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công'})
        
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# Existing Routes...
@api_bp.route('/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, slug, description, icon FROM categories WHERE status = 'active'")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(categories)
    return jsonify({'error': 'Database connection failed'}), 500

@api_bp.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, c.name as category_name, 
            (SELECT COUNT(*) FROM accounts a WHERE a.product_id = p.id AND a.status = 'live') as stock,
            (SELECT COUNT(*) FROM accounts a WHERE a.product_id = p.id AND a.status = 'sold') as sold_count
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active'
        """)
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(products)
    return jsonify({'error': 'Database connection failed'}), 500

@api_bp.route('/purchase', methods=['POST'])
def purchase():
    # Check authentication
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Vui lòng đăng nhập để tiếp tục'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id or quantity < 1:
        return jsonify({'success': False, 'error': 'Thông tin không hợp lệ'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Không thể kết nối cơ sở dữ liệu'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session['user_id']
        
        # Get user balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'error': 'Không tìm thấy thông tin người dùng'}), 404
        
        # Get product info
        cursor.execute("SELECT * FROM products WHERE id = %s AND status = 'active'", (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Sản phẩm không tồn tại hoặc đã ngừng bán'}), 404
        
        # Calculate total
        total_amount = float(product['price']) * quantity
        
        # Check balance
        if float(user['balance']) < total_amount:
            return jsonify({'success': False, 'error': f'Số dư không đủ. Bạn cần thêm {int(total_amount - float(user["balance"])):,}đ'}), 400
        
        # Check stock
        cursor.execute("SELECT COUNT(*) as available FROM accounts WHERE product_id = %s AND status = 'live'", (product_id,))
        stock_check = cursor.fetchone()
        if stock_check['available'] < quantity:
            return jsonify({'success': False, 'error': f'Sản phẩm chỉ còn {stock_check["available"]} tài khoản'}), 400
        
        # Generate order code
        import random
        import string
        order_code = 'ORD' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (order_code, user_id, product_name, total_amount, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_code, user_id, product['name'], total_amount, quantity))
        order_id = cursor.lastrowid
        
        # Get accounts from inventory
        cursor.execute("""
            SELECT id, content FROM accounts 
            WHERE product_id = %s AND status = 'live' 
            LIMIT %s
        """, (product_id, quantity))
        accounts = cursor.fetchall()
        
        # Mark accounts as sold and link to order
        account_data = []
        for account in accounts:
            cursor.execute("""
                UPDATE accounts SET status = 'sold', sold_at = NOW() 
                WHERE id = %s
            """, (account['id'],))
            
            cursor.execute("""
                INSERT INTO order_items (order_id, account_id, purchase_price)
                VALUES (%s, %s, %s)
            """, (order_id, account['id'], product['price']))
            
            account_data.append(account['content'])
        
        # Deduct balance
        new_balance = float(user['balance']) - total_amount
        cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
        
        # Log balance change
        cursor.execute("""
            INSERT INTO balance_history (user_id, amount_before, amount_change, amount_after, type, description)
            VALUES (%s, %s, %s, %s, 'purchase', %s)
        """, (user_id, user['balance'], -total_amount, new_balance, f'Purchase: {product["name"]} x{quantity}'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'order_code': order_code,
            'accounts': account_data,
            'total_amount': total_amount,
            'new_balance': float(new_balance)
        })
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/orders', methods=['GET'])
def get_orders():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    order_code = request.args.get('order_code', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    limit = int(request.args.get('limit', 10))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT order_code, product_name, quantity, total_amount, 
                   note, created_at 
            FROM orders 
            WHERE user_id = %s
        """
        params = [user_id]
        
        if order_code:
            query += " AND order_code LIKE %s"
            params.append(f'%{order_code}%')
        
        if date_from:
            query += " AND DATE(created_at) >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(created_at) <= %s"
            params.append(date_to)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'orders': orders})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/order/<order_code>', methods=['GET'])
def get_order_details(order_code):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get order info
        cursor.execute("""
            SELECT * FROM orders 
            WHERE order_code = %s AND user_id = %s
        """, (order_code, user_id))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get order items with account details
        cursor.execute("""
            SELECT oi.*, a.content as account_content
            FROM order_items oi
            JOIN accounts a ON oi.account_id = a.id
            WHERE oi.order_id = %s
        """, (order['id'],))
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'order': order,
            'items': items
        })
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/activity-logs', methods=['GET'])
def get_activity_logs():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    limit = int(request.args.get('limit', 20))
    action = request.args.get('action', '')
    ip_address = request.args.get('ip_address', '')
    date = request.args.get('date', '')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT action, ip_address, created_at 
            FROM activity_logs 
            WHERE user_id = %s 
        """
        params = [user_id]
        
        if action:
            query += " AND action LIKE %s"
            params.append(f'%{action}%')
            
        if ip_address:
            query += " AND ip_address LIKE %s"
            params.append(f'%{ip_address}%')
            
        if date:
            query += " AND DATE(created_at) = %s"
            params.append(date)
            
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/balance-history', methods=['GET'])
def get_balance_history():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    limit = int(request.args.get('limit', 20))
    description = request.args.get('description', '')
    date = request.args.get('date', '')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT type, amount_before, amount_change, amount_after, 
                   description, created_at 
            FROM balance_history 
            WHERE user_id = %s 
        """
        params = [user_id]
        
        if description:
            query += " AND description LIKE %s"
            params.append(f'%{description}%')
            
        if date:
            query += " AND DATE(created_at) = %s"
            params.append(date)
            
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/deposits', methods=['GET'])
def get_deposits():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    limit = int(request.args.get('limit', 10))
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, transaction_id, amount, method, status, created_at, is_notified
            FROM deposits 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (user_id, limit))
        deposits = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'deposits': deposits})
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/deposits/check-new', methods=['GET'])
def check_new_deposit():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        # Check for completed deposits that haven't been notified
        cursor.execute("""
            SELECT id, amount, transaction_id, method, created_at
            FROM deposits 
            WHERE user_id = %s AND status = 'completed' AND is_notified = 0
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        deposit = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if deposit:
            # Return details for the modal
            return jsonify({'success': True, 'new_deposit': True, 'deposit': deposit})
        else:
            return jsonify({'success': True, 'new_deposit': False})
            
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/deposits/mark-seen', methods=['POST'])
def mark_deposit_seen():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    deposit_id = data.get('deposit_id')
    
    if not deposit_id:
        return jsonify({'success': False, 'error': 'Missing deposit_id'}), 400
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE deposits SET is_notified = 1 WHERE id = %s AND user_id = %s", (deposit_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        if conn: conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500
