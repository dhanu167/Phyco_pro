from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, widgets , IntegerField, SelectField
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.no_of_chance = 1

global D_conclusion,A_conclusion,S_conclusion

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'phyco_test'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


@app.route('/article/<string:id>/')
def article(id):

    cur = mysql.connection.cursor()


    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.length(min=6, max=50),validators.Email()])
    phno = IntegerField('Contact Number', widget=widgets.Input(input_type="tel"))
    dob = StringField('Date of birth', widget=widgets.Input(input_type="date"))
    gender = SelectField('Gender',choices=[('Male','Male'),('Female','Female'),('Others','Others')])
    no_sib = SelectField('No of Siblings', choices=[('0','0'),('1','1'),('2','2'),('3','3'),('4','4'),('5','More')])
    eq = StringField('Education Qualification',[validators.length(min=3, max = 10)])
    anual_in = SelectField('Anual Income',choices=[('1','Below 1,00,000'),('2','Above 1,00,000')])
    username = StringField('Username', [validators.length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')


class SearchForm(Form):
    search = SelectField('Search Query', choices=[('Addicted','Addicted'),('Not Addicted','Not Addicted')])
    iasearch = SelectField('Search Query', choices=[('Mild User','Mild User'),('Problematic User','Problematic User'),('Sever Addiction','Sever Addiction')])
    dassearch = SelectField('Search Query',choices=[('Normal','Normal'),('Moderate','Moderate'),('Severe','Severe'),('Extremely Severe','Extremely Severe')])


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        dob = form.dob.data
        phno = form.phno.data
        gender = form.gender.data
        no_sib = form.no_sib.data
        eq = form.eq.data
        anual_in = form.anual_in.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, dob, gender, no_sib, email, ph_no, eq, anual_in, username, password) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (name, dob, gender, no_sib, email, phno, eq, anual_in, username, password))

        mysql.connection.commit()

        cur.close()

        flash('Your now registered and can log in, Remember Your Username and Password', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('home'))

            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now Logged Out', 'success')
    return redirect(url_for('login'))


@app.route('/ga_search_query',methods=['GET', 'POST'])
@is_logged_in
def ga_search_query():
    search = ""
    form = SearchForm(request.form)
    if request.method == 'POST':
        search = form.search.data
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT ga.name,users.gender,users.dob,users.email,users.ph_no,score,result FROM `ga` INNER JOIN users ON ga.name = users.username WHERE result = '{adict}'".format(adict=search))

    users = cur.fetchall()

    if result > 0:
        return render_template('ga_search_query.html',details=users ,form=form)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('ga_search_query.html', msg=msg, form=form)


@app.route('/ia_search_query',methods=['GET', 'POST'])
@is_logged_in
def ia_search_query():
    iasearch = ""
    form = SearchForm(request.form)
    if request.method == 'POST':
        iasearch = form.iasearch.data
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT ia.name,users.gender,users.dob,users.email,users.ph_no,score,result,test_date FROM `ia` INNER JOIN users ON ia.name = users.username WHERE result = '{adict}'".format(adict=iasearch))

    users = cur.fetchall()

    if result > 0:
        return render_template('ia_search_query.html',details=users ,form=form)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('ia_search_query.html', msg=msg, form=form)


@app.route('/d_search_query',methods=['GET', 'POST'])
@is_logged_in
def d_search_query():
    dsearch = ""
    form = SearchForm(request.form)
    if request.method == 'POST':
        dsearch = form.dassearch.data
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT das.name,users.gender,users.dob,users.email,users.ph_no,D_score,D_result,test_date FROM `das` INNER JOIN users ON das.name = users.username WHERE D_result = '{adict}'".format(adict=dsearch))

    users = cur.fetchall()

    if result > 0:
        return render_template('d_search_query.html',details=users ,form=form)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('d_search_query.html', msg=msg, form=form)


