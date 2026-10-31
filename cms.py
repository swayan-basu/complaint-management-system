import os
import re
import secrets
from flask import Flask, request, jsonify, render_template, redirect, url_for, abort, session, g
from flask_mysqldb import MySQL
from datetime import timedelta
from functools import wraps
from db import connect_db, setup_database
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

app=Flask(__name__)
app.config["SECRET_KEY"]=os.getenv("secret_key", "super-secret-fallback-key")
app.config["MAX_CONTENT_LENGTH"]=1024*1024
app.config["SESSION_COOKIE_HTTPONLY"]=True
app.config["SESSION_COOKIE_SECURE"]=os.getenv("cookie_secure","0")=="1"
app.config["SESSION_COOKIE_SAMESITE"]="lax"
app.config["SESSION_REFRESH_EACH_REQUEST"]=True
app.config["PERMANENT_SESSION_LIFETIME"]=timedelta(hours=1)

Admin_username=os.getenv("admin_username", "admin")
Admin_pass_hash=generate_password_hash(os.getenv("admin_password", "admin123"))


csrf=CSRFProtect(app)
valid_status={'pending', 'under review', 'closed'}
valid_urgencies={'low', 'medium','high'}
category_options=[
    "billing",
    "technical",
    "general"
]
valid_categories=set(category_options)
email_regex=re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
reference_re=re.compile(r"^CM[-_][A-Z0-9]{8}$")

def input_inspect(value, field_name, max_length=None, allow_newlines=False):
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if allow_newlines:
        lines = [" ".join(line.split()) for line in value.splitlines()]
        cleaned = "\n".join(lines)
    else:
        cleaned = " ".join(value.split())
    cleaned = "".join(ch for ch in cleaned if ord(ch) >= 32 or ch == "\n")
    if max_length is not None:
        return cleaned[:max_length]
    return cleaned

def normalize_ref(value):
    if not value:
        return None
    ref = input_inspect(value, "ref", max_length=32).upper()
    if reference_re.match(ref):
        return ref
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    submitted_ref=normalize_ref(request.args.get("ref", ""))
    if request.method=="POST":
        full_name= request.form.get("full_name", "").strip()
        email= request.form.get("email", "").strip()
        category= request.form.get("category", "").strip().lower()
        urgency= request.form.get("urgency", "").strip().lower()
        issue=request.form.get("issue", "").strip()


        if not full_name or not email or not category or not urgency or not issue:
            return render_template("user.html", error="please fill all required fields!", submitted_ref=submitted_ref)
        if not email_regex.match(email):
            return render_template("user.html", error="invalid email address!", submitted_ref=submitted_ref)
        if category not in valid_categories:
            return render_template("user.html", error="invalid category!", submitted_ref=submitted_ref)
        if urgency not in valid_urgencies:
            return render_template("user.html", error="select proper urgency!", submitted_ref=submitted_ref)
        
        if len(full_name)>100 or len(email)>100 or len(issue)>1000:
            return render_template("user.html", error="Too long.please keep it short.", submitted_ref=submitted_ref)

        
        tracking_id="CM_"+secrets.token_hex(4).upper()

        conn=connect_db()
        if conn:
            cursor=conn.cursor()
            try:
                sql="""insert into complaints(ref, name, email, category, urgency, message)values(%s,%s,%s,%s,%s,%s)"""
                values=(tracking_id, full_name, email, category, urgency, issue)
                cursor.execute(sql, values)
                conn.commit()
                return redirect(url_for("index", ref=tracking_id))
            
            except Exception as e:
                return render_template("user.html", error="There's an error! please try again.", submitted_ref=submitted_ref)
    return render_template("user.html", submitted_ref=submitted_ref)

