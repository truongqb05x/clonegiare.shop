from flask import Flask, render_template, redirect, url_for, session, send_from_directory, request, make_response
import os
from datetime import datetime
from .utils.db import get_db_connection
from .config import Config
from .routes.auth import auth_bp
from .routes.api import api_bp
from .routes.admin import admin_bp
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(Config)

# Apply ProxyFix for production environments
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

@app.before_request
def enforce_https():
    if not request.is_secure and Config.SESSION_COOKIE_SECURE:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

@app.route('/')
@app.route('/category/<slug>')
def index(slug=None):
    seo_data = {
        'title': 'FBStore - Shop Bán Acc Facebook, Via, Clone, BM Chất Lượng Số 1',
        'description': 'FBStore - Hệ thống cung cấp tài khoản Facebook, Via cổ, Clone, Fanpage, BM quảng cáo uy tín, chất lượng. Bảo hành 1 đổi 1, hỗ trợ 24/7.',
        'keywords': 'mua via facebook, mua clone facebook, mua bm, shop acc fb, tai khoan quang cao, via khang, clone gia re',
        'url': request.url,
        'image': 'https://fbstore.com/static/images/banner.jpg' 
    }
    
    if slug:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT name, description FROM categories WHERE slug = %s", (slug,))
                category = cursor.fetchone()
                if category:
                    seo_data['title'] = f"Mua {category['name']} - FBStore Chất Lượng Uy Tín"
                    if category['description']:
                         # Truncate description if too long or use it as is
                        seo_data['description'] = category['description']
                    seo_data['keywords'] += f", mua {category['name']}, {category['name']} gia re"
                
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"SEO Error: {e}")
                
    response = make_response(render_template('pages/index.html', seo=seo_data))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

# Public pages
@app.route('/api')
def api_page():
    return render_template('pages/api.html')

@app.route('/blog')
def blog():
    return render_template('pages/blog.html')

@app.route('/support')
def support():
    return render_template('pages/support.html')

# Auth-required pages
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('pages/profile.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('pages/history.html')

@app.route('/deposit')
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('pages/nap-tien.html')

@app.route('/order/<order_code>')
def order_details(order_code):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('pages/order-details.html')

@app.route('/sitemap.xml')
def sitemap():
    base_url = "https://fbstore.com" # Replace with actual domain from request.host_url if needed, but hardcoded for SEO consistency is often better or use request.url_root[:-1]
    
    # Static pages
    pages = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': '/deposit', 'priority': '0.9', 'changefreq': 'weekly'},
        {'loc': '/blog', 'priority': '0.7', 'changefreq': 'weekly'},
        {'loc': '/api', 'priority': '0.7', 'changefreq': 'monthly'},
        {'loc': '/support', 'priority': '0.6', 'changefreq': 'monthly'},
        {'loc': '/login', 'priority': '0.8', 'changefreq': 'monthly'},
        {'loc': '/history', 'priority': '0.8', 'changefreq': 'daily'},
        {'loc': '/profile', 'priority': '0.8', 'changefreq': 'weekly'},
    ]
    
    # Dynamic Categories
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT slug FROM categories WHERE status = 'active'")
            categories = cursor.fetchall()
            
            for cat in categories:
                pages.append({
                    'loc': f"/category/{cat['slug']}",
                    'priority': '0.9',
                    'changefreq': 'weekly'
                })
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Sitemap Error: {e}")

    # XML Construction
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for page in pages:
        sitemap_xml.append('    <url>')
        sitemap_xml.append(f'        <loc>{base_url}{page["loc"]}</loc>')
        sitemap_xml.append(f'        <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>')
        sitemap_xml.append(f'        <changefreq>{page["changefreq"]}</changefreq>')
        sitemap_xml.append(f'        <priority>{page["priority"]}</priority>')
        sitemap_xml.append('    </url>')
        
    sitemap_xml.append('</urlset>')
    
    response = make_response('\n'.join(sitemap_xml))
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/robots.txt')
def robots():
    return send_from_directory('../', 'robots.txt')

if __name__ == '__main__':
    app.run(debug=True)