@app.route('/a_search_query',methods=['GET', 'POST'])
@is_logged_in
def a_search_query():
    asearch = ""
    form = SearchForm(request.form)
    if request.method == 'POST':
        asearch = form.dassearch.data
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT das.name,users.gender,users.dob,users.email,users.ph_no,A_score,A_result,test_date FROM `das` INNER JOIN users ON das.name = users.username WHERE A_result = '{adict}'".format(adict=asearch))

    users = cur.fetchall()

    if result > 0:
        return render_template('a_search_query.html',details=users ,form=form)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('a_search_query.html', msg=msg, form=form)


@app.route('/s_search_query',methods=['GET', 'POST'])
@is_logged_in
def s_search_query():
    ssearch = ""
    form = SearchForm(request.form)
    if request.method == 'POST':
        ssearch = form.dassearch.data
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT das.name,users.gender,users.dob,users.email,users.ph_no,S_score,S_result,test_date FROM `das` INNER JOIN users ON das.name = users.username WHERE S_result = '{adict}'".format(adict=ssearch))

    users = cur.fetchall()

    if result > 0:
        return render_template('s_search_query.html',details=users ,form=form)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('s_search_query.html', msg=msg, form=form)


@app.route('/view_DAS')
@is_logged_in
def view_DAS():
    cur = mysql.connection.cursor()
    dasresult = cur.execute("SELECT * FROM das")

    dasusers = cur.fetchall()

    if dasresult > 0:
        return render_template('view_DAS.html', dasdetails=dasusers)
    else:
        msg = 'No User Found'
        cur.close()
        return render_template('view_DAS.html', msg=msg)


@app.route('/view_GA',methods=['GET', 'POST'])
@is_logged_in
def view_GA():

    cur = mysql.connection.cursor()
    garesult = cur.execute("SELECT * FROM ga")
    gausers = cur.fetchall()

    if garesult > 0:
        return render_template('view_GA.html',gadetails=gausers)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('view_GA.html', msg=msg)


@app.route('/view_IA')
@is_logged_in
def view_IA():
    cur = mysql.connection.cursor()
    garesult = cur.execute("SELECT * FROM ia")

    iausers = cur.fetchall()

    if garesult > 0:
        return render_template('view_IA.html', iadetails=iausers)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('view_IA.html', msg=msg)


@app.route('/view_users')
@is_logged_in
def view_users():
    cur = mysql.connection.cursor()
    userresult = cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    if userresult > 0:
        return render_template('view_users.html', gadetails=users)

    else:
        msg = 'No User Found'
        cur.close()
        return render_template('view_users.html', msg=msg)


@app.route('/dashboard')
@is_logged_in
def dashboard():
    if session["username"] != "admin":
        msg = 'Your not Authorised to enter Dashboard.'
        return render_template('home.html', msg=msg)
    else:
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM articles")

        articles = cur.fetchall()

        if result > 0:
            return render_template('dashboard.html', articles=articles)
        else:
            msg = 'No Articles Found'
            cur.close()
            return render_template('dashboard.html', msg=msg)


@app.route('/user_view')
@is_logged_in
def user_view():
    return render_template('user_view.html')


@app.route('/ga_view')
@is_logged_in
def ga_view():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM ga WHERE name = '{user}'".format(user=session["username"]))

    gaview = cur.fetchall()

    if result > 0:
        return render_template('gaview.html', gaview = gaview)
    else:
        msg = 'No Articles Found'
        cur.close()
        return render_template('gaview.html', msg=msg)


@app.route('/ia_view')
@is_logged_in
def ia_view():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM ia WHERE name = '{user}'".format(user=session["username"]))

    iaview = cur.fetchall()

    if result > 0:
        return render_template('iaview.html', iaview=iaview)
    else:
        msg = 'No Articles Found'
        cur.close()
        return render_template('iaview.html', msg=msg)


