from flask import Flask, render_template, flash, redirect, request, url_for, session, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, HiddenField
from passlib.hash import sha256_crypt
from functools import wraps 
from flask import abort


app = Flask(__name__, template_folder='/Users/divine/Flaskworld/templates/')

# config MySQUL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Balija4real123$'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
Mysql = MySQL(app)

#Articles = Articles()


@app.route('/')
def page():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles_view():
    # Create cursor
    cur = Mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'NO Articles Found'
        return render_template('articles.html', msg=msg)
    #close connection
    cur.close()

#single article
@app.route('/article/<int:article_id>')
def article(article_id):
    # Create cursor
    cur = Mysql.connection.cursor()

    # Get article by ID
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [article_id])

    if result == 0:
        # If no article with the given ID is found, return a 404 error
        abort(404)

    article = cur.fetchone()

    # Close cursor
    cur.close()

    return render_template('article.html', article=article)



#register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

#user Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = Mysql.connection.cursor()
        cur.execute('INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s )',
                    (name, email, username, password))
        
        #commit to DB
        Mysql.connection.commit()

        #close connection
        cur.close()

        flash('You\'re now registered and can Login.')

        return redirect(url_for('register'))

    return render_template('register.html', form=form)

#user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create Cursor
        cur = Mysql.connection.cursor()

        #get user name
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #get stored hash
            data = cur.fetchone()
            password = data['password']

            #compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username']  = username


                flash('You\'re now logged in', 'success')
                return redirect(url_for('dashboard'))
             
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            #close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unathorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap
   


#logout
@app.route('/logout')
def logout():
    session.clear()
    flash ('you\'re now logged out', 'success')
    return redirect(url_for('login'))


#Dashboard      
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = Mysql.connection.cursor()

    # get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        # close cursor
        cur.close()

        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        # close cursor
        cur.close()

        return render_template('dashboard.html', msg=msg)



# Article form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=300)])
    body = StringField('Body', [validators.Length(min=30)])
    

    
#Add article    
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)   
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        cur = Mysql.connection.cursor()

        #create cursor
        cur.execute('INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)',
                    (title, body, session['username']))

        #commit to DB
        Mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

#Edit article    
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = Mysql.connection.cursor()

    #get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    #get form
    form = ArticleForm(request.form)

    #Populate article with form files
    form.title.data = article['title']
    form.body.data = article['body']


    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        cur = Mysql.connection.cursor()
        app.logger.info(title)

        #create cursor
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id ))
                    

        #commit to DB
        Mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

#Delete article  
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = Mysql.connection.cursor()

    #Execute
    result = cur.execute("DELETE FROM articles WHERE id = %s", [id])

     #commit to DB
    Mysql.connection.commit()

    #close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    app.secret_key='Havacci123 '
    app.run(debug=True)
