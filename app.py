from flask import Flask, g, render_template
import sqlite3

DATABASE = 'bnd.db'

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv\



@app.route("/")
def home():
    sql = """SELECT * FROM members"""
    information = query.db(sql)
    #home page
    return render_template('profile.html')

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/login")
def login():
    return render_template("login.html")





# members app route
@app.route("/product/<name>")
def product(name):
    return render_template("product.html", name=name)




if __name__ == "__main__":
    app.run(debug=True, port=8080)