@app.route('/das_view')
@is_logged_in
def das_view():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM das WHERE name = '{user}'".format(user=session["username"]))

    dasview = cur.fetchall()

    if result > 0:
        return render_template('dasview.html', dasview=dasview)
    else:
        msg = 'No Articles Found'
        cur.close()
        return render_template('dasview.html', msg=msg)


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.length(min=30)])


@app.route('/add_article', methods = ['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        mysql.connection.commit()

        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form = form)


@app.route('/edit_article/<string:id>', methods = ['GET', 'POST'])
@is_logged_in
def edit_article(id):

    cur = mysql.connection.cursor()


    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()

    form = ArticleForm(request.form)


    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']


        cur = mysql.connection.cursor()
        app.logger.info(title)

        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))

        mysql.connection.commit()


        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):

    cur = mysql.connection.cursor()


    cur.execute("DELETE FROM articles WHERE id = %s", [id])


    mysql.connection.commit()


    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


questions = { "1" : { "question_type": "S","question" : " I found it hard to wind down ","options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "2" : { "question_type": "A","question" : " I was aware of dryness of my mouth", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "3" : { "question_type": "D","question" : " I couldn’t seem to experience any positive feeling at all","options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
	          "4" : { "question_type": "A","question" : " I experienced breathing difficulty (eg, excessively rapid breathing,breathlessness in the absence of physical exertion)","options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "5" : { "question_type": "D","question" : " I found it difficult to work up the initiative to do things", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "6" : { "question_type": "S",'question' : " I tended to over-react to situations ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "7" : { "question_type": "A",'question' : " I experienced trembling (eg, in the hands) ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "8" : { "question_type": "S",'question' : " I felt that I was using a lot of nervous energy ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "9" : { "question_type": "A",'question' : " I was worried about situations in which I might panic and make a fool of myself", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "10": { "question_type": "D",'question' : " I felt that I had nothing to look forward to ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "11": { "question_type": "S",'question' : " I found myself getting agitated ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "12": { "question_type": "S",'question' : " I found it difficult to relax ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "13": { "question_type": "D",'question' : " I felt down-hearted and blue ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "14": { "question_type": "S",'question' : " I was intolerant of anything that kept me from getting on with what I was doing ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "15": { "question_type": "A",'question' : " I felt I was close to panic ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "16": { "question_type": "D",'question' : " I was unable to become enthusiastic about anything", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "17": { "question_type": "D",'question' : " I felt I wasn’t worth much as a person ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "18": { "question_type": "S",'question' : " I felt that I was rather touchy ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "19": { "question_type": "A",'question' : " I was aware of the action of my heart in the absence of physicalexertion (eg,sense of heart rate increase, heart missing a beat) ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "20": { "question_type": "A",'question' : " I felt scared without any good reason ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"},
              "21": { "question_type": "D",'question' : " I felt that life was meaningless ", "options": ["Never","Sometimes","Often","Almost Always"],"answer" : "Almost Always"}


            }


@app.route('/take_test')
@is_logged_in
def take_test():
    return render_template('take_test.html')


@app.route('/DAS', methods=['GET', 'POST'])
@is_logged_in
def DAS():
    if request.method == "POST":
        if "question" in session:
            entered_answer = request.form.get('answer', '')
            question_type = questions[session["question"]]["question_type"]
            if questions.get(session["question"], False):
                if question_type == "A":
                    if entered_answer == "Never":
                        A_mark = 0
                        session["A_mark"] += A_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))

                    if entered_answer == "Sometimes":
                        A_mark = 1
                        session["A_mark"] += A_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))


                    if entered_answer == "Often":
                        A_mark = 2
                        session["A_mark"] += A_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))


                    if entered_answer == "Almost Always":
                        A_mark = 3
                        session["A_mark"] += A_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))



                if question_type == "D":
                    if entered_answer == "Never":
                        D_mark = 0
                        session["D_mark"] += D_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))


                    if entered_answer == "Sometimes":
                        D_mark = 1
                        session["D_mark"] += D_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))

                    if entered_answer == "Often":
                        D_mark = 2
                        session["D_mark"] += D_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))


                    if entered_answer == "Almost Always":
                        D_mark = 3
                        session["D_mark"] += D_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))



                if question_type == "S":
                    if entered_answer == "Never":
                        S_mark = 0
                        session["S_mark"] += S_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))


                    if entered_answer == "Sometimes":
                        S_mark = 1
                        session["S_mark"] += S_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))


                    if entered_answer == "Often":
                        S_mark = 2
                        session["S_mark"] += S_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))


                    if entered_answer == "Almost Always":
                        S_mark = 3
                        session["S_mark"] += S_mark
                        session["question"] = str(int(session["question"]) + 1)
                        if session["question"] in questions:
                            redirect(url_for('DAS'))

            else:
                A_score = session["A_mark"]
                D_score = session["D_mark"]
                S_score = session["S_mark"]

                user = session["username"]
                cur = mysql.connection.cursor()

                if A_score >= 0 and A_score <= 3:
                    A_result = "Normal"
                elif A_score >= 4 and A_score <= 5:
                    A_result = "Mild"
                elif A_score >= 6 and A_score <= 7:
                    A_result = "Moderate"
                elif A_score >= 8 and A_score <= 9:
                    A_result = "Severe"
                elif A_score >= 10:
                    A_result = "Extremely Severe"

                if S_score >= 0 and S_score <= 7:
                    S_result = "Normal"
                elif S_score >= 8 and S_score <= 9:
                    S_result = "Mild"
                elif S_score >= 10 and S_score <= 12:
                    S_result = "Moderate"
                elif S_score >= 13 and S_score <= 16:
                    S_result = "Severe"
                elif S_score >= 17:
                    S_result = "Extremely Severe"

                if D_score >= 0 and D_score <= 7:
                    D_result = "Normal"
                elif D_score >= 8 and D_score <= 9:
                    D_result = "Mild"
                elif D_score >= 10 and D_score <= 12:
                    D_result = "Moderate"
                elif D_score >= 13 and D_score <= 16:
                    D_result = "Severe"
                elif D_score >= 17:
                    D_result = "Extremely Severe"

                cur.execute(
                    "INSERT INTO das(name, D_score, A_score, S_score, D_result, A_result, S_result) VALUES(%s, %s, %s, %s, %s, %s, %s)",
                    (user, D_score, A_score, S_score, D_result, A_result, S_result))

                mysql.connection.commit()

                cur.close()

                return render_template("score.html", A_score=session["A_mark"], S_score=session["S_mark"],
                                       D_score=session["D_mark"],D_result = D_result,A_result = A_result,S_result = S_result)


    if "question" not in session:
        session["question"] = "1"
        session["A_mark"] = 0
        session["D_mark"] = 0
        session["S_mark"] = 0

    elif session["question"] not in questions:
        A_score = session["A_mark"]
        D_score = session["D_mark"]
        S_score = session["S_mark"]

        user = session["username"]
        cur = mysql.connection.cursor()

        if A_score >= 0 and A_score <= 3:
            A_result = "Normal"
        elif A_score >= 4 and A_score <= 5:
            A_result = "Mild"
        elif A_score >= 6 and A_score <= 7:
            A_result = "Moderate"
        elif A_score >= 8 and A_score <= 9:
            A_result = "Severe"
        elif A_score >= 10:
            A_result = "Extremely Severe"

        if S_score >= 0 and S_score <= 7:
            S_result = "Normal"
        elif S_score >= 8 and S_score <= 9:
            S_result = "Mild"
        elif S_score >= 10 and S_score <= 12:
            S_result = "Moderate"
        elif S_score >= 13 and S_score <= 16:
            S_result = "Severe"
        elif S_score >= 17:
            S_result = "Extremely Severe"

        if D_score >= 0 and D_score <= 7:
            D_result = "Normal"
        elif D_score >= 8 and D_score <= 9:
            D_result = "Mild"
        elif D_score >= 10 and D_score <= 12:
            D_result = "Moderate"
        elif D_score >= 13 and D_score <= 16:
            D_result = "Severe"
        elif D_score >= 17:
            D_result = "Extremely Severe"

        cur.execute("INSERT INTO das(name, D_score, A_score, S_score, D_result, A_result, S_result) VALUES(%s, %s, %s, %s, %s, %s, %s)",(user, D_score, A_score, S_score, D_result, A_result, S_result))

        mysql.connection.commit()

        cur.close()

        return render_template("score.html",A_score=session["A_mark"],S_score=session["S_mark"],D_score=session["D_mark"],D_result = D_result,A_result = A_result,S_result = S_result)


    return render_template('quiz.html',question=questions[session["question"]]["question"],question_number=session["question"],options=questions[session["question"]]["options"],A_score=session["A_mark"],D_score=session["D_mark"],S_score=session["S_mark"])


gaming_questions = {  "1" : { "questions" : " Over time, have you been spending much more time playing video games, learning about video game playing, or planning the next opportunity to play? ","options": ["Yes","No"],"answer" : "Yes"},
                      "2" : { "questions" : " Do you need to spend more time and money on video games in order to feel the same amount of excitement as other activities in your life?", "options": ["Yes","No"],"answer" : "Yes"},
                      "3" : { "questions" : " Have you tried to play video games for shorter durations of times but have been unsuccessful?","options": ["Yes","No"],"answer" : "Yes"},
                      "4" : { "questions" : " Do you become restless or irritable when you attempt to cut down or stop playing video games?","options": ["Yes","No"],"answer" : "Yes"},
                      "5" : { "questions" : " Have you played video games as a way to escape problems or negative feelings?", "options": ["Yes","No"],"answer" : "Yes"},
                      "6" : { 'questions' : " Have you lied to family or friends about how much you play video games? ", "options": ["Yes","No"],"answer" : "Yes"},
                      "7" : { 'questions' : " Have you ever stolen a video games from a store or a friend, or stolen money to buy a video game? ", "options": ["Yes","No"],"answer" : "Yes"},
                      "8" : { 'questions' : " Do you sometimes skip household chores in order to play more video games? ", "options": ["Yes","No"],"answer" : "Yes"},
                      "9" : { 'questions' : " Do you sometimes skip homework or work in order to play more video games?", "options": ["Yes","No"],"answer" : "Yes"},
                      "10": { 'questions' : " Have you ever done poorly on a school assignment, test or work assignment because you have spent so much time playing video games? ", "options": ["Yes","No"],"answer" : "Yes"},
                      "11": { 'questions' : " Have you ever needed friends or family to give you extra money because you've spent too much of your own money on video games, software, or game internet fees?  ", "options": ["Yes","No"],"answer" : "Yes"},

                  }


@app.route('/GA', methods=['GET', 'POST'])
@is_logged_in
def GA():
    if request.method == "POST":
        if "q" in session:
            entered_answer = request.form.get('answer', '')
            if gaming_questions.get(session["q"], False):
                if entered_answer == "Yes":
                    mark = 1
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["q"] = str(int(session["q"]) + 1)
                    if session["q"] in gaming_questions:
                        redirect(url_for('GA'))
                    else:
                        score = session["mark"]
                        if score <= 6:
                            conclusion = "Not Addicted"
                        else:
                            conclusion = "Addicted"

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ga(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()
                        return render_template("gascore.html", score=session["mark"])

                if entered_answer == "No":
                    mark = 0
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["q"] = str(int(session["q"]) + 1)
                    if session["q"] in gaming_questions:
                        redirect(url_for('GA'))
                    else:
                        score = session["mark"]
                        if score <= 6:
                            conclusion = "Not Addicted"
                        else:
                            conclusion = "Addicted"

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ga(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()

                        return render_template("gascore.html", score=session["mark"])


            else:
                score = session["mark"]
                if score <= 6:
                    conclusion = "Not Addicted"
                else:
                    conclusion = "Addicted"

                user = session["username"]
                cur = mysql.connection.cursor()

                cur.execute("INSERT INTO ga(name, score, result) VALUES(%s, %s, %s)",
                            (user, score, conclusion))

                mysql.connection.commit()

                cur.close()

                return render_template("gascore.html", score=session["mark"])

    if "q" not in session:
        session["q"] = "1"
        session["mark"] = 0

    elif session["q"] not in gaming_questions:
        score = session["mark"]
        if score <= 6:
            conclusion = "Not Addicted"
        else:
            conclusion = "Addicted"

        user = session["username"]
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO ga(name, score, result) VALUES(%s, %s, %s)",
                    (user, score, conclusion))

        mysql.connection.commit()

        cur.close()

        return render_template("gascore.html",score=session['mark'])

    return render_template('gaquiz.html', q=gaming_questions[session["q"]]["questions"],
                           question_number=session["q"],
                           options=gaming_questions[session["q"]]["options"], score=session["mark"])


internet_questions = {"1" : { "questions" : " How often do you find that you stay online longer than you intended? ","options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "2" : { "questions" : " How often do you neglect household chores to spend more time online?", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "3" : { "questions" : " How often do you prefer the excitement of the Internet to intimacy with your partner?","options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "4" : { "questions" : " How often do you form new relationships with fellow online users?","options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "5" : { "questions" : " How often do others in your life complain to you about the amount of time you spend online?", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "6" : { 'questions' : " How often do your grades or school work suffer because of the amount of time you spend online? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "7" : { 'questions' : " How often do you check your e-mail before something else that you need to do? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "8" : { 'questions' : " How often does your job performance or productivity suffer because of the Internet? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "9" : { 'questions' : " How often do you become defensive or secretive when anyone asks you what you do online?", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "10": { 'questions' : " How often do you block out disturbing thoughts about your life with soothing thoughts of the Internet? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "11": { 'questions' : " How often do you find yourself anticipating when you will go online again?  ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "12": { "questions" : " How often do you fear that life without the Internet would be boring, empty, and joyless?", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "13": { "questions" : " How often do you snap, yell, or act annoyed if someone bothers you while you are online?","options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "14": { "questions" : " How often do you lose sleep due to late-night log-ins?","options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "15": { "questions" : " How often do you feel preoccupied with the Internet when off-line, or fantasize about being online?", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "16": { 'questions' : " How often do you find yourself saying \"just a few more minutes\" when online? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "17": { 'questions' : " How often do you try to cut down the amount of time you spend online and fail? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "18": { 'questions' : " How often do you try to hide how long you've been online? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "19": { 'questions' : " How often do you choose to spend more time online over going out with others?", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                      "20": { 'questions' : " How often do you feel depressed, moody, or nervous when you are off-line, which goes away once you are back online? ", "options": ["Not Applicable","Rarely","Occasionally","Frequently","Often","Always"],"answer" : "Yes"},
                  }


@app.route('/IA', methods=['GET', 'POST'])
@is_logged_in
def IA():
    if request.method == "POST":
        if "questions" in session:
            entered_answer = request.form.get('answer', '')
            if internet_questions.get(session["questions"], False):
                if entered_answer == "Not Applicable":
                    mark = 0
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["questions"] = str(int(session["questions"]) + 1)
                    if session["questions"] in internet_questions:
                        redirect(url_for('IA'))
                    else:
                        score = session["mark"]
                        if score < 50:
                            conclusion = "Mild User"
                        elif score >= 50 and score <= 79:
                            conclusion = "Problematic User"
                        elif score >= 80 and score <= 100:
                            conclusion = "Sever Addiction "

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()
                        return render_template("iascore.html", score=session["mark"])

                if entered_answer == "Rarely":
                    mark = 1
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["questions"] = str(int(session["questions"]) + 1)
                    if session["questions"] in internet_questions:
                        redirect(url_for('IA'))
                    else:
                        score = session["mark"]
                        if score < 50:
                            conclusion = "Mild User"
                        elif score >= 50 and score <= 79:
                            conclusion = "Problematic User"
                        elif score >= 80 and score <= 100:
                            conclusion = "Sever Addiction "

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()
                        return render_template("iascore.html", score=session["mark"])

                if entered_answer == "Occasionally":
                    mark = 2
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["questions"] = str(int(session["questions"]) + 1)
                    if session["questions"] in internet_questions:
                        redirect(url_for('IA'))
                    else:
                        score = session["mark"]
                        if score < 50:
                            conclusion = "Mild User"
                        elif score >= 50 and score <= 79:
                            conclusion = "Problematic User"
                        elif score >= 80 and score <= 100:
                            conclusion = "Sever Addiction "

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()
                        return render_template("iascore.html", score=session["mark"])

                if entered_answer == "Frequently":
                    mark = 3
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["questions"] = str(int(session["questions"]) + 1)
                    if session["questions"] in internet_questions:
                        redirect(url_for('IA'))
                    else:
                        score = session["mark"]
                        if score < 50:
                            conclusion = "Mild User"
                        elif score >= 50 and score <= 79:
                            conclusion = "Problematic User"
                        elif score >= 80 and score <= 100:
                            conclusion = "Sever Addiction "

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()
                        return render_template("iascore.html", score=session["mark"])

                if entered_answer == "Often":
                    mark = 4
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["questions"] = str(int(session["questions"]) + 1)
                    if session["questions"] in internet_questions:
                        redirect(url_for('IA'))
                    else:
                        score = session["mark"]
                        if score < 50:
                            conclusion = "Mild User"
                        elif score >= 50 and score <= 79:
                            conclusion = "Problematic User"
                        elif score >= 80 and score <= 100:
                            conclusion = "Sever Addiction "

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()
                        return render_template("iascore.html", score=session["mark"])

                if entered_answer == "Always":
                    mark = 5
                    session["mark"] += mark
                    app.no_of_chance = 1
                    session["questions"] = str(int(session["questions"]) + 1)
                    if session["questions"] in internet_questions:
                        redirect(url_for('IA'))
                    else:
                        score = session["mark"]
                        if score < 50:
                            conclusion = "Mild User"
                        elif score >= 50 and score <= 79:
                            conclusion = "Problematic User"
                        elif score >= 80 and score <= 100:
                            conclusion = "Sever Addiction "

                        user = session["username"]
                        cur = mysql.connection.cursor()

                        cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                                    (user, score, conclusion))

                        mysql.connection.commit()

                        cur.close()
                        return render_template("iascore.html", score=session["mark"])

            else:
                score = session["mark"]
                if score < 50:
                    conclusion = "Mild User"
                elif score >= 50 and score <= 79:
                    conclusion = "Problematic User"
                elif score >= 80 and score <= 100:
                    conclusion = "Sever Addiction"

                user = session["username"]
                cur = mysql.connection.cursor()

                cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                            (user, score, conclusion))

                mysql.connection.commit()

                cur.close()
                return render_template("iascore.html", score=session["mark"])


    if "questions" not in session:
        session["questions"] = "1"
        session["mark"] = 0

    elif session["questions"] not in internet_questions:
        score = session["mark"]
        if score < 50:
            conclusion = "Mild User"
        elif score >= 50 and score <= 79:
            conclusion = "Problematic User"
        elif score >= 80 and score <= 100:
            conclusion = "Sever Addiction "

        user = session["username"]
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO ia(name, score, result) VALUES(%s, %s, %s)",
                    (user, score, conclusion))

        mysql.connection.commit()

        cur.close()
        return render_template("iascore.html", score=session["mark"])


    return render_template('iaquiz.html',question=internet_questions[session["questions"]]["questions"],question_number=session["questions"],options=internet_questions[session["questions"]]["options"],score=session["mark"])


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)