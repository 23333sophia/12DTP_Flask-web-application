

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



# discograhpy route
@app.route("/discography")
def discography():
    if 'user' not in session:
        return redirect('/login')

    album_sql = "SELECT * FROM album ORDER BY album_id DESC"
    all_albums = query_db(album_sql)

    # list for songs to go in each albums
    disco_data = []

    if all_albums:
        for album in all_albums:
            current_album_id = album[0]
            song_sql = "SELECT * FROM song WHERE album_id = ?"
            songs = query_db(song_sql, (current_album_id,))
            
            # saving datas as a set for convienience
            disco_data.append({
                'album_info': album,
                'song_list': songs if songs else []
            })

    return render_template("discography.html", disco_data=disco_data)







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




# inventory system

# to  add a member to the inventory
@app.route("/add_to_inventory/<int:member_id>", methods=["POST"])
def add_to_inventory(member_id):
    if 'user' not in session or session['user'] is None:
        flash("Please log in first to add to inventory")
        return redirect('/login')
        
    user_id = session['user'][0]
    
    # to create an empty list if user doesnt have a list yet
    if 'inventory' not in session:
        session['inventory'] = []

 # saving produt to current inventory and saving to session so you cant 중복
    current_inventory = session['inventory']

    #saving saved item in a n-n way 
    item = str(user_id) + "-" + str(member_id)


    if item not in current_inventory:
        current_inventory.append(item)
        session['inventory'] = current_inventory
        flash("Added to your inventory.")
    else:
        flash("This already exists in your inventory.")

    return redirect('/inventory')



# displaying items in inventory
@app.route("/inventory")
def inventory():
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user'][0]
    
    # getting list of member ids saved in current session
    inventory_items_raw = session.get('inventory', [])
    inventory_members = []

    #spliting ids from the n-n position to check conditions-which item it is
    for item in inventory_items_raw:
        if type(item) is not str:
            continue

        parts = item.split("-")
        item_user_id = int(parts[0])
        item_member_id = int(parts[1])
        
        # bringing specific members details from db using id after checking specific user
        if item_user_id == user_id:
            sql = "SELECT * FROM member WHERE member_id = ?"
            member_data = query_db(sql, (item_member_id,), one=True)
            if member_data:
                inventory_members.append(member_data)
    
    return render_template("inventory.html", inventory_items=inventory_members)



if __name__ == "__main__":
    app.run(debug=True, port=8080)