

from flask import Flask, render_template, request,flash, session, redirect, g
import sqlite3
#to generate and check password password hashes
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'bnd.db'

app = Flask(__name__)
#secret key needed gor sessions and flash messages
app.config['SECRET_KEY'] = "bnd"

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


# Routes

@app.route("/")
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')


@app.route("/discography")
def discography():
    if 'user' not in session:
        return redirect('/login')
    return render_template("discography.html")


@app.route("/cart")
def cart():
    if 'user' not in session:
        return redirect('/login')
    return render_template("cart.html")

#user sign up & login route
@app.route('/signup', methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        hashed_password = generate_password_hash(password, method='pbkdf2')

        
        sql = "INSERT INTO user (username, password) VALUES (?,?)"
        query_db(sql,(username, hashed_password))
        get_db().commit()
        flash("You are now signed up! Login to continue")
        return redirect('/login')
    return render_template('signup.html')


@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        sql = "SELECT * FROM user WHERE username = ?"
        user = query_db(query=sql, args=(username,), one=True)
        
        if user:
            if check_password_hash(user[2], password):
                session['user'] = user
                flash("Welcome!")
                return redirect('/')
            else:
                flash("Incorrect password")
        else:
            flash("Username does not exist")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session['user'] = None
    flash("Logged out")
    return redirect('/')





# profile page route
@app.route("/profile")
def profile():
    if 'user' not in session:
        return redirect('/login')
    
    return render_template("profile.html")

# to bring each member profile for product.html and not make html for each member
@app.route("/product/<int:member_id>")
def product(member_id):
    sql = "SELECT * FROM member WHERE member_id = ?" 
    member_data = query_db(sql, (member_id,), one=True)
    
    return render_template("product.html", member=member_data)



if __name__ == "__main__":
    app.run(debug=True, port=8080)
