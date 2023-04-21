# flask library import edildi
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# reduce , map , filter , zip , any all gibi gömülü fonksiyonlar için kullanılır.
from functools import reduce, wraps
from flask_mysqldb import MySQL  # mysql database library
# form validation library
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt  # password encryption library

app = Flask(__name__)

app.secret_key = "ybblog"  # session için gerekli
app.config["MYSQL_HOST"] = "localhost"  # default host
app.config["MYSQL_PORT"] = 5430  # default port
app.config["MYSQL_USER"] = "root"   # default user
app.config["MYSQL_PASSWORD"] = ""  # default password
app.config["MYSQL_DB"] = "ybblog"  # default database
# dictionary formatında veri döndürür.
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


# mysql database connection  flask ile mysql bağlantısı yapıldı
mysql = MySQL(app)


# kullanıcı kayıt formu

class RegisterForm(Form):  # form classından türetildi inherit edildi
    name = StringField("İsim Soyisim", validators=[  # validators ile form validation işlemleri yapılır.
                       validators.Length(min=4, max=25)])

    email = StringField("e-mail",  # validators ile form validation işlemleri yapılır. # validators.Email(message="Lütfen geçerli bir e-mail adresi giriniz.")
                        validators=[validators.DataRequired(message="Lütfen bir e-mail adresi giriniz."),])

    userName = StringField("Kullanıcı Adı", validators=[  # validators ile form validation işlemleri yapılır.
        validators.Length(min=5, max=35)])

    password = PasswordField("Şifre", validators=[  # validators ile form validation işlemleri yapılır.
        # boş geçilemez alan için kullanılır. boş geçilirse hata mesajı verir.
        validators.DataRequired(message="Lütfen bir şifre belirleyiniz."),
        validators.EqualTo(fieldname="confirm", message="Parolanız Uyuşmuyor")])  # şifre ile şifre tekrarı aynı olmalı

    # yukardaki field ile aynı olmalı yoksa hata verir.
    confirm = PasswordField("Şifre Doğrula")


class LoginForm(Form):
    userName = StringField("Kullanıcı Adı", validators=[
                           validators.DataRequired(message="Lütfen bir kullanıcı adı giriniz.")])
    password = PasswordField("Şifre", validators=[
                             validators.DataRequired(message="Lütfen bir şifre giriniz.")])


class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[
                        validators.Length(min=5)])
    content = TextAreaField("Makale İçeriği", validators=[
                            validators.length(min=10)])
# Kullanıcı Giriş Decorator Kontrol DashBoard vs .


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ("logged_in" in session):
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız.", "danger")
            return redirect(url_for("login"))
    return decorated_function


def userList():
    users = list()
    users.append({"id": 1, "name": "Ali", "surname": "Veli"})
    users.append({"id": 2, "name": "Ayşe", "surname": "Fatma"})
    users.append({"id": 3, "name": "Ahmet", "surname": "Mehmet"})
    return users


@ app.route('/')
def index():
    users = userList()
    return render_template('index.html', islem=2, users=users)


@ app.route("/about")
def about():
    about = "This is about page"
    return render_template('about.html')


# string yerine int yazarsak sayısal değerlerde çalışır. path variable kullanımı
@ app.route("/article/<string:id>")
def article(id):

    cursor = mysql.connection.cursor()

    sorgu = "select * from articles where id = %s"

    result = cursor.execute(sorgu, (id))

    if (result > 0):
        article = cursor.fetchone()
        return render_template('article.html', article=article)
    else:
        return render_template('article.html')


@ app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    # method post ise formdan gelen verileri alır.
    # form validation işlemleri yapılır. # formdan gelen verileri alır. kontrol eder. geçerli ise kayıt işlemi yapılır.
    if request.method == "POST" and form.validate():

        name = form.name.data
        email = form.email.data
        userName = form.userName.data
        # şifre şifrelenir.
        password = sha256_crypt.encrypt(form.password.data)

        # mysql database bağlantısı
        cursor = mysql.connection.cursor()

        # sql sorgusu

        list = "select * from users"
        print("list" + list)
        cursor.execute(list)
        userList = cursor.fetchall()   # sorguyu çalıştırır.
        maxId = 1

        for i in userList:
            if (i["id"] > maxId):
                maxId = i["id"]
            elif (i["id"] == maxId):
                maxId = i["id"] + 1

        # %s yerine verileri sırayla yazılır. {} benzer
        sorgu = "Insert into users(id,name,email,username,password) VALUES(%s,%s,%s,%s,%s)"

        # verileri tuple formatında verir.
        cursor.execute(sorgu, (maxId, name, email, userName, password))
        mysql.connection.commit()  # transaction bitirir

        cursor.close()

        # flash mesajı gönderir. # success bootstrap classıdır.
        flash("Başarıyla kayıt oldunuz.", "success")

        # index sayfasına yönlendirir. # redirect ile yönlendirme yapılır.
        return redirect(url_for("login"))
    else:
        return render_template('register.html', form=form)


@ app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        userName = form.userName.data
        password = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "select * from users where username = %s"

        result = cursor.execute(sorgu, (userName,))

        if (result > 0):  # kullanıcı varsa
            user = cursor.fetchone()  # tek bir kayıt döndürür.
            if (sha256_crypt.verify(password, user["password"])):
                flash("Başarıyla giriş yaptınız.", "success")
                # session başlatır. # session ile kullanıcı bilgileri tutulur. key value tutar
                session["logged_in"] = True
                session["userName"] = userName
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz.", "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor.", "danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yapıldı.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
# session açık değilse burayı kullanamaz böylece istek attığında görmesini istemediğimiz methodları ortak olarak decoratorda kontrol edebiliriz.
@login_required
def dashboard():

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s"

    results = cursor.execute(sorgu, (session["userName"],))

    if (results > 0):
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")


@app.route("/addArticle", methods=["GET", "POST"])
def addArticle():
    form = ArticleForm(request.form)
    if (request.method == "POST" and form.validate()):
        title = form.title.data
        content = form.content.data

        # cursor oluşturalım db işlem yapalım

        cursor = mysql.connection.cursor()

        sorgu = "insert into articles(title,author,content) values (%s,%s,%s)"

        cursor.execute(sorgu, (title, session["userName"], content))

        mysql.connection.commit()

        cursor.close()

        flash("Makele Başarıyla Eklendi", "success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html", form=form)


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "select * from articles "

    result = cursor.execute(sorgu)

    if (result > 0):
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")


@app.route("/delete/<string:id>")
@login_required
def deleteArticle(id):
    cursor = mysql.connection.cursor()

    sorgu = "select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu, (session["userName"], id))

    if (result > 0):
        deleteQuery = "delete from articles where id = %s"
        cursor.execute(deleteQuery, (id))
        mysql.connection.commit()
        flash("Kayıt başarıyla silindi...", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme ait yetkiniz yok", "danger")
        return redirect(url_for("index"))


@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def editArticle(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where author = %s and id = %s"

        result = cursor.execute(sorgu, (session["userName"], id))

        if (result == 0):
            flash("Böyle bir makale yok veya bu işleme ait yetkiniz yok", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("update.html", form=form)
    else:
        # post request
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        updateQuery = "update articles set title=%s , content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(updateQuery, (newTitle, newContent, id))

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi", "success")
        return redirect(url_for("dashboard"))


if (__name__ == "__main__"):
    app.run(debug=True, port=9091, host="localhost")


# bootstrap hazır css ve js dosyaları içerir.


# <!--{ % extends "layout.html" % }
# <!--# inheritance from layout.html  # isterse methodları override edebilir.-->
# <!--{ % block content % }
