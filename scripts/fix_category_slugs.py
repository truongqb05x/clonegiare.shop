import sys
sys.path.insert(0, 'd:/facebook/shop_account')
from src.utils.db import get_db_connection
import re

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

# Check current categories
cursor.execute("SELECT id, name, slug FROM categories")
cats = cursor.fetchall()
print("Current categories:")
for c in cats:
    print(f"  id={c['id']}, name={c['name']}, slug={c['slug']}")

# Fix null/empty slugs by generating from name
def make_slug(name):
    slug = name.lower()
    slug = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', slug)
    slug = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', slug)
    slug = re.sub(r'[ìíịỉĩ]', 'i', slug)
    slug = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', slug)
    slug = re.sub(r'[ùúụủũưừứựửữ]', 'u', slug)
    slug = re.sub(r'[ỳýỵỷỹ]', 'y', slug)
    slug = re.sub(r'[đ]', 'd', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug

updated = 0
for c in cats:
    if not c['slug']:
        new_slug = make_slug(c['name'])
        cursor.execute("UPDATE categories SET slug = %s WHERE id = %s", (new_slug, c['id']))
        print(f"  Fixed: id={c['id']}, name={c['name']} -> slug={new_slug}")
        updated += 1

conn.commit()
cursor.close()
conn.close()
print(f"\nDone. Updated {updated} categories.")