def login_required(f):
    @wraps(f)
    def cred_check(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return cred_check       

@app.route("/admin", methods=["GET"])
@login_required
def admin_page():
    conn=connect_db()
    if not conn:
        return "Internal error. Please try again later"
    search_query= request.args.get("search", "").strip()
    category_filter= request.args.get("category", "").strip().lower()
    urgency_filter= request.args.get("priority", "").strip().lower()
    status_filter= request.args.get("status", "").strip().lower()
    page= request.args.get("page", 1, type=int)
    per_page=25

    cursor=conn.cursor(dictionary=True)
    try:
        sql="from complaints where 1=1"
        params=[]
        if search_query:
            sql+=" and ref like %s"
            params.append(f"%{search_query}%")
        if category_filter in valid_categories:
            sql+=" and category=%s"
            params.append(category_filter)
        if urgency_filter in valid_urgencies:
            sql+=" and urgency=%s"
            params.append(urgency_filter)
        if status_filter in valid_status:
            sql+=" and status=%s"
            params.append(status_filter)
        count_sql=f"select count(*) as total {sql}"
        cursor.execute(count_sql, tuple(params))
        total_records=cursor.fetchone()["total"]
        total_pages=max((total_records+per_page-1)//per_page, 1)

        if page>total_pages:
          page=total_pages
        offset=(page-1)*per_page
        data_sql=f"select * {sql} order by created_at desc limit %s offset %s"
        data_params=tuple(params)+ (per_page, offset)
        cursor.execute(data_sql, tuple(data_params))
        all_complaints=cursor.fetchall()
        return render_template("admin.html", complaints=all_complaints,
                                   page=page,
                                   total_pages=total_pages,
                                   search_query=search_query,
                                   category_filter=category_filter,
                                   urgency_filter=urgency_filter,
                                   status_filter=status_filter,
                                   valid_categories=valid_categories,
                                   valid_urgencies=valid_urgencies,
                                   valid_status=valid_status)   
    except Exception as e:
        app.logger.error(f"Error fetching complaints: {e}")
        return f"complaints fetching error. Please try again later.", 500
    finally:        
        cursor.close()
        conn.close()
            

@app.route("/user.html", methods=["GET"])
def user_page():
    return redirect(url_for("index"))

@app.route("/admin/view/<ref>", methods=["GET"])
@login_required
def view_issue(ref):
    conn=connect_db()
    if conn:
        cursor=conn.cursor(dictionary=True)
        try:
            sql= "select * from complaints where ref=%s"
            cursor.execute(sql, (ref,))
            single_complaint=cursor.fetchone()
            if not single_complaint:
                return f"complaint#{ref} not found!", 404
            return render_template("admin_view.html", c=single_complaint, valid_status=valid_status, track_id=ref)
        except Exception as e:
            app.logger.error(f"Error fetching complaint details: {e}")
            return f"unable to fetch complaint details. Please try again later.", 500
        finally:
            cursor.close()
            conn.close()
    return "Database connection error. Please try again later."
        

@app.route("/admin/update/<ref>", methods=["POST"])
@login_required
def admin_update_status(ref):
    status=request.form.get("status").strip().lower()
    if status not in valid_status:
        return "invalid status! Try again", 400
    conn=connect_db()
    if conn:
        cursor=conn.cursor(dictionary=True)
        try:
            sql="update complaints set status=%s where ref=%s"
            print(f"DEBUG CHECK - My SQL is: {sql}")
            cursor.execute(sql,(status, ref))
            conn.commit()
            return redirect(url_for("view_issue", ref=ref))
        except Exception as e:
            app.logger.error(f"Error updating complaint status: {e}")
            return f"unable to update complaint status. Please try again later.", 500
        finally:
            cursor.close()
            conn.close()
    return "Database connection error. Please try again later."


@app.route("/api/track/<ref>", methods=["GET"])
def track_issue(ref):
    ref = normalize_ref(ref)
    if not ref:
        return jsonify({"success":False, "error":"invalid tracking id"}), 400
    conn=connect_db()
    if conn:
        cursor=conn.cursor(dictionary=True)
        try:
            sql="select status from complaints where ref=%s"
            cursor.execute(sql, (ref,))
            complaint=cursor.fetchone()
            if complaint:
                return jsonify({"success":True, "status":complaint["status"]})
            else:
                return jsonify({"success":False, "error":"complaint not found! please check the tracking id"})
        except Exception as e:
            app.logger.error(f"API tracking error: {e}")
            return jsonify({"success":False, "error": f"unable to fetch complaint status. Please try again later."}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({"success":False, "error":"There's an internal error. please try again later."})


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method=="POST":
        username=request.form.get("username", "").strip()
        password=request.form.get("password", "").strip()

        if username==Admin_username and check_password_hash(Admin_pass_hash, password):
            session["admin_logged_in"]=True
            return redirect(url_for("admin_page"))
        else:
            return render_template("admin_login.html", error="Invalid username or password! Try again.")
    return render_template("admin_login.html")

@app.route("/admin/logout", methods=["GET"])
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["strict-transport-security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["server"]="CMS web server"
    return response



if __name__=="__main__":
    setup_database()
    app.run(debug=False, host="127.0.0.1", port=5000) 
