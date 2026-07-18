from flask import Blueprint, render_template, request, session, url_for, jsonify, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from ..utils.db import get_db_connection
from mysql.connector import Error

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username_email = data.get('username')
        password = data.get('password')

        if not username_email or not password:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin.'}), 400

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s OR email = %s"
            cursor.execute(query, (username_email, username_email))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                if user['status'] == 'banned':
                    return jsonify({'success': False, 'message': 'Tài khoản của bạn đã bị khóa.'}), 403
                
                
                session.permanent = True  # Enable eternal session (1 year as per config)
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                
                return jsonify({'success': True, 'message': 'Đăng nhập thành công!', 'redirect': url_for('index')})
            else:
                return jsonify({'success': False, 'message': 'Tên đăng nhập hoặc mật khẩu không chính xác.'}), 401
        else:
            return jsonify({'success': False, 'message': 'Lỗi kết nối cơ sở dữ liệu.'}), 500

    return render_template('pages/login.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([fullname, email, password, confirm_password]):
        return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin.'}), 400

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Mật khẩu xác nhận không khớp.'}), 400

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email đã được sử dụng.'}), 400

        username = email.split('@')[0]
        password_hash = generate_password_hash(password)
        
        try:
            query = "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, 'user')"
            cursor.execute(query, (username, email, password_hash))
            conn.commit()
            
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO activity_logs (user_id, action) VALUES (%s, 'Đăng ký tài khoản mới')", (user_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Đăng ký thành công! Đang chuyển đến đăng nhập...'})
        except Error as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': f'Lỗi khi đăng ký: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Lỗi kết nối cơ sở dữ liệu.'}), 500

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
