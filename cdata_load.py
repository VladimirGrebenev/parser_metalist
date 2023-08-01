import cdata.woocommerce as mod
from env import CONS_SEC, CONS_KEY, SITE_URL_UPLOAD

conn = mod.connect(
    f" Url={SITE_URL_UPLOAD};ConsumerKey={CONS_KEY};ConsumerSecret={CONS_SEC};")

cur = conn.execute("SELECT ALL FROM Products")
rs = cur.fetchall()
for row in rs:
    print(row)