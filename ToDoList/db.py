import MySQLdb

db = MySQLdb.connect(host="localhost", user="shiva", db="mysql", read_default_file="~/.my.cnf")

db.query("SELECT * FROM Patient_Details")

r = db.store_result()

print(r.fetch_row(maxrows=0))