import pymysql

def get_connection():
    return pymysql.connect(
        host='auth-db1873.hstgr.io',
        user='u500860565_office2026',
        password='Niveshcart@123',
        database='u500860565_office2026',
        port=3306,
        connect_timeout=10
    )