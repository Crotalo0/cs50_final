"""
CS50 Final Project
Sample login/registration page with Captcha and mail OTP
"""
import datetime
import os
import uuid as uuid

from cs50 import SQL
from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import flash
from flask import redirect
from flask import session

from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from flask_recaptcha_modded import ReCaptcha


from mail import Mail
from helpers import login_required
from helpers import secure_password
from helpers import otp_generator
from helpers import one_day_old_timeout
from helpers import otp_expired
from helpers import random_url_gen


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = os.environ["FLASK_SECRET_KEY"]

UPLOAD_FOLDER = "static/images/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.permanent_session_lifetime = datetime.timedelta(days=3)

HOST = "http://127.0.0.1:5000"
# DB creation
db = SQL("sqlite:///users.sqlite3")

mail = Mail(
    "smtp.gmail.com",
    os.environ["FLASK_EMAIL"],
    os.environ["FLASK_EMAIL_PWD"],
)


#################
# Captcha setup #
#################
recaptcha = ReCaptcha(app=app)
app.config.update(
    dict(
        RECAPTCHA_ENABLED=True,
        RECAPTCHA_SITE_KEY=os.environ["RECAPTCHA_SITE_KEY"],
        RECAPTCHA_SECRET_KEY=os.environ["RECAPTCHA_SECRET_KEY"],
    )
)
recaptcha.init_app(app)
##################


# Layout page variables
@app.context_processor
def utility_processor():
    year = datetime.datetime.now().year
    creator = "Alex"

    return dict(
        year=year,
        creator=creator,
    )


################
# Flask Routes #
################


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login for registered user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Error, email entry blank")
            return redirect(url_for("login"))

        if not password:
            flash("Error, password entry blank")
            return redirect(url_for("login"))

        row = db.execute(
            "SELECT * FROM users WHERE username=? OR email=?", username, username
        )

        if not row:
            flash("No existing user, register first!")
            return redirect(url_for("login"))

        if not check_password_hash(row[0]["hash"], password):
            flash("Error, wrong password")
            return redirect(url_for("login"))

        if not recaptcha.verify():
            flash("Captcha failed")
            return redirect(url_for("login"))

        session.permanent = True

        # Save data in session dictionary
        session["user_id"] = row[0]["id"]
        session["user"] = row[0]["username"]
        session["email"] = row[0]["email"]

        avatar = db.execute(
            "SELECT pic_name FROM profile_avatars WHERE user_id=?",
            session["user_id"],
        )
        # Profile pic loading
        # TODO: actually save the avatar locally
        session["profile_pic"] = avatar[0]["pic_name"]

        flash("Login successful")
        return redirect(url_for("main_session"))
    else:
        if "user" in session:
            return redirect(url_for("main_session"))
        else:
            return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """User logout route"""
    session.clear()
    flash("Logout successful")
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration route"""
    if request.method == "POST":
        username = request.form.get("username")
        pwd = request.form.get("password")
        email = request.form.get("email")
        pwd_check = request.form.get("pwdCheck")
        email_check = request.form.get("emailCheck")

        duplicate_username = db.execute(
            "SELECT username FROM users WHERE username=?",
            username,
        )
        duplicate_email = db.execute(
            "SELECT email FROM users WHERE email=?",
            email,
        )

        if not username:
            flash("Error, blank username")
            return redirect(url_for("register"))
        elif duplicate_username:
            flash("Error, username already taken")
            return redirect(url_for("register"))

        if not email:
            flash("Error, blank email entry")
            return redirect(url_for("register"))
        elif duplicate_email:
            flash("Error, email already registered")
            return redirect(url_for("register"))

        if pwd != pwd_check:
            flash("Error, password mismatch")
            return redirect(url_for("register"))
        if email != email_check:
            flash("Error, email mismatch")
            return redirect(url_for("register"))

        if not secure_password(pwd):
            flash(
                "Error, password must "
                "be longer than 8 characters, "
                "and must include at least one symbol, "
                "one lowercase letter and "
                "one upercase letter"
            )
            return redirect(url_for("register"))

        if not recaptcha.verify():
            flash("Captcha failed")
            return redirect(url_for("register"))

        db.execute(
            "INSERT INTO users (username, email, hash)" "VALUES(?, ?, ?)",
            username,
            email,
            generate_password_hash(pwd),
        )

        session.permanent = True

        flash(
            f"Registration successful, Welcome {username}!"
            f"Please confirm your email address by clicking the received link"
        )

        session["user_id"] = db.execute(
            "SELECT id FROM users WHERE username=?", username
        )

        session["user"] = username
        session["email"] = email

        # Send to user email verification URL
        random_url = random_url_gen()
        msg = (
            f"Subject:ALEX WEBSITE - Email confirmation\n\n"
            f"Hello, {username}.\nIn order to activate your account, go to this link:\n"
            f"{HOST}/{random_url}"
        )
        mail.send_email(msg=msg, receiver=email)

        user_id = db.execute(
            "SELECT id FROM users WHERE username=?",
            username,
        )

        db.execute(
            "INSERT OR REPLACE INTO account_verification (user_id, URL) VALUES(?, ?)",
            user_id[0]["id"],
            random_url,
        )

        return redirect("/session")
    else:
        return render_template("register.html")


@app.route("/")
def index():
    """Index page"""
    if "user" not in session:
        return render_template("index.html")
    else:
        return redirect(url_for("main_session"))


@app.route("/session")
@login_required
def main_session():
    """Main page after login"""
    # if "user" in session:
    #     user = session["user"]
    #     return render_template("session.html", user=user)
    # else:
    #     return redirect(url_for("login"))
    user = session["user"]
    # TODO: Add main content to site
    return render_template("session.html", user=user)


@app.route("/email_send")
def email_send():
    return redirect(url_for("user_settings"))


@app.route("/user_settings", methods=["GET", "POST"])
@login_required
def user_settings():
    """User settings page"""
    user_id = session["user_id"]
    account_is_verified = db.execute(
        "SELECT confirmed FROM users WHERE id=?",
        user_id,
    )
    profile_pic = db.execute(
        "SELECT pic_name FROM profile_avatars WHERE user_id=?",
        session["user_id"],
    )
    # Password Reset
    if request.method == "POST":
        if request.form.get("old-password"):
            old_password = request.form.get("old-password")
            new_password = request.form.get("password")
            check_new_password = request.form.get("pwdCheck")

            # Search for old_password in DB
            old_password_in_db = db.execute(
                "SELECT hash FROM users WHERE id=?",
                user_id,
            )
            if not check_password_hash(old_password_in_db[0]["hash"], old_password):
                flash("Old password is wrong.")
                return redirect(url_for("user_settings"))

            if new_password != check_new_password:
                flash("new password mismatch from check password.")
                return redirect(url_for("user_settings"))

            if not secure_password(new_password):
                flash(
                    "Error, password must "
                    "be longer than 8 characters, "
                    "and must include at least one symbol, "
                    "one lowercase letter and "
                    "one upercase letter"
                )
                return redirect(url_for("user_settings"))

            db.execute(
                "UPDATE users SET hash=? WHERE id=?",
                generate_password_hash(new_password),
                user_id,
            )

            flash("Password updated succeessfully")
            return redirect(url_for("user_settings"))

        # Email change
        elif request.form.get("email"):
            new_email = request.form.get("email")
            new_email_check = request.form.get("emailCheck")
            if new_email != new_email_check:
                flash("email mismatch")
                return redirect(url_for("user_settings"))

            db.execute(
                "UPDATE users SET email=? WHERE id=?",
                new_email,
                user_id,
            )
            flash("email updated")
            return redirect(url_for("user_settings"))

        elif request.files.get("profile_pic_form"):
            # TODO: Add picture to database for every user
            new_profile_pic = request.files.get("profile_pic_form")
            pic_filename = secure_filename(new_profile_pic.filename)
            pic_name = str(uuid.uuid1()) + "_" + pic_filename

            db.execute(
                "INSERT OR REPLACE INTO profile_avatars (user_id,pic_name) VALUES(?,?)",
                session["user_id"],
                pic_name,
            )
            # Save avatar locally
            new_profile_pic.save(os.path.join(app.config["UPLOAD_FOLDER"], pic_name))
            session["profile_pic"] = pic_name
            flash("profile picture updated.")
            return redirect(url_for("user_settings"))
        else:
            # In case buttons are clicked and JS fails to check for null
            return redirect(url_for("user_settings"))

    else:
        return render_template(
            "user_settings.html",
            account_is_verified=account_is_verified[0]["confirmed"],
            profile_pic=profile_pic[0]["pic_name"],
        )


@app.route("/pw_reset", methods=["GET", "POST"])
def pw_reset():
    """Start of password reset route"""
    if request.method == "POST":
        email = request.form.get("email")
        emailCheck = request.form.get("emailCheck")

        if not email:
            flash("blank email form")
            return redirect(url_for("pw_reset"))

        if email != emailCheck:
            flash("email mismatch")
            return redirect(url_for("pw_reset"))

        is_present_in_db = db.execute("SELECT * FROM users WHERE email=?", email)

        if not is_present_in_db:
            flash("email not registered")
            return redirect(url_for("pw_reset"))

        if not recaptcha.verify():
            flash("Captcha failed")
            return redirect(url_for("pw_reset"))

        id_from_email = db.execute(
            "SELECT id FROM users WHERE email=?",
            email,
        )
        is_timed_out = db.execute(
            "SELECT * FROM otp_timeout WHERE user_id=?", id_from_email[0]["id"]
        )

        if is_timed_out:
            if one_day_old_timeout(
                is_timed_out,
                datetime.timedelta(days=1),
                "timeout_time",
            ):
                db.execute(
                    "DELETE FROM otp_timeout WHERE user_id=?", id_from_email[0]["id"]
                )
            else:
                flash("You are currently timeoutted")
                return redirect("login")

        otp = otp_generator()
        user_id = db.execute(
            "SELECT id FROM users WHERE email=?",
            email,
        )

        db.execute(
            "INSERT OR REPLACE INTO otp (user_id, otp, email) VALUES(?, ?, ?)",
            user_id[0]["id"],
            otp,
            email,
        )

        msg = f"Subject:OTP from Alex Website\n\n" f"Hello,\nyour OTP is: {otp}"
        mail.send_email(msg=msg, receiver=email)
        flash("reset mail sent to {}".format(email))
        session["otp_email"] = email
        return redirect(url_for("verify"))
    else:
        return render_template("pw_reset.html")


@app.route("/verify", methods=["POST", "GET"])
def verify():
    """Routed aftert pw_reset, asks for OTP to confirm email address"""
    try:
        email = session["otp_email"]
    except KeyError:
        return redirect(url_for("login"))

    otp_info = db.execute(
        "SELECT * FROM otp WHERE email=?",
        email,
    )

    otp_tries = otp_info[0]["tries"]
    otp_code = otp_info[0]["otp"]

    if otp_tries == 0:
        flash("too many tries, retry tomorrow")
        # TODO: Block user for some time there
        user_id_from_email = db.execute(
            "SELECT id FROM users WHERE email=?",
            email,
        )
        db.execute(
            "INSERT OR REPLACE INTO otp_timeout (user_id) VALUES(?)",
            user_id_from_email[0]["id"],
        )

        db.execute(
            "DELETE FROM otp WHERE email=?",
            email,
        )
        return redirect("login")

    if request.method == "POST":
        # TODO: Remember to leave OTP from verify.html
        otp_entry = request.form.get("recovery")

        if otp_entry != otp_code:
            flash("Wrong OTP")
            db.execute(
                "UPDATE otp SET tries=? WHERE email=?",
                otp_tries - 1,
                email,
            )
            return redirect("verify")
        else:
            if otp_expired(
                otp_info,
                mail.otp_total_time,
                "send_time",
            ):
                flash("OTP expired, please request a new one.")

                db.execute(
                    "DELETE FROM otp WHERE email=?",
                    email,
                )
                return redirect(url_for("pw_reset"))

            flash("OTP accepted, redirecting to password change page.")

            db.execute(
                "DELETE FROM otp WHERE email=?",
                email,
            )
            return render_template("reset_password.html")
    else:
        otp_info = db.execute(
            "SELECT * FROM otp WHERE email=?",
            email,
        )

        otp_tries = otp_info[0]["tries"]
        otp_code = otp_info[0]["otp"]

        return render_template("verify.html", otp=otp_code, otp_tries=otp_tries)


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    """Routed after verify, password reset page for a verified user"""
    try:
        email = session["otp_email"]
    except KeyError:
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form.get("password")
        check_password = request.form.get("pwdCheck")
        if password != check_password:
            flash("password mismatch")
            return redirect("reset_password")

        if not secure_password(password):
            flash(
                "Error, password must "
                "be longer than 8 characters, "
                "and must include at least one symbol, "
                "one lowercase letter and "
                "one upercase letter"
            )
            return redirect(url_for("reset_password"))

        db.execute(
            "UPDATE users SET hash=? WHERE email=?",
            generate_password_hash(password),
            email,
        )

        flash("Password updated successfully")
        return redirect(url_for("login"))
    else:
        return render_template("reset_password.html")


@app.route("/<random_url>")
def email_confirmation(random_url):
    url_in_database = db.execute(
        "SELECT * FROM account_verification WHERE URL=?",
        random_url,
    )
    if not url_in_database:
        flash("Error, link invalid")
        return redirect(url_for("index"))

    user_id = url_in_database[0]["user_id"]

    already_confirmed = db.execute(
        "SELECT confirmed FROM users WHERE id=?",
        user_id,
    )

    if already_confirmed[0]["confirmed"]:
        flash("Account already confirmed.")
        db.execute(
            "DELETE FROM account_verification WHERE URL=?",
            random_url,
        )
        return redirect(url_for("login"))

    db.execute(
        "UPDATE users SET confirmed=? WHERE id=?",
        True,
        user_id,
    )

    db.execute(
        "DELETE FROM account_verification WHERE URL=?",
        random_url,
    )

    flash("Account confirmed!")
    return redirect(url_for("session"))


@app.route("/verification_email_sender")
def verification_email_sender():
    """Send verification email, add that request to DB"""
    random_url = random_url_gen()
    user_id = session["user_id"]
    username = session["user"]
    receiver = session["email"]
    msg = (
        f"Subject:ALEX WEBSITE - Email confirmation\n\n"
        f"Hello, {username}.\nIn order to activate your account, go to this link:\n"
        f"{HOST}/{random_url}"
    )
    db.execute(
        "INSERT OR REPLACE INTO account_verification (user_id, URL) VALUES(?, ?)",
        user_id,
        random_url,
    )
    flash("A new verification email has been sent.")
    mail.send_email(msg=msg, receiver=receiver)
    return redirect(url_for("user_settings"))


if __name__ == "__main__":
    app.run(debug=True)
