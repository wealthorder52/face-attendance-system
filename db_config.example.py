import pymysql

def get_connection():
    return pymysql.connect(
        host='YOUR_HOST',
        user='YOUR_USERNAME',
        password='YOUR_PASSWORD',
        database='YOUR_DATABASE',
        port=3306
    )