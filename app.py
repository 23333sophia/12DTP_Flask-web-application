

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

# dont allow users who have logged out access by clicking back in browser
@app.after_request
def add_no_cache_headers(response):
    """
    tells the browser not to cache any pages & forces a fresh server request when navigating back
    so dont allow users who have logged out access by clicking back in browser
    """
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response





#user sign up & login route
@app.route('/signup', methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        
        # requiring atleast a number and some character when signing up
        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        has_num = False
        has_letter = False

        for char in password:
            if char in numbers:
                has_num = True
            else:
                # considering all other than numbers are letters
                has_letter = True
        if has_num == False or has_letter == False:
            flash("Password must include both letters and numbers")
            return render_template('signup.html')
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
                # checking whether the account is disabled
                if user[3] == 0:
                    flash('Account disabled.')
                    return render_template('login.html')
                else:
                    session['user'] = user[1]       # saving username in session
                    session['user_id'] = user[0]    # saving users own id in db                
                    flash("Welcome!")
                    return redirect('/')
            else:
                flash("Incorrect password")
        else:
            flash("Username does not exist")
            
    return render_template('login.html')



@app.route('/logout')
def logout():
    # cleanly remove session keys instead of setting them to none
    session.pop('user', None)
    session.pop('user_id', None)
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





# displaying items in inventory
@app.route("/inventory")
def inventory():
    if 'user' not in session or session['user'] is None:
        flash("Log in to check your account")
        return redirect('/login')

    user_id = session.get('user_id')
    inventory_items_raw = session.get('inventory', [])
    inventory_members = []

    for item in inventory_items_raw:
        # checking boundaries- format safety to prevent crashes from bad data formats
        if type(item) is not str or "-" not in item:
            continue

        parts = item.split("-")
        # ensuring it split into exactly 2 parts (user_id and member_id)
        if len(parts) != 2:
            continue
            
        # try and except block to ensure the web app will not crash if data isn't a clean number
        try:
            item_user_id = int(parts[0])
            item_member_id = int(parts[1])
        except ValueError:
            continue  # skip to the next item if conversion fails
        
        # bringing specific members details from db using id after checking specific user
        if item_user_id == user_id:
            sql = "SELECT * FROM member WHERE member_id = ?"
            member_data = query_db(sql, (item_member_id,), one=True)
            if member_data:
                inventory_members.append(member_data)
    
    return render_template("inventory.html", inventory_items=inventory_members)





# to  add a member to the inventory
@app.route("/add_to_inventory/<int:member_id>", methods=["POST"])
def add_to_inventory(member_id):
    if 'user' not in session or session['user'] is None:
        flash("Please log in first to add to inventory")
        return redirect('/login')
        
    user_id = session['user_id']
    
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




if __name__ == "__main__":
    app.run(debug=True, port=8080)