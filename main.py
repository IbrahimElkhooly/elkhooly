from flask import Flask, render_template, request, redirect, jsonify, abort, url_for, session, flash, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import sqlite3
from werkzeug.security import generate_password_hash
import os
from werkzeug.utils import secure_filename
import pdfkit
import random

app = Flask(__name__)
app.secret_key = '1a2b3c4d5e6d7g8h9i10'

# ⚡ الإعدادات المعدلة للاتصال بالسيرفر الخارجي
app.config['MYSQL_HOST'] = 'hopper.proxy.rlwy.net'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'bCxdRxziPcrfHZvRmkltXzVZEqsuclWb'
app.config['MYSQL_DB'] = 'railway'
app.config['MYSQL_PORT'] = 54636
app.config['UPLOAD_FOLDER'] = 'static/uploads'

mysql = MySQL(app)

# ⚡ الاتصال المباشر بقاعدة البيانات الخارجية
def get_db_connection():
    try:
        db = MySQLdb.connect(
            host='hopper.proxy.rlwy.net',
            user='root',
            passwd='bCxdRxziPcrfHZvRmkltXzVZEqsuclWb',
            db='railway',
            port=54636,
            charset="utf8",
            connect_timeout=10
        )
        print("✅ تم الاتصال بقاعدة البيانات الخارجية بنجاح!")
        return db
    except Exception as e:
        print(f"❌ فشل الاتصال بقاعدة البيانات الخارجية: {e}")
        # استخدام الإعدادات المحلية كبديل
        try:
            db = MySQLdb.connect(
                host="localhost",
                user="root",
                passwd="",
                db="loginapp",
                charset="utf8"
            )
            print("🔄 استخدام قاعدة البيانات المحلية")
            return db
        except Exception as local_error:
            print(f"❌ فشل الاتصال المحلي أيضاً: {local_error}")
            return None

# إنشاء اتصال بقاعدة البيانات
db = get_db_connection()
if db:
    cursor = db.cursor()
    print("🎯 تم تهيئة الاتصال بقاعدة البيانات")
else:
    print("🚨 فشل في إنشاء الاتصال بقاعدة البيانات")
    cursor = None

from werkzeug.security import check_password_hash


@app.route('/notifications')
def notifications():
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول أولاً!", "danger")
        return redirect(url_for('auth'))

    filter_type = request.args.get('filter', None)

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if filter_type and filter_type in ['exam', 'homework', 'subject_file', 'friend_request']:
        cursor.execute('''
            SELECT * FROM notifications
            WHERE user_id = %s AND notification_type = %s
            ORDER BY created_at DESC
        ''', (session['id'], filter_type))
    else:
        cursor.execute('''
            SELECT * FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', (session['id'],))

    notifications = cursor.fetchall()
    cursor.close()

    return render_template('notifications.html', notifications=notifications, filter=filter_type)



@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, username, password, role FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account and check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['role'] = account['role']  # تخزين نوع المستخدم

            flash("تم تسجيل الدخول بنجاح!", "success")
            return redirect(url_for('home'))
        else:
            flash("اسم المستخدم أو كلمة المرور غير صحيحة!", "danger")

        cursor.close()

    return render_template('auth/login.html', title="تسجيل الدخول")



@app.route('/latest_notifications')
def latest_notifications():
    if 'loggedin' not in session:
        return jsonify({'notifications': []})

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    ''', (session['id'],))
    notifications = cursor.fetchall()
    cursor.close()

    return jsonify({'notifications': notifications})


def is_teacher_or_assistant(subject_id):
    if 'loggedin' not in session:
        return False

    user_id = session['id']
    role = session.get('role')

    if role == 'teacher':
        return True

    if role == 'assistant':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM assistants WHERE assistant_id = %s AND subject_id = %s", (user_id, subject_id))
        assistant_record = cursor.fetchone()
        cursor.close()
        return bool(assistant_record)

    return False

def is_admin():
    return 'loggedin' in session and session.get('role') == 'admin'

@app.route('/parent-lookup', methods=['GET', 'POST'])
def parent_lookup():
    student = None
    grades = []
    homeworks = []
    stats = {}
    error = None

    if request.method == 'POST':
        parent_code = request.form['parent_code']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # 1. جلب بيانات الطالب باستخدام كود ولي الأمر
        cursor.execute('SELECT id, username FROM accounts WHERE parent_access_code = %s', (parent_code,))
        student = cursor.fetchone()

        if student:
            student_id = student['id']

            # 2. جلب درجات الامتحانات لكل المواد
            cursor.execute('''
                SELECT sg.exam_id, e.exam_name, e.subject_id, s.name, sg.score, sg.total_questions, sg.grade_date
                FROM student_grades sg
                JOIN exams e ON sg.exam_id = e.id
                JOIN subjects s ON e.subject_id = s.id
                WHERE sg.user_id = %s
            ''', (student_id,))
            grades = cursor.fetchall()

            # 3. جلب درجات الواجبات لكل المواد
            # 3. جلب درجات الواجبات لكل المواد
            cursor.execute('''SELECT 
    a.id AS student_id, 
    a.username, 
    COALESCE(hs.grade, 0) AS homework_score,  
    h.subject_id,
    h.title AS homework_name,  -- ✅ اسم الواجب
    s.name AS subject_name     -- ✅ اسم المادة
FROM homework_submissions hs
JOIN accounts a ON TRIM(LOWER(hs.student_name)) = TRIM(LOWER(a.username))
JOIN homeworks h ON hs.homework_id = h.id
JOIN subjects s ON h.subject_id = s.id  -- ✅ ربط المادة للحصول على اسمها
WHERE a.id = %s

            ''', (student_id,))
            homeworks = cursor.fetchall()

            # 4. حساب إحصائيات الأداء لكل مادة
            # 4. حساب إحصائيات الأداء لكل مادة (المعدلة)
            cursor.execute('''
                SELECT s.id AS subject_id, 
                       s.name,
                       COUNT(DISTINCT e.id) AS total_exams,
                       COUNT(DISTINCT h.id) AS total_homeworks
                FROM subjects s
                JOIN student_subjects ss ON s.id = ss.subject_id  -- إضافة الجدول المرتبط
                LEFT JOIN exams e ON e.subject_id = s.id
                LEFT JOIN homeworks h ON h.subject_id = s.id
                WHERE ss.student_id = %s  -- فلترة بالمواد المسجل بها
                GROUP BY s.id, s.name
            ''', (student_id,))  # إضافة الباراميتر
            subjects_stats = cursor.fetchall()

            for stat in subjects_stats:
                stats[stat['subject_id']] = {
                    'subject_name': stat['name'],  # تعديل الاسم هنا
                    'total_exams': stat['total_exams'],
                    'total_homeworks': stat['total_homeworks'],
                    'exam_percentage': 0,
                    'homework_percentage': 0,
                    'final_grade': 0
                }

            # 5. حساب متوسط الدرجات لكل مادة
            subject_totals = {}

            # إضافة القيم الافتراضية لكل مادة
            for row in grades:
                subject_id = row['subject_id']
                if subject_id not in subject_totals:
                    subject_totals[subject_id] = {'exam_percentage': 0, 'exam_count': 0, 'homework_percentage': 0, 'homework_count': 0}

                if row['total_questions'] > 0:  # التحقق قبل القسمة
                    percentage = (row['score'] / row['total_questions']) * 100
                else:
                    percentage = 0
                subject_totals[subject_id]['exam_percentage'] += percentage
                subject_totals[subject_id]['exam_count'] += 1

            for row in homeworks:
                subject_id = row['subject_id']
                if subject_id not in subject_totals:
                    subject_totals[subject_id] = {'exam_percentage': 0, 'exam_count': 0, 'homework_percentage': 0, 'homework_count': 0}

                percentage = ((row['homework_score'] or 0) / 10) * 100
                subject_totals[subject_id]['homework_percentage'] += percentage
                subject_totals[subject_id]['homework_count'] += 1

            for subject_id, data in subject_totals.items():
                exam_percentage = (data['exam_percentage'] / data['exam_count']) if data['exam_count'] > 0 else 0
                homework_percentage = (data['homework_percentage'] / data['homework_count']) if data['homework_count'] > 0 else 0
                final_grade = (exam_percentage * 0.5) + (homework_percentage * 0.5)

                if subject_id in stats:
                    stats[subject_id]['exam_percentage'] = round(exam_percentage, 2)
                    stats[subject_id]['homework_percentage'] = round(homework_percentage, 2)
                    stats[subject_id]['final_grade'] = round(final_grade, 2)

        else:
            error = "كود ولي الأمر غير صحيح أو لا يوجد طالب مسجل به."

    return render_template('parent_search.html', student=student, grades=grades, homeworks=homeworks, stats=stats, error=error)


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        form_type = request.form.get('form_type')  # لمعرفة نوع النموذج (تسجيل أو تسجيل الدخول)

        if form_type == 'register':
            # --- تسجيل حساب جديد ---
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']

            cursor.execute("SELECT * FROM accounts WHERE username = %s OR email = %s", (username, email))
            account = cursor.fetchone()

            if account:
                flash("اسم المستخدم أو البريد الإلكتروني مسجل بالفعل!", "danger")
            elif not re.match(r'^[A-Za-z0-9]+$', username):
                flash("اسم المستخدم يجب أن يحتوي فقط على أحرف وأرقام!", "danger")
            elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                flash("بريد إلكتروني غير صحيح!", "danger")
            elif len(password) < 6:
                flash("كلمة المرور يجب أن تكون 6 أحرف على الأقل!", "danger")
            else:
                hashed_password = generate_password_hash(password)

                # توليد كود ولي الأمر (8 أرقام عشوائية)
                parent_code = ''.join(random.choices('0123456789', k=8))

                cursor.execute('''
                    INSERT INTO accounts (username, email, password, parent_access_code) 
                    VALUES (%s, %s, %s, %s)
                ''', (username, email, hashed_password, parent_code))
                mysql.connection.commit()

                flash(f"تم إنشاء الحساب بنجاح! كود ولي الأمر: {parent_code}", "success")
                return redirect(url_for('auth'))  # يرجع لنفس الصفحة

        elif form_type == 'auth':
            # --- تسجيل الدخول ---
            username = request.form['username']
            password = request.form['password']

            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()

            if account and check_password_hash(account['password'], password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['role'] = account['role']

                flash("تم تسجيل الدخول بنجاح!", "success")
                return redirect(url_for('home'))
            else:
                flash("بيانات تسجيل الدخول غير صحيحة!", "danger")

    return render_template('auth_combined.html')  # الصفحة الجديدة اللي فيها الفورمين



# عرض صفحة  بيها كود ولي الامر ولي الامر
@app.route('/my_parent_code')
def my_parent_code():
    if 'loggedin' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT parent_access_code FROM accounts WHERE id = %s', (session['id'],))
    account = cursor.fetchone()

    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('blog'))

    return render_template('parent_code.html', parent_code=account['parent_access_code'])


@app.route('/admin/manage_users', methods=['GET', 'POST'])
def manage_users():
    if not is_admin():
        flash("ليس لديك الصلاحيات للوصول إلى هذه الصفحة!", "danger")
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        user_id = request.form['user_id']
        new_role = request.form['role']
        cursor.execute("UPDATE accounts SET role = %s WHERE id = %s", (new_role, user_id))
        mysql.connection.commit()
        flash("تم تحديث صلاحيات المستخدم بنجاح!", "success")

    cursor.execute("SELECT id, username, role FROM accounts")
    users = cursor.fetchall()
    cursor.close()

    return render_template('manage_users.html', users=users)




@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # التحقق مما إذا كان اسم المستخدم أو البريد الإلكتروني موجود بالفعل
        cursor.execute("SELECT * FROM accounts WHERE username = %s OR email = %s", (username, email))
        account = cursor.fetchone()

        if account:
            flash("Username or email already exists!", "danger")
        elif not re.match(r'^[A-Za-z0-9]+$', username):
            flash("Username must contain only letters and numbers!", "danger")
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash("Invalid email address!", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long!", "danger")
        else:
            # تشفير كلمة المرور قبل التخزين
            hashed_password = generate_password_hash(password)

            # توليد كود ولي الأمر (8 أرقام عشوائية)
            parent_code = ''.join(random.choices('0123456789', k=8))

            # إدخال المستخدم الجديد إلى قاعدة البيانات مع كود ولي الأمر
            cursor.execute('INSERT INTO accounts (username, email, password, parent_access_code) VALUES (%s, %s, %s, %s)',
                           (username, email, hashed_password, parent_code))
            mysql.connection.commit()

            # تسجيل النشاط في activity_logs
            cursor.execute("INSERT INTO activity_logs (activity, username, user_id) VALUES (%s, %s, LAST_INSERT_ID())",
                           ("New user registered", username))
            mysql.connection.commit()

            flash(f"You have successfully registered! Please log in. Parent Access Code: {parent_code}", "success")
            return redirect(url_for('auth'))

    return render_template('auth/register.html', title="Register")

@app.route('/')
def home():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))  # توجيه المستخدم إلى صفحة تسجيل الدخول إذا لم يكن مسجلاً

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT posts.id, posts.content, posts.timestamp, accounts.username, accounts.profile_picture "
        "FROM posts JOIN accounts ON posts.user_id = accounts.id ORDER BY posts.timestamp DESC"
    )
    posts_data = cursor.fetchall()

    posts_list = []
    for row in posts_data:
        post_id = row[0]
        cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id,))
        likes_count = cursor.fetchone()[0]

        cursor.execute("SELECT comments.content, comments.timestamp, accounts.username, accounts.profile_picture "
                       "FROM comments JOIN accounts ON comments.user_id = accounts.id WHERE comments.post_id = %s ORDER BY comments.timestamp DESC", (post_id,))
        comments_data = cursor.fetchall()

        posts_list.append({
            'id': post_id,
            'content': row[1],
            'timestamp': row[2],
            'username': row[3],
            'profile_picture': row[4],  # إضافة صورة المستخدم
            'likes_count': likes_count,
            'comments': [{'content': comment[0], 'timestamp': comment[1], 'username': comment[2], 'profile_picture': comment[3]} for comment in comments_data]
        })

    cursor.close()
    return render_template('home/home.html', username=session['username'], title="Home", posts=posts_list)
@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor()

    # التحقق من وجود تفاعل سابق
    cursor.execute("SELECT * FROM likes WHERE user_id = %s AND post_id = %s", (session['id'], post_id))
    existing_like = cursor.fetchone()

    if existing_like:
        # إذا كان المستخدم قد أعجب بالمنشور بالفعل، قم بإزالة الإعجاب
        cursor.execute("DELETE FROM likes WHERE user_id = %s AND post_id = %s", (session['id'], post_id))
        mysql.connection.commit()
    else:
        # إذا لم يكن هناك تفاعل سابق، قم بإضافة إعجاب جديد
        cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (%s, %s)", (session['id'], post_id))
        mysql.connection.commit()

    cursor.close()
    return redirect(url_for('home'))
@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    content = request.form['content']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO comments (user_id, post_id, content) VALUES (%s, %s, %s)", (session['id'], post_id, content))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('home'))


@app.route('/add_friend', methods=['GET', 'POST'])
def add_friend():
    if 'id' not in session:
        flash("يجب تسجيل الدخول أولاً!", "danger")
        return redirect(url_for('auth'))

    current_user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب قائمة الأصدقاء الحاليين
    cursor.execute("""
        SELECT a.id FROM accounts a
        JOIN friends f ON (a.id = f.user_id OR a.id = f.friend_id)
        WHERE (f.user_id = %s OR f.friend_id = %s) AND f.status = 'accepted'
    """, (current_user_id, current_user_id))

    friend_ids = [row['id'] for row in cursor.fetchall()]
    friend_ids.append(current_user_id)  # استبعاد المستخدم الحالي نفسه

    query = "SELECT id, username, profile_picture FROM accounts WHERE id NOT IN %s"
    params = (tuple(friend_ids),)

    # البحث حسب اسم المستخدم إذا تم إدخال بحث
    if request.method == 'POST' and 'username' in request.form:
        search_username = f"%{request.form['username']}%"
        query += " AND username LIKE %s"
        params += (search_username,)

    cursor.execute(query, params)
    users = cursor.fetchall()

    return render_template('add_friend.html', users=users)


@app.route('/send_friend_request/<int:friend_id>', methods=['POST'])
def send_friend_request(friend_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor()

    # إضافة الطلب
    cursor.execute("INSERT INTO friends (user_id, friend_id, status) VALUES (%s, %s, 'pending')",
                   (session['id'], friend_id))
    mysql.connection.commit()

    # إرسال إشعار لصاحب الحساب
    cursor.execute('''
        INSERT INTO notifications (user_id, message, notification_type, related_id)
        VALUES (%s, %s, %s, %s)
    ''', (friend_id, f"لديك طلب صداقة جديد من {session['username']}", 'friend_request', session['id']))

    mysql.connection.commit()
    cursor.close()

    flash('تم إرسال طلب الصداقة!', 'success')
    return redirect(url_for('profile', user_id=friend_id))


@app.route('/friend_requests', methods=['GET', 'POST'])
def friend_requests():
    if 'id' not in session:
        flash("يجب تسجيل الدخول أولاً!", "danger")
        return redirect(url_for('auth'))

    current_user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب طلبات الصداقة مع اسم المرسل وصورة الملف الشخصي
    cursor.execute("""
        SELECT friends.id, accounts.username, accounts.profile_picture, friends.user_id 
        FROM friends 
        JOIN accounts ON friends.user_id = accounts.id 
        WHERE friends.friend_id = %s AND friends.status = 'pending'
    """, [current_user_id])

    requests = cursor.fetchall()

    if request.method == 'POST':
        action = request.form['action']
        request_id = request.form['request_id']

        if action == 'accept':
            cursor.execute("UPDATE friends SET status = 'accepted' WHERE id = %s", [request_id])

            flash("تم قبول طلب الصداقة!", "success")

        elif action == 'reject':
            cursor.execute("DELETE FROM friends WHERE id = %s", [request_id])  # حذف الطلب بدل من تعيينه rejected
            flash("تم رفض طلب الصداقة!", "danger")

        mysql.connection.commit()
        return redirect(url_for('friend_requests'))

    return render_template('friend_requests.html', requests=requests)


@app.route('/accept_friend_request/<int:request_id>', methods=['POST'])
def accept_friend_request(request_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # تحديث حالة الطلب
    cursor.execute("UPDATE friends SET status = 'accepted' WHERE id = %s", [request_id])
    mysql.connection.commit()

    # جلب صاحب الطلب لإرسال الإشعار
    cursor.execute("SELECT user_id FROM friends WHERE id = %s", [request_id])
    friend_request = cursor.fetchone()

    if friend_request:
        sender_id = friend_request['user_id']
        cursor.execute('''
            INSERT INTO notifications (user_id, message, notification_type, related_id)
            VALUES (%s, %s, %s, %s)
        ''', (sender_id, f"تم قبول طلب الصداقة من {session['username']}", 'friend_request_accept', session['id']))

    mysql.connection.commit()
    cursor.close()

    flash('تم قبول الطلب!', 'success')
    return redirect(url_for('friend_requests'))


@app.route('/reject_friend_request/<int:request_id>', methods=['POST'])
def reject_friend_request(request_id):
    if 'id' not in session:
        flash("يجب تسجيل الدخول أولاً!", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # حذف الطلب من قاعدة البيانات
    cursor.execute("DELETE FROM friends WHERE id = %s", [request_id])
    mysql.connection.commit()

    flash("تم رفض طلب الصداقة!", "danger")
    return redirect(url_for('friend_requests'))
@app.route('/my_friends')
def my_friends():
    if 'id' not in session:
        flash("يجب تسجيل الدخول أولاً!", "danger")
        return redirect(url_for('auth'))

    current_user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT a.id, a.username, a.email, a.profile_picture 
        FROM friends f
        JOIN accounts a ON a.id = f.friend_id OR a.id = f.user_id
        WHERE (f.user_id = %s OR f.friend_id = %s) 
        AND f.status = 'accepted' 
        AND a.id != %s
    """, (current_user_id, current_user_id, current_user_id))

    friends = cursor.fetchall()
    return render_template('my_friends.html', friends=friends)

@app.route('/messages')
def messages():
    if 'id' not in session:
        return redirect(url_for('auth'))

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)


    cursor.execute("""
        SELECT accounts.id, accounts.username, 
               COALESCE(accounts.profile_picture, 'default.png') AS profile_picture,
               (SELECT MAX(messages.timestamp)
                FROM messages 
                WHERE (messages.sender_id = accounts.id AND messages.receiver_id = %s)
                   OR (messages.receiver_id = accounts.id AND messages.sender_id = %s)
               ) AS last_message_time
        FROM friends
        JOIN accounts ON (friends.friend_id = accounts.id OR friends.user_id = accounts.id)
        WHERE (friends.user_id = %s OR friends.friend_id = %s) 
          AND accounts.id != %s
        ORDER BY IFNULL(last_message_time, '1970-01-01 00:00:00') DESC
    """, (user_id, user_id, user_id, user_id, user_id))

    friends = cursor.fetchall()
    cursor.close()

    return render_template('messages.html', friends=friends)

# 📍 عرض المحادثة بين شخصين وإرسال الرسائل
@app.route('/chat/<int:friend_id>', methods=['GET', 'POST'])
def chat(friend_id):
    if 'id' not in session:
        return redirect(url_for('auth'))

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        message = request.form['message']
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s)",
                       (user_id, friend_id, message))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'status': 'success'})

    cursor.execute("""
        SELECT * FROM messages 
        WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) 
        ORDER BY timestamp
    """, (user_id, friend_id, friend_id, user_id))
    messages = cursor.fetchall()

    cursor.execute("""
        SELECT username, 
               COALESCE(profile_picture, 'default.png') AS profile_picture 
        FROM accounts WHERE id = %s
    """, (friend_id,))

    friend = cursor.fetchone()
    cursor.close()

    if not friend:
        flash("المستخدم غير موجود!", "danger")
        return redirect(url_for('messages'))

    return render_template('chat.html', messages=messages, friend=friend, friend_id=friend_id)


@app.route('/get_messages/<int:friend_id>')
def get_messages(friend_id):
    if 'id' not in session:
        return jsonify({'error': 'يجب تسجيل الدخول'}), 403

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT m.*, a.username AS sender_name 
        FROM messages m
        JOIN accounts a ON m.sender_id = a.id
        WHERE (m.sender_id = %s AND m.receiver_id = %s) 
           OR (m.sender_id = %s AND m.receiver_id = %s) 
        ORDER BY m.timestamp
    """, (user_id, friend_id, friend_id, user_id))

    messages = cursor.fetchall()
    cursor.close()

    chat_html = ""
    for message in messages:
        sender = "أنت" if message['sender_id'] == user_id else message['sender_name']
        css_class = "sent" if message['sender_id'] == user_id else "received"
        chat_html += f'''
        <div class="message-container {css_class}">
            <div class="message">
                <div class="message-username">{sender}</div>
                {message["message"]}
                <div class="message-time">{message["timestamp"].strftime('%H:%M')}</div>
            </div>
        </div>
        '''

    return chat_html

@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        if account:
            return render_template('auth/profile.html', account=account, title="Profile")
    return redirect(url_for('auth'))


@app.route('/info')
def info():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        if account:
            return render_template('auth/info.html', account=account, title="Info")
    return redirect(url_for('auth'))


@app.route('/activity')
def activity():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM activity_logs WHERE user_id = %s ORDER BY date DESC', (session['id'],))
        activities = cursor.fetchall()
        return render_template('auth/activity.html', activities=activities, title="Activity Logs")
    return redirect(url_for('auth'))


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    flash("You have successfully logged out!", "success")
    return redirect(url_for('auth'))

@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session or session.get('role') not in ['admin', 'teacher']:
        flash("ليس لديك صلاحية للوصول لهذه الصفحة", "danger")
        return redirect(url_for('home'))

    username = session.get('username')  # اسم المعلم المسجل في الجلسة
    user_role = session.get('role')
    is_admin = (user_role == 'admin')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # عدد الطلاب في كل مادة (فلترة بالاسم لو معلم - بدون فلترة لو أدمن)
    if is_admin:
        cursor.execute("""
            SELECT subjects.name AS subject_name, COUNT(student_subjects.student_id) AS student_count
            FROM subjects
            LEFT JOIN student_subjects ON subjects.id = student_subjects.subject_id
            GROUP BY subjects.id
        """)
    else:
        cursor.execute("""
            SELECT subjects.name AS subject_name, COUNT(student_subjects.student_id) AS student_count
            FROM subjects
            LEFT JOIN student_subjects ON subjects.id = student_subjects.subject_id
            WHERE subjects.teacher = %s
            GROUP BY subjects.id
        """, (username,))

    students_per_subject = cursor.fetchall()

    # متوسط درجات الطلاب في الامتحانات
    if is_admin:
        cursor.execute("""
            SELECT subjects.name AS subject_name, 
                   IFNULL(AVG(student_grades.score / student_grades.total_questions * 100), 0) AS avg_score
            FROM subjects
            JOIN exams ON subjects.id = exams.subject_id
            LEFT JOIN student_grades ON exams.id = student_grades.exam_id
            GROUP BY subjects.id
        """)
    else:
        cursor.execute("""
            SELECT subjects.name AS subject_name, 
                   IFNULL(AVG(student_grades.score / student_grades.total_questions * 100), 0) AS avg_score
            FROM subjects
            JOIN exams ON subjects.id = exams.subject_id
            LEFT JOIN student_grades ON exams.id = student_grades.exam_id
            WHERE subjects.teacher = %s
            GROUP BY subjects.id
        """, (username,))

    avg_scores_per_subject = cursor.fetchall()

    # الواجبات التي لم يتم تسليمها بالكامل
    if is_admin:
        cursor.execute("""
            SELECT h.title, s.name AS subject_name,
                   (SELECT COUNT(*) FROM student_subjects WHERE subject_id = s.id) AS total_students,
                   (SELECT COUNT(DISTINCT student_name) FROM homework_submissions WHERE homework_id = h.id) AS submitted_students
            FROM homeworks h
            JOIN subjects s ON h.subject_id = s.id
        """)
    else:
        cursor.execute("""
            SELECT h.title, s.name AS subject_name,
                   (SELECT COUNT(*) FROM student_subjects WHERE subject_id = s.id) AS total_students,
                   (SELECT COUNT(DISTINCT student_name) FROM homework_submissions WHERE homework_id = h.id) AS submitted_students
            FROM homeworks h
            JOIN subjects s ON h.subject_id = s.id
            WHERE s.teacher = %s
        """, (username,))

    homework_submissions = cursor.fetchall()

    for hw in homework_submissions:
        hw['not_submitted'] = hw['total_students'] - hw['submitted_students']

    # أكواد التسجيل
    if is_admin:
        cursor.execute("""
            SELECT subjects.name AS subject_name, 
                   COUNT(CASE WHEN subject_codes.is_used = TRUE THEN 1 END) AS used_codes,
                   COUNT(*) AS total_codes
            FROM subjects
            LEFT JOIN subject_codes ON subjects.id = subject_codes.subject_id
            GROUP BY subjects.id
        """)
    else:
        cursor.execute("""
            SELECT subjects.name AS subject_name, 
                   COUNT(CASE WHEN subject_codes.is_used = TRUE THEN 1 END) AS used_codes,
                   COUNT(*) AS total_codes
            FROM subjects
            LEFT JOIN subject_codes ON subjects.id = subject_codes.subject_id
            WHERE subjects.teacher = %s
            GROUP BY subjects.id
        """, (username,))

    codes_usage = cursor.fetchall()

    for code in codes_usage:
        code['unused_codes'] = code['total_codes'] - code['used_codes']

    cursor.close()

    return render_template('dashboard.html',
                           students_per_subject=students_per_subject,
                           avg_scores_per_subject=avg_scores_per_subject,
                           homework_submissions=homework_submissions,
                           codes_usage=codes_usage)




@app.route('/subject/<int:subject_id>/homeworks')
def subject_homeworks(subject_id):
    if 'loggedin' not in session or session.get('role') not in ['admin', 'teacher']:
        flash("ليس لديك صلاحية للوصول لهذه الصفحة", "danger")
        return redirect(url_for('home'))

    username = session.get('username')
    user_role = session.get('role')
    is_admin = (user_role == 'admin')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # استعلام لجلب الواجبات الخاصة بالمادة
    if is_admin:
        cursor.execute("""
            SELECT h.title, 
                   (SELECT COUNT(*) FROM student_subjects WHERE subject_id = %s) AS total_students,
                   (SELECT COUNT(DISTINCT student_name) FROM homework_submissions WHERE homework_id = h.id) AS submitted_students
            FROM homeworks h
            WHERE h.subject_id = %s
        """, (subject_id, subject_id))
    else:
        cursor.execute("""
            SELECT h.title, 
                   (SELECT COUNT(*) FROM student_subjects WHERE subject_id = %s) AS total_students,
                   (SELECT COUNT(DISTINCT student_name) FROM homework_submissions WHERE homework_id = h.id) AS submitted_students
            FROM homeworks h
            JOIN subjects s ON h.subject_id = s.id
            WHERE h.subject_id = %s AND s.teacher = %s
        """, (subject_id, subject_id, username))

    homeworks = cursor.fetchall()

    for hw in homeworks:
        hw['not_submitted'] = hw['total_students'] - hw['submitted_students']

    cursor.close()

    return render_template('subject_homeworks.html', homeworks=homeworks)


@app.route('/blog')
def blog():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))
    return render_template('blog.html')


@app.route('/freinds')
def freinds():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))
    return render_template('freinds.html')


@app.route('/setting')
def setting():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))
    return render_template('setting.html')


# صفحة النشر
@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        if 'id' in session:  # تعديل التحقق من session['user_id'] إلى session['id']
            user_id = session['id']
            content = request.form['content']

            cursor = mysql.connection.cursor()  # إنشاء كيرسور جديد
            sql = "INSERT INTO posts (user_id, content) VALUES (%s, %s)"
            cursor.execute(sql, (user_id, content))
            mysql.connection.commit()
            cursor.close()  # إغلاق الكيرسور بعد الاستخدام

            return redirect(url_for('home'))
        else:
            return "يجب تسجيل الدخول أولاً"

    return render_template('post.html')


from werkzeug.utils import secure_filename
import os


@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if 'loggedin' not in session or session.get('role') != 'teacher':  # السماح فقط للمدرسين
        flash("ليس لديك الصلاحية لإضافة المواد الدراسية!", "danger")
        return redirect(url_for('subjects'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        teacher = session['username']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO subjects (name, description, teacher) VALUES (%s, %s, %s)",
                       (name, description, teacher))
        mysql.connection.commit()
        cursor.close()

        flash("تمت إضافة المادة بنجاح!", "success")
        return redirect(url_for('subjects'))

    return render_template('add_subject.html')


@app.route('/subjects')
def subjects():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    try:
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            if session['role'] == 'teacher':
                # المعلم يشوف المواد الخاصة بيه فقط
                cursor.execute("""
                    SELECT * 
                    FROM subjects 
                    WHERE BINARY teacher = %s
                """, (session['username'],))

            elif session['role'] == 'student':
                # الطالب يشوف فقط المواد اللي سجل فيها باستخدام الأكواد
                cursor.execute("""
                    SELECT s.* 
                    FROM subjects s
                    JOIN student_subjects ss ON s.id = ss.subject_id
                    WHERE ss.student_id = %s
                """, (session['id'],))

            elif session['role'] == 'assistant':
                # المساعد يشوف فقط المواد اللي تم تعيينه عليها
                cursor.execute("""
                    SELECT s.* 
                    FROM subjects s
                    JOIN assistants a ON s.id = a.subject_id
                    WHERE a.assistant_id = %s
                """, (session['id'],))

            elif session['role'] == 'admin':
                # الأدمن يشوف كل المواد
                cursor.execute("SELECT * FROM subjects")

            subjects = cursor.fetchall()

        return render_template('subjects.html', subjects=subjects)

    except Exception as e:
        flash(f"حدث خطأ أثناء جلب المواد: {str(e)}", "danger")
        return redirect(url_for('subjects'))


@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    if 'loggedin' not in session or not is_teacher_or_assistant(subject_id):
        flash("ليس لديك الصلاحية لتعديل هذه المادة!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب بيانات المادة الحالية
    cursor.execute("SELECT * FROM subjects WHERE id = %s", (subject_id,))
    subject = cursor.fetchone()

    if not subject:
        flash("المادة غير موجودة!", 'danger')
        return redirect(url_for('subjects'))

    if request.method == 'POST':
        name = request.form['name']

        try:
            cursor.execute("""
                UPDATE subjects 
                SET name = %s 
                WHERE id = %s
            """, (name, subject_id))
            mysql.connection.commit()
            flash('تم تحديث المادة بنجاح', 'success')
            return redirect(url_for('subjects'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'danger')

    cursor.close()

    return render_template('edit_subject.html', subject=subject)



@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية لحذف هذه المادة!", "danger")
        return redirect(url_for('subjects'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # جلب بيانات المادة
        cursor.execute("""
            SELECT teacher 
            FROM subjects 
            WHERE id = %s
        """, (subject_id,))
        result = cursor.fetchone()

        # التحقق من أن المدرس الحالي هو صاحب المادة
        if not result or result['teacher'] != session['username']:
            flash("غير مصرح بهذه العملية!", 'danger')
            return redirect(url_for('subjects'))

        # تنفيذ الحذف
        cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
        mysql.connection.commit()
        flash("تم حذف المادة بنجاح!", 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f"حدث خطأ أثناء الحذف: {str(e)}", 'danger')

    finally:
        cursor.close()

    return redirect(url_for('subjects'))




@app.route('/generate_subject_codes/<int:subject_id>', methods=['POST'])
def generate_subject_codes(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("يجب تسجيل الدخول كمعلم", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor()
    for _ in range(50):  # مثلا يولد 50 كود
        random_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))
        cursor.execute('''
            INSERT INTO subject_codes (subject_id, code)
            VALUES (%s, %s)
        ''', (subject_id, random_code))

    mysql.connection.commit()
    cursor.close()

    flash(f"تم توليد 50 كود للمادة رقم {subject_id} بنجاح!", "success")
    return redirect(url_for('subject_page', subject_id=subject_id))


@app.route('/enroll_subject', methods=['POST'])
def enroll_subject():
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول", "danger")
        return redirect(url_for('auth'))

    code = request.form['code']
    student_id = session['id']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # التحقق من صحة الكود وهل تم استخدامه
    cursor.execute('''
        SELECT * FROM subject_codes 
        WHERE code = %s AND is_used = FALSE
    ''', (code,))
    code_data = cursor.fetchone()

    if not code_data:
        flash("الكود غير صالح أو تم استخدامه", "danger")
        return redirect(url_for('subjects'))

    # تسجيل الطالب في المادة وتحديث حالة الكود مع حفظ تاريخ التسجيل
    cursor.execute('''
        INSERT INTO student_subjects (student_id, subject_id) 
        VALUES (%s, %s)
    ''', (student_id, code_data['subject_id']))

    cursor.execute('''
        UPDATE subject_codes 
        SET is_used = TRUE, used_by = %s, used_at = NOW()
        WHERE id = %s
    ''', (student_id, code_data['id']))

    mysql.connection.commit()
    cursor.close()

    flash("تم تسجيلك في المادة بنجاح!", "success")
    return redirect(url_for('subjects'))


@app.route('/subject_codes/<int:subject_id>')
def subject_codes(subject_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        flash("يجب تسجيل الدخول كمعلم", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT code, is_used, used_by 
        FROM subject_codes 
        WHERE subject_id = %s
    ''', (subject_id,))

    codes = cursor.fetchall()
    cursor.close()

    return render_template('subject_codes.html', codes=codes, subject_id=subject_id)


@app.route('/registered_students/<int:subject_id>')
def registered_students(subject_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        flash("يجب تسجيل الدخول كمعلم", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT a.username AS student_name, s.code, s.used_at 
        FROM subject_codes s
        JOIN accounts a ON s.used_by = a.id  -- افتراض أن `used_by` يشير إلى `id` للطالب
        WHERE s.subject_id = %s AND s.is_used = 1
    ''', (subject_id,))

    students = cursor.fetchall()
    cursor.close()

    return render_template('registered_students.html', students=students, subject_id=subject_id)


@app.route('/available_codes/<int:subject_id>')
def available_codes(subject_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        flash("يجب تسجيل الدخول كمعلم", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT code 
        FROM subject_codes
        WHERE subject_id = %s AND is_used = 0
    ''', (subject_id,))

    codes = cursor.fetchall()
    cursor.close()

    return render_template('available_codes.html', codes=codes, subject_id=subject_id)



@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if 'loggedin' not in session or session.get('role') != 'teacher':
        return redirect(url_for('auth'))

    if request.method == 'POST':
        question_text = request.form['question_text']
        question_type = request.form['question_type']
        correct_answer = request.form['correct_answer']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO questions (subject_id, question_text, question_type, correct_answer) VALUES (%s, %s, %s, %s)",
                       (1, question_text, question_type, correct_answer))
        question_id = cursor.lastrowid

        if question_type == 'mcq':
            choices = request.form['choices'].split("\n")
            for choice in choices:
                cursor.execute("INSERT INTO choices (question_id, choice_text) VALUES (%s, %s)", (question_id, choice.strip()))

        mysql.connection.commit()
        cursor.close()
        flash("تمت إضافة السؤال بنجاح!", "success")

    return render_template('add_question.html')







@app.route('/exam')

def list_exams():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, exam_name FROM exams")  # جلب جميع الامتحانات
        exams = cursor.fetchall()
        return render_template('exams_list.html', exams=exams)  # صفحة تحتوي على روابط الامتحانات
    return redirect(url_for('auth'))


@app.route('/exam/')
def exam():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()

    for question in questions:
        if question['question_type'] == 'mcq':
            cursor.execute("SELECT * FROM choices WHERE question_id = %s", (question['id'],))
            question['choices'] = cursor.fetchall()

    cursor.close()
    return render_template('exam.html', questions=questions)









from datetime import datetime, timedelta

def get_exam_settings(exam_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM exam_settings WHERE exam_id = %s", (exam_id,))
    return cursor.fetchone()

def get_student_attempts(user_id, exam_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM student_grades WHERE user_id = %s AND exam_id = %s", (user_id, exam_id))
    return cursor.fetchone()[0]


from datetime import datetime, timedelta

from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, url_for, flash, session
import MySQLdb.cursors
from datetime import datetime, timedelta

@app.route('/exam/<int:exam_id>/', methods=['GET', 'POST'])
def take_exam(exam_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        user_id = session['id']

        # ✅ جلب بيانات الامتحان ومعرفة `subject_id`
        cursor.execute("SELECT exam_name, subject_id FROM exams WHERE id = %s", (exam_id,))
        exam = cursor.fetchone()

        if not exam:
            flash("الامتحان غير موجود!", "danger")
            return redirect(url_for('subjects'))  # ✅ إذا لم يكن الامتحان موجودًا، عد إلى قائمة المواد

        exam_name = exam['exam_name']
        subject_id = exam['subject_id']  # ✅ حفظ `subject_id` لاستخدامه عند إعادة التوجيه

        # ✅ جلب الإعدادات الخاصة بالامتحان
        cursor.execute("SELECT * FROM exam_settings WHERE exam_id = %s", (exam_id,))
        settings = cursor.fetchone()

        if not settings:
            flash("إعدادات الامتحان غير متوفرة!", "danger")
            return redirect(url_for('subject_page', subject_id=subject_id))  # ✅ العودة لصفحة المادة

        start_time = settings['start_time']
        end_time = settings['end_time']
        exam_duration = settings['exam_duration']
        max_attempts = settings['max_attempts']  # ✅ عدد المحاولات المسموح بها

        now = datetime.now()

        # ✅ التحقق من النطاق الزمني
        if now < start_time:
            flash(f"الامتحان لم يبدأ بعد! يبدأ في: {start_time.strftime('%Y-%m-%d %H:%M')}", "danger")
            return redirect(url_for('subject_page', subject_id=subject_id))  # ✅ العودة لصفحة المادة

        if now > end_time:
            flash(f"انتهى وقت الامتحان! انتهى في: {end_time.strftime('%Y-%m-%d %H:%M')}", "danger")
            return redirect(url_for('subject_page', subject_id=subject_id))  # ✅ العودة لصفحة المادة

        # ✅ التحقق من عدد المحاولات السابقة للطالب
        cursor.execute("SELECT COUNT(*) AS attempts FROM student_grades WHERE user_id = %s AND exam_id = %s", (user_id, exam_id))
        attempt_data = cursor.fetchone()
        attempts = attempt_data['attempts'] if attempt_data else 0

        if attempts >= max_attempts:
            flash(f"لقد استنفدت كل محاولاتك لهذا الامتحان! ({max_attempts} محاولات كحد أقصى)", "danger")
            return redirect(url_for('subject_page', subject_id=subject_id))  # ✅ العودة لصفحة المادة

        # ✅ حساب وقت انتهاء الطالب بناءً على وقت دخوله
        student_end_time = now + timedelta(minutes=exam_duration)

        # ✅ إذا كان وقت انتهاء الطالب بعد وقت انتهاء الامتحان، يتم ضبط وقته ليكون ضمن النطاق
        if student_end_time > end_time:
            student_end_time = end_time

        # ✅ جلب الأسئلة
        cursor.execute("""
            SELECT q.id, q.question_text, q.question_type, q.correct_answer 
            FROM exam_questions eq
            JOIN questions q ON eq.question_id = q.id
            WHERE eq.exam_id = %s
        """, (exam_id,))
        questions = cursor.fetchall()

        # ✅ جلب الخيارات للأسئلة متعددة الاختيارات
        for question in questions:
            if question['question_type'] == 'mcq':
                cursor.execute("SELECT choice_text FROM choices WHERE question_id = %s", (question['id'],))
                question['choices'] = cursor.fetchall()

        return render_template('exam.html',
                               exam_id=exam_id,
                               exam_name=exam_name,
                               questions=questions,
                               student_end_time=int(student_end_time.timestamp()),  # إرسال كـ timestamp لاستخدامه في JavaScript
                               exam_duration=exam_duration)  # إرسال مدة الامتحان لاستخدامها في العداد التنازلي

    except Exception as e:
        flash(f"حدث خطأ: {str(e)}", "danger")
        return redirect(url_for('subject_page', subject_id=subject_id))  # ✅ العودة لصفحة المادة عند حدوث أي خطأ

    finally:
        cursor.close()




from datetime import datetime

@app.route('/add_exam/<int:subject_id>', methods=['GET', 'POST'])
def add_exam(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        exam_name = request.form.get('exam_name')
        exam_description = request.form.get('exam_description')

        # ✅ جلب القيم الجديدة
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        exam_duration = int(request.form.get('exam_duration'))  # مدة الامتحان لكل طالب بالدقائق
        max_attempts = int(request.form.get('max_attempts'))  # عدد المحاولات المسموحة

        # ✅ دمج التاريخ مع الأوقات
        full_start_time = f"{start_date} {start_time}"
        full_end_time = f"{start_date} {end_time}"

        # ✅ التأكد من أن وقت النهاية بعد وقت البداية
        start_datetime = datetime.strptime(full_start_time, "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(full_end_time, "%Y-%m-%d %H:%M")

        if end_datetime <= start_datetime:
            flash("وقت نهاية الامتحان يجب أن يكون بعد وقت البداية!", "danger")
            return redirect(url_for('add_exam', subject_id=subject_id))

        # ✅ إدخال الامتحان في قاعدة البيانات
        cursor.execute(
            "INSERT INTO exams (subject_id, exam_name, description) VALUES (%s, %s, %s)",
            (subject_id, exam_name, exam_description)
        )
        exam_id = cursor.lastrowid  # للحصول على ID الامتحان الجديد
        mysql.connection.commit()

        # ✅ حفظ وقت البداية والنهاية والمدة في exam_settings
        cursor.execute(
            "INSERT INTO exam_settings (exam_id, start_time, end_time, exam_duration, max_attempts) VALUES (%s, %s, %s, %s, %s)",
            (exam_id, start_datetime, end_datetime, exam_duration, max_attempts)
        )
        mysql.connection.commit()

        # ✅ جلب اسم المادة
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT name FROM subjects WHERE id = %s", (subject_id,))
        subject = cursor.fetchone()
        subject_name = subject['name'] if subject else 'مادة غير معروفة'

        # ✅ إرسال إشعار لكل الطلاب المسجلين في المادة
        cursor.execute('SELECT student_id FROM student_subjects WHERE subject_id = %s', (subject_id,))
        students = cursor.fetchall()

        for student in students:
            cursor.execute('''
                INSERT INTO notifications (user_id, message, notification_type, related_id)
                VALUES (%s, %s, %s, %s)
            ''', (student['student_id'], f"تم إضافة امتحان جديد '{exam_name}' في مادة {subject_name}", 'subject_id', subject_id))

        mysql.connection.commit()
        cursor.close()

        flash("تم إنشاء الامتحان بنجاح!", "success")
        return redirect(url_for('add_questions_to_exam', exam_id=exam_id))

    return render_template('add_exam.html', subject_id=subject_id)

@app.route('/add_questions_to_exam/<int:exam_id>', methods=['GET', 'POST'])
def add_questions_to_exam(exam_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ جلب subject_id من جدول exams
    cursor.execute("SELECT subject_id FROM exams WHERE id = %s", (exam_id,))
    exam = cursor.fetchone()
    subject_id = exam['subject_id'] if exam else None

    if request.method == 'POST':
        print(request.form)  # ✅ عرض القيم القادمة من النموذج لفحصها

        if 'add_bank_question' in request.form:
            bank_question_id = request.form.get('bank_question_id')

            cursor.execute('SELECT * FROM question_bank WHERE id = %s', (bank_question_id,))
            bank_question = cursor.fetchone()

            question_type = bank_question['question_type']

            # ✅ إدراج السؤال مع `source_id` للإشارة إلى مصدره في بنك الأسئلة
            cursor.execute('''
                INSERT INTO questions (question_text, question_type, correct_answer, source, source_id)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                bank_question['question_text'],
                question_type,
                bank_question['correct_option'],
                'bank',
                bank_question['id']
            ))
            question_id = cursor.lastrowid

            # ✅ ربط السؤال بالامتحان
            cursor.execute(
                "INSERT INTO exam_questions (exam_id, question_id) VALUES (%s, %s)",
                (exam_id, question_id)
            )

            # ✅ إدخال الخيارات إذا كان السؤال اختيار من متعدد
            if question_type == 'mcq':
                options = [
                    bank_question['option_1'],
                    bank_question['option_2'],
                    bank_question['option_3'],
                    bank_question['option_4']
                ]
                for option in options:
                    if option:
                        cursor.execute("INSERT INTO choices (question_id, choice_text) VALUES (%s, %s)", (question_id, option))

            elif question_type == 'true_false':
                for option in ['صح', 'خطأ']:
                    cursor.execute("INSERT INTO choices (question_id, choice_text) VALUES (%s, %s)", (question_id, option))

            mysql.connection.commit()
            flash("تمت إضافة السؤال من بنك الأسئلة بنجاح!", "success")

        else:
            question_text = request.form.get('question_text')
            question_type = request.form.get('question_type')
            grade = request.form.get('grade')  # ✅ استخراج الصف الدراسي
            correct_answer = None
            save_to_bank = 'save_to_bank' in request.form  # ✅ تحديد إذا كان السؤال سيُحفظ في بنك الأسئلة

            if question_type == 'mcq':
                correct_choice = request.form.get('correct_choice')
                choices = [
                    request.form.get('choice1'),
                    request.form.get('choice2'),
                    request.form.get('choice3'),
                    request.form.get('choice4')
                ]
                correct_answer = choices[int(correct_choice) - 1]

            elif question_type == 'true_false':
                correct_answer = request.form.get('correct_answer_tf')

            elif question_type == 'short_answer':
                correct_answer = request.form.get('correct_answer_short')

            print(f"🚀 إضافة سؤال جديد: {question_text}, النوع: {question_type}, الصف الدراسي: {grade}, الإجابة الصحيحة: {correct_answer}")

            if not question_text or not question_type or correct_answer is None or not grade:
                flash("يرجى ملء جميع الحقول واختيار الإجابة الصحيحة!", "danger")
                return redirect(url_for('add_questions_to_exam', exam_id=exam_id))

            # ✅ إدخال السؤال في جدول `questions`
            cursor.execute(
                "INSERT INTO questions (question_text, question_type, correct_answer, source) VALUES (%s, %s, %s, %s)",
                (question_text, question_type, correct_answer, 'manual')
            )
            question_id = cursor.lastrowid

            # ✅ ربط السؤال بالامتحان
            cursor.execute(
                "INSERT INTO exam_questions (exam_id, question_id) VALUES (%s, %s)",
                (exam_id, question_id)
            )

            # ✅ إدخال الخيارات في حالة MCQ
            if question_type == 'mcq':
                for choice in choices:
                    if choice:
                        cursor.execute(
                            "INSERT INTO choices (question_id, choice_text) VALUES (%s, %s)",
                            (question_id, choice)
                        )

            elif question_type == 'true_false':
                for option in ['صح', 'خطأ']:
                    cursor.execute("INSERT INTO choices (question_id, choice_text) VALUES (%s, %s)", (question_id, option))

            # ✅ حفظ السؤال في بنك الأسئلة إذا تم تحديد الخيار
            if save_to_bank:
                cursor.execute("""
                    INSERT INTO question_bank (question_text, question_type, correct_option, option_1, option_2, option_3, option_4, subject_id, grade)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    question_text, question_type, correct_answer,
                    choices[0] if question_type == 'mcq' else None,
                    choices[1] if question_type == 'mcq' else None,
                    choices[2] if question_type == 'mcq' else None,
                    choices[3] if question_type == 'mcq' else None,
                    subject_id, grade
                ))

            mysql.connection.commit()
            flash("تمت إضافة السؤال بنجاح!", "success")

        return redirect(url_for('add_questions_to_exam', exam_id=exam_id))

    # ✅ جلب الأسئلة المضافة لهذا الامتحان
    cursor.execute("""
        SELECT q.id, q.question_text, q.question_type, q.correct_answer, q.source 
        FROM exam_questions eq
        JOIN questions q ON eq.question_id = q.id
        WHERE eq.exam_id = %s
    """, (exam_id,))
    questions = cursor.fetchall()

    for question in questions:
        if question['question_type'] == 'mcq':
            cursor.execute("SELECT choice_text FROM choices WHERE question_id = %s", (question['id'],))
            question['choices'] = cursor.fetchall()

    # ✅ استبعاد الأسئلة المضافة من بنك الأسئلة
    cursor.execute("""
        SELECT qb.* 
        FROM question_bank qb
        WHERE qb.subject_id = %s 
        AND NOT EXISTS (
            SELECT 1 FROM exam_questions eq
            JOIN questions q ON eq.question_id = q.id
            WHERE eq.exam_id = %s 
            AND q.source = 'bank' 
            AND q.source_id = qb.id
        )
    """, (subject_id, exam_id))

    bank_questions = cursor.fetchall()

    cursor.close()

    return render_template('add_questions_to_exam.html',
                           exam_id=exam_id,
                           questions=questions,
                           bank_questions=bank_questions,
                           subject_id=subject_id)  # ✅ تمرير subject_id إلى القالب




@app.route('/add_bank_question/<int:exam_id>/<int:question_id>', methods=['POST'])
def add_bank_question(exam_id, question_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        return jsonify({"success": False, "message": "يجب تسجيل الدخول"}), 403

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # ✅ جلب السؤال من بنك الأسئلة
        cursor.execute('SELECT * FROM question_bank WHERE id = %s', (question_id,))
        bank_question = cursor.fetchone()

        if not bank_question:
            return jsonify({"success": False, "message": "السؤال غير موجود في بنك الأسئلة"}), 404

        # ✅ إدراج السؤال في جدول `questions`
        cursor.execute('''
            INSERT INTO questions (question_text, question_type, correct_answer, source)
            VALUES (%s, %s, %s, %s)
        ''', (bank_question['question_text'], bank_question['question_type'], bank_question['correct_option'], 'bank'))
        question_id_new = cursor.lastrowid

        # ✅ ربط السؤال بالامتحان
        cursor.execute("INSERT INTO exam_questions (exam_id, question_id) VALUES (%s, %s)", (exam_id, question_id_new))

        # ✅ إدخال الاختيارات إذا كان السؤال MCQ
        if bank_question['question_type'] == 'mcq':
            choices = [
                bank_question['option_1'],
                bank_question['option_2'],
                bank_question['option_3'],
                bank_question['option_4']
            ]
            for choice in choices:
                if choice:
                    cursor.execute("INSERT INTO choices (question_id, choice_text) VALUES (%s, %s)", (question_id_new, choice))

        elif bank_question['question_type'] == 'true_false':
            for option in ['صح', 'خطأ']:
                cursor.execute("INSERT INTO choices (question_id, choice_text) VALUES (%s, %s)", (question_id_new, option))

        mysql.connection.commit()
        return jsonify({"success": True})  # ✅ إرسال استجابة ناجحة

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()






@app.route('/subject_exams/<int:subject_id>/')
def subject_exams(subject_id):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, exam_name FROM exams WHERE subject_id = %s", (subject_id,))
        exams = cursor.fetchall()
        return render_template('subject_exams.html', exams=exams, subject_id=subject_id)
    return redirect(url_for('auth'))


@app.route('/student_grades')
def student_grades():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # جلب درجات الطالب
        cursor.execute("""
            SELECT sg.score, sg.total_questions, sg.grade_date, e.exam_name 
            FROM student_grades sg
            JOIN exams e ON sg.exam_id = e.id
            WHERE sg.user_id = %s
            ORDER BY sg.grade_date DESC
        """, (session['id'],))
        grades = cursor.fetchall()

        return render_template('student_grades.html', grades=grades)

    except Exception as e:
        flash(f"حدث خطأ: {str(e)}", "danger")
        return redirect(url_for('home'))

    finally:
        cursor.close()  # إغلاق الكيرسور في النهاية

from flask import jsonify

from flask import jsonify, redirect, url_for

from flask import jsonify
@app.route('/submit_exam/<int:exam_id>', methods=['POST'])
def submit_exam(exam_id):
    if 'loggedin' not in session:
        return jsonify({"success": False, "message": "يرجى تسجيل الدخول!"}), 403

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        user_id = session['id']
        score = 0

        # ✅ التحقق من عدد المحاولات السابقة
        cursor.execute("""
            SELECT COUNT(*) AS attempts 
            FROM student_grades 
            WHERE user_id = %s AND exam_id = %s
        """, (user_id, exam_id))
        attempt_data = cursor.fetchone()
        attempts = attempt_data['attempts'] if attempt_data else 0

        # ✅ جلب الحد الأقصى للمحاولات
        cursor.execute("""
            SELECT max_attempts 
            FROM exam_settings 
            WHERE exam_id = %s
        """, (exam_id,))
        settings = cursor.fetchone()
        max_attempts = settings['max_attempts']

        if attempts >= max_attempts:
            return jsonify({"success": False, "message": "لقد استنفدت كل محاولاتك لهذا الامتحان!"}), 400

        # ✅ جلب أسئلة الامتحان المحدد
        cursor.execute("""
            SELECT q.id, q.correct_answer 
            FROM exam_questions eq
            JOIN questions q ON eq.question_id = q.id
            WHERE eq.exam_id = %s
        """, (exam_id,))
        questions = cursor.fetchall()

        # ✅ تسجيل وقت البدء قبل حفظ الإجابات
        start_time = request.form.get("start_time")
        if start_time:
            cursor.execute("""
                INSERT INTO student_grades (user_id, exam_id, start_time) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE start_time = %s
            """, (user_id, exam_id, start_time, start_time))
            mysql.connection.commit()

        # ✅ حفظ إجابات الطالب
        for question in questions:
            question_id = question['id']
            user_answer = request.form.get(f"q{question_id}", "")

            correct_answer = question['correct_answer']
            is_correct = (user_answer == correct_answer)

            if is_correct:
                score += 1

            cursor.execute(
                "INSERT INTO answers (user_id, question_id, user_answer, is_correct) VALUES (%s, %s, %s, %s)",
                (user_id, question_id, user_answer, is_correct)
            )

        total_questions = len(questions)

        # ✅ تسجيل النتيجة وتحديث وقت انتهاء الامتحان
        cursor.execute("""
            UPDATE student_grades 
            SET score = %s, total_questions = %s, end_time = NOW() 
            WHERE user_id = %s AND exam_id = %s
        """, (score, total_questions, user_id, exam_id))

        mysql.connection.commit()

        # ✅ تحديث تقرير التقدم بعد تسجيل النتيجة
        cursor.execute("SELECT subject_id FROM exams WHERE id = %s", (exam_id,))
        subject_data = cursor.fetchone()
        if subject_data:
            update_student_progress(user_id, subject_data['subject_id'])

        return jsonify({
            "success": True,
            "redirect_url": url_for('exam_result', exam_id=exam_id, score=score, total=total_questions)
        })

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()

@app.route('/exam_result/<int:exam_id>/<int:score>/<int:total>')
def exam_result(exam_id, score, total):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    return render_template('exam_result.html', exam_id=exam_id, score=score, total=total)

@app.route('/teacher_grades', methods=['GET'])
def teacher_grades():
    if 'loggedin' not in session or session.get('role') != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # جلب جميع الامتحانات التي أنشأها المعلم
        cursor.execute("""
            SELECT e.id AS exam_id, e.exam_name, s.name AS subject_name
            FROM exams e
            JOIN subjects s ON e.subject_id = s.id
            WHERE s.teacher = %s
        """, (session['username'],))
        exams = cursor.fetchall()

        # جلب الامتحان المحدد (إذا تم اختياره)
        selected_exam_id = request.args.get('exam_id')
        selected_exam = None

        if selected_exam_id:
            # جلب تفاصيل الامتحان المحدد
            cursor.execute("""
                SELECT e.id AS exam_id, e.exam_name, s.name AS subject_name
                FROM exams e
                JOIN subjects s ON e.subject_id = s.id
                WHERE e.id = %s AND s.teacher = %s
            """, (selected_exam_id, session['username']))
            selected_exam = cursor.fetchone()

            # جلب درجات الطلاب للامتحان المحدد
            if selected_exam:
                cursor.execute("""
                    SELECT a.username, sg.score, sg.total_questions, sg.grade_date
                    FROM student_grades sg
                    JOIN accounts a ON sg.user_id = a.id
                    WHERE sg.exam_id = %s
                    ORDER BY sg.grade_date DESC
                """, (selected_exam_id,))
                selected_exam['grades'] = cursor.fetchall()

        return render_template(
            'teacher_grades.html',
            exams=exams,
            selected_exam_id=selected_exam_id,
            selected_exam=selected_exam
        )

    except Exception as e:
        flash(f"حدث خطأ: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()  # إغلاق الكيرسور في النهاية


@app.route('/view_student_grades', methods=['GET'])
def view_student_grades():
    if 'loggedin' not in session or session.get('role') != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # جلب جميع الامتحانات مع اسم المادة
        cursor.execute("""
            SELECT e.id AS exam_id, e.exam_name, s.name AS subject_name
            FROM exams e
            JOIN subjects s ON e.subject_id = s.id
        """)
        exams = cursor.fetchall()

        # جلب الامتحان المحدد (إذا تم اختياره)
        selected_exam_id = request.args.get('exam_id')
        selected_exam = None

        if selected_exam_id:
            # جلب تفاصيل الامتحان المحدد
            cursor.execute("""
                SELECT e.id AS exam_id, e.exam_name, s.name AS subject_name
                FROM exams e
                JOIN subjects s ON e.subject_id = s.id
                WHERE e.id = %s
            """, (selected_exam_id,))
            selected_exam = cursor.fetchone()

            # جلب درجات الطلاب للامتحان المحدد
            if selected_exam:
                cursor.execute("""
                    SELECT a.username, sg.score, sg.total_questions, sg.grade_date
                    FROM student_grades sg
                    JOIN accounts a ON sg.user_id = a.id
                    WHERE sg.exam_id = %s
                    ORDER BY sg.grade_date DESC
                """, (selected_exam_id,))
                selected_exam['grades'] = cursor.fetchall()

        return render_template(
            'view_student_grades.html',
            exams=exams,
            selected_exam_id=selected_exam_id,
            selected_exam=selected_exam
        )

    except Exception as e:
        flash(f"حدث خطأ: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

    finally:
        cursor.close()



# ---- Routes للتحكم في الامتحانات ----
@app.route('/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
def edit_exam(exam_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # ✅ جلب بيانات الامتحان وإعداداته
        cursor.execute("""
            SELECT e.*, es.start_time, es.end_time, es.exam_duration, es.max_attempts 
            FROM exams e
            LEFT JOIN exam_settings es ON e.id = es.exam_id
            WHERE e.id = %s
        """, (exam_id,))
        exam = cursor.fetchone()

        if not exam:
            flash("الامتحان غير موجود!", "danger")
            return redirect(url_for('subjects'))

        # ✅ معالجة طلب التحديث
        if request.method == 'POST':
            new_name = request.form.get('exam_name')
            new_description = request.form.get('description')
            start_date = request.form.get('start_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            exam_duration = request.form.get('exam_duration')
            max_attempts = request.form.get('max_attempts')

            if not new_name or not new_description or not start_date or not start_time or not end_time or not exam_duration or not max_attempts:
                flash("الرجاء ملء جميع الحقول!", "danger")
                return redirect(url_for('edit_exam', exam_id=exam_id))

            # ✅ تحويل `start_date` و `start_time` و `end_time` إلى `datetime`
            full_start_time = f"{start_date} {start_time}"
            full_end_time = f"{start_date} {end_time}"  # ❗ استخدم نفس التاريخ للـ `end_time` مبدئيًا

            # ✅ التحقق مما إذا كان `end_time` قبل `start_time`
            if full_end_time <= full_start_time:
                flash("وقت نهاية الامتحان يجب أن يكون بعد وقت البداية!", "danger")
                return redirect(url_for('edit_exam', exam_id=exam_id))

            # ✅ تحديث جدول `exams`
            cursor.execute("""
                UPDATE exams 
                SET exam_name = %s, description = %s
                WHERE id = %s
            """, (new_name, new_description, exam_id))

            # ✅ تحديث جدول `exam_settings`
            cursor.execute("""
                UPDATE exam_settings 
                SET start_time = %s, end_time = %s, exam_duration = %s, max_attempts = %s
                WHERE exam_id = %s
            """, (full_start_time, full_end_time, exam_duration, max_attempts, exam_id))

            mysql.connection.commit()

            flash("تم تحديث الامتحان بنجاح!", "success")
            return redirect(url_for('add_questions_to_exam', exam_id=exam_id))

        return render_template('edit_exam.html', exam=exam)

    except Exception as e:
        flash(f"حدث خطأ: {str(e)}", "danger")
        return redirect(url_for('subjects'))

    finally:
        cursor.close()

# حذف الامتحان
@app.route('/delete_exam/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor()

    try:
        # التحقق من أن المعلم هو صاحب المادة
        cursor.execute("""
            SELECT e.id 
            FROM exams e
            INNER JOIN subjects s ON e.subject_id = s.id
            WHERE e.id = %s AND s.teacher = %s
        """, (exam_id, session['username']))

        if not cursor.fetchone():
            flash("ليست لديك صلاحية لهذا الإجراء", "danger")
            return redirect(url_for('subjects'))

        # حذف الدرجات المرتبطة أولاً
        cursor.execute("DELETE FROM student_grades WHERE exam_id = %s", (exam_id,))

        # حذف الامتحان
        cursor.execute("DELETE FROM exams WHERE id = %s", (exam_id,))

        mysql.connection.commit()
        flash("تم الحذف بنجاح", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"خطأ في الحذف: {str(e)}", "danger")

    finally:
        cursor.close()

    return redirect(url_for('subjects'))


# حذف السؤال
@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    exam_id = None  # تعريف متغير exam_id

    try:
        # جلب exam_id المرتبط بالسؤال
        cursor.execute("SELECT exam_id FROM exam_questions WHERE question_id = %s", (question_id,))
        exam_data = cursor.fetchone()
        if exam_data:
            exam_id = exam_data['exam_id']

        # حذف الاختيارات أولاً
        cursor.execute("DELETE FROM choices WHERE question_id = %s", (question_id,))
        # حذف الربط بين الامتحان والسؤال
        cursor.execute("DELETE FROM exam_questions WHERE question_id = %s", (question_id,))
        # حذف السؤال
        cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        mysql.connection.commit()
        flash("تم حذف السؤال بنجاح", "success")

    except Exception as e:
        flash(f"حدث خطأ أثناء الحذف: {str(e)}", "danger")

    finally:
        cursor.close()

    # التأكد من وجود exam_id قبل التوجيه
    if exam_id is not None:
        return redirect(url_for('add_questions_to_exam', exam_id=exam_id))
    else:
        flash("لم يتم العثور على الامتحان المرتبط", "danger")
        return redirect(url_for('dashboard'))

# تعديل السؤال
@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    exam_id = None

    try:
        # الحصول على الامتحان المرتبط بالسؤال
        cursor.execute("""
            SELECT exam_id FROM exam_questions 
            WHERE question_id = %s 
            LIMIT 1
        """, (question_id,))
        exam_data = cursor.fetchone()

        if not exam_data:
            flash("لم يتم ربط السؤال بأي امتحان", "warning")
            return redirect(url_for('dashboard'))

        exam_id = exam_data['exam_id']

        # جلب بيانات السؤال
        cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
        question = cursor.fetchone()

        if not question:
            flash("السؤال غير موجود", "danger")
            return redirect(url_for('dashboard'))

        # جلب الاختيارات لو السؤال MCQ
        choices = []
        if question['question_type'] == 'mcq':
            cursor.execute("""
                SELECT * FROM choices 
                WHERE question_id = %s 
                ORDER BY choice_order
            """, (question_id,))
            choices = cursor.fetchall()

        if request.method == 'POST':
            # جلب البيانات الجديدة من النموذج
            new_text = request.form['question_text']
            new_type = request.form['question_type']
            correct_answer = ""

            if new_type == 'mcq':
                # جلب correct_answer من الاختيار المحدد
                correct_choice_number = request.form.get('correct_choice', '')
                if correct_choice_number:
                    correct_choice_index = int(correct_choice_number) - 1
                    correct_answer = request.form.get(f'choice{correct_choice_number}', '')
            elif new_type == 'true_false':
                correct_answer = request.form.get('correct_answer', '')
            elif new_type == 'short_answer':
                correct_answer = request.form.get('correct_answer', '')

            # تحديث بيانات السؤال
            cursor.execute("""
                UPDATE questions 
                SET question_text = %s,
                    question_type = %s,
                    correct_answer = %s 
                WHERE id = %s
            """, (new_text, new_type, correct_answer, question_id))

            # تحديث الاختيارات في حالة MCQ
            if new_type == 'mcq':
                # حذف الخيارات القديمة
                cursor.execute("DELETE FROM choices WHERE question_id = %s", (question_id,))

                # إضافة الخيارات الجديدة (4 افتراضياً، ويمكن جعله ديناميكي لو تحب)
                for i in range(1, 5):
                    choice_text = request.form.get(f'choice{i}', '').strip()
                    if choice_text:
                        cursor.execute("""
                            INSERT INTO choices (question_id, choice_order, choice_text) 
                            VALUES (%s, %s, %s)
                        """, (question_id, i, choice_text))
            else:
                # لو مش MCQ احذف كل الخيارات
                cursor.execute("DELETE FROM choices WHERE question_id = %s", (question_id,))

            mysql.connection.commit()
            flash("تم تحديث السؤال بنجاح ✅", "success")
            return redirect(url_for('add_questions_to_exam', exam_id=exam_id))

        return render_template('edit_question.html',
                               question=question,
                               choices=choices,
                               exam_id=exam_id)

    except Exception as e:
        flash(f"حدث خطأ غير متوقع: {str(e)}", "danger")
        return redirect(url_for('add_questions_to_exam', exam_id=exam_id)) if exam_id else redirect(url_for('dashboard'))

    finally:
        cursor.close()


@app.route('/toggle_exam_visibility/<int:exam_id>', methods=['POST'])
def toggle_exam_visibility(exam_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor()

    try:
        # التحقق من ملكية المادة
        cursor.execute("""
            SELECT e.id 
            FROM exams e
            INNER JOIN subjects s ON e.subject_id = s.id
            WHERE e.id = %s AND s.teacher = %s
        """, (exam_id, session['username']))

        if not cursor.fetchone():
            flash("ليست لديك صلاحية لهذا الإجراء", "danger")
            return redirect(url_for('subjects'))

        # تبديل الحالة
        cursor.execute("""
            UPDATE exams 
            SET is_visible = NOT is_visible 
            WHERE id = %s
        """, (exam_id,))

        mysql.connection.commit()
        flash("تم تغيير الحالة بنجاح", "success")

    except Exception as e:
        mysql.connection.rollback()
        flash(f"خطأ في التحديث: {str(e)}", "danger")

    finally:
        cursor.close()

    return redirect(url_for('subjects'))



import pymysql


# إعداد اتصال قاعدة البيانات
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='loginapp',
        cursorclass=pymysql.cursors.DictCursor
    )

# عرض صفحة المادة + الواجبات

from datetime import datetime, date

from datetime import datetime


@app.route('/subject/<int:subject_id>')
def subject_page(subject_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))
    now = datetime.now()
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # ✅ جلب بيانات المادة مع حالة التقييم
        cursor.execute("SELECT id, name, teacher, description, evaluation_status FROM subjects WHERE id = %s",
                       (subject_id,))
        subject = cursor.fetchone()

        if not subject:
            flash("المادة غير موجودة!", "danger")
            return redirect(url_for('subjects'))

        # ✅ التحقق من الصلاحيات لو المستخدم مساعد
        permissions = {}
        if session.get('role') == 'assistant':
            cursor.execute("""
                SELECT * FROM assistant_permissions 
                WHERE assistant_id = %s AND subject_id = %s
            """, (session['id'], subject_id))
            permissions = cursor.fetchone() or {}  # لو مفيش صلاحيات، يرجع قاموس فاضي
        # ✅ جلب جميع الدروس الخاصة بالمادة
        cursor.execute("SELECT COUNT(*) AS total_lessons FROM lessons WHERE subject_id = %s", (subject_id,))
        total_lessons = cursor.fetchone()['total_lessons']

        # ✅ جلب عدد الدروس المكتملة للطالب
        cursor.execute("""
            SELECT COUNT(*) AS completed_lessons FROM lesson_progress 
            WHERE student_id = %s AND lesson_id IN (SELECT id FROM lessons WHERE subject_id = %s) 
            AND completed = TRUE
        """, (session['id'], subject_id))
        completed_lessons = cursor.fetchone()['completed_lessons']

        # ✅ حساب نسبة التقدم
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

        # ✅ جلب جميع الدروس الخاصة بهذه المادة
        cursor.execute("SELECT id, title, created_at FROM lessons WHERE subject_id = %s ORDER BY created_at DESC", (subject_id,))
        lessons = cursor.fetchall()  # ✅ تأكد من استخدام fetchall()

        # ✅ جلب الإعلانات الخاصة بالمادة
        cursor.execute("""
            SELECT a.id, a.subject_id, a.teacher_id, a.created_at, a.content, 
                   t.username AS teacher_name
            FROM announcements a
            JOIN accounts t ON a.teacher_id = t.id
            WHERE a.subject_id = %s
            ORDER BY a.created_at DESC
        """, (subject_id,))
        announcements = cursor.fetchall()

        # ✅ جلب الأسئلة المرسلة من الطلاب

        # ✅ جلب الأسئلة المرسلة من الطلاب مع معرف السؤال (id)
        cursor.execute("""
            SELECT student_questions.id, student_questions.question, student_questions.answer, 
                   student_questions.is_visible, student_questions.student_id, accounts.username
            FROM student_questions 
            JOIN accounts ON student_questions.student_id = accounts.id 
            WHERE student_questions.subject_id = %s 
            ORDER BY student_questions.created_at DESC
        """, (subject_id,))
        questions = cursor.fetchall()


        # ✅ جلب الملفات الخاصة بالمادة
        cursor.execute("""
            SELECT id, filename, filetype, uploaded_at 
            FROM subject_files 
            WHERE subject_id = %s 
            ORDER BY uploaded_at DESC
        """, (subject_id,))
        files = cursor.fetchall()

        # ✅ جلب الامتحانات
        cursor.execute("""
            SELECT e.id, e.exam_name, e.description, e.is_visible, e.created_at,
                   COALESCE(es.start_time, NULL) AS start_time, 
                   COALESCE(es.end_time, NULL) AS end_time, 
                   COALESCE(es.exam_duration, 0) AS exam_duration, 
                   COALESCE(es.max_attempts, 1) AS max_attempts
            FROM exams e
            LEFT JOIN exam_settings es ON e.id = es.exam_id
            WHERE e.subject_id = %s
            ORDER BY e.created_at DESC
        """, (subject_id,))
        exams = cursor.fetchall()

        # ✅ جلب جميع الواجبات الخاصة بالمادة مع حالة التسليم
        student_name = session.get('username')  # أو استخدم session.get('id') حسب قاعدة البيانات

        # ✅ جلب جميع الواجبات الخاصة بالمادة مع حالة التسليم
        cursor.execute("""
                 SELECT h.id, h.title, h.description, h.due_date, 
                        s.submitted_at  -- ✅ جلب تاريخ التسليم (إن وجد)
                 FROM homeworks h
                 LEFT JOIN homework_submissions s 
                     ON h.id = s.homework_id AND s.student_name = %s  -- ✅ مطابقة الطالب
                 WHERE h.subject_id = %s
             """, (student_name, subject_id))

        homeworks = cursor.fetchall()

        for hw in homeworks:
            if hw['due_date']:
                if isinstance(hw['due_date'], date) and not isinstance(hw['due_date'], datetime):
                    # ✅ ضبط موعد التسليم ليكون في آخر لحظة من اليوم
                    hw['due_date'] = datetime.combine(hw['due_date'], datetime.max.time())

                hw['due_date_str'] = hw['due_date'].strftime('%Y-%m-%d %H:%M')

                if hw['submitted_at']:
                    submission_time = hw['submitted_at']
                    hw['status'] = "تم التسليم"
                    hw['details'] = f"تم التسليم في {submission_time.strftime('%Y-%m-%d %H:%M')}"
                else:
                    remaining_time = (hw['due_date'] - now).total_seconds() // 60
                    hw['status'] = "لم يتم التسليم"
                    hw[
                        'details'] = f"الوقت المتبقي للتسليم: {remaining_time} دقيقة" if remaining_time > 0 else "انتهت المهلة"

            else:
                hw['due_date_str'] = "غير محدد"
                hw['status'] = "غير معروف"
                hw['details'] = "لم يتم تحديد موعد نهائي لهذا الواجب"
        return render_template('subject_page.html',
                               subject=subject,
                               files=files,
                               exams=exams,
                               homeworks=homeworks,
                               permissions=permissions,
                               announcements=announcements,
                               questions=questions, # ✅ تم تمرير الأسئلة هنا
                               lessons=lessons,
        progress_percentage = progress_percentage)  # ✅ تم تمرير نسبة التقدم

    finally:
        cursor.close()
        connection.close()

# إضافة واجب

@app.route('/add_homework/<int:subject_id>', methods=['GET', 'POST'])
def add_homework(subject_id):
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول!", "danger")
        return redirect(url_for('auth'))

    user_id = session['id']
    role = session['role']

    # السماح للمدرس أو المساعد (لو عنده الصلاحية)
    if role != 'teacher' and not (role == 'assistant' and has_permission(user_id, subject_id, 'can_add_homework')):
        flash("ليس لديك الصلاحية لإضافة الواجب!", "danger")
        return redirect(url_for('subject_page', subject_id=subject_id))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date = request.form.get('due_date', '').strip()  # ✅ التقاط موعد الانتهاء

        # ✅ تحويل `due_date` إلى صيغة `datetime`
        if due_date:
            try:
                due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("تنسيق موعد التسليم غير صحيح!", "danger")
                return redirect(url_for('add_homework', subject_id=subject_id))

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        try:
            # ✅ تعديل استعلام `INSERT` ليشمل `due_date`
            cursor.execute(
                "INSERT INTO homeworks (subject_id, title, description, due_date) VALUES (%s, %s, %s, %s)",
                (subject_id, title, description, due_date)
            )
            connection.commit()
            homework_id = cursor.lastrowid

            # ✅ جلب اسم المادة
            cursor.execute("SELECT name FROM subjects WHERE id = %s", (subject_id,))
            subject = cursor.fetchone()
            subject_name = subject['name']

            # ✅ إرسال إشعار لكل الطلاب المسجلين في المادة
            cursor.execute('SELECT student_id FROM student_subjects WHERE subject_id = %s', (subject_id,))
            students = cursor.fetchall()

            for student in students:
                cursor.execute('''
                    INSERT INTO notifications (user_id, message, notification_type, related_id)
                    VALUES (%s, %s, %s, %s)
                ''', (student['student_id'], f"تم إضافة واجب جديد '{title}' في مادة {subject_name}", 'homework', homework_id))

            connection.commit()

            flash('تم إضافة الواجب بنجاح!', 'success')
            return redirect(url_for('subject_page', subject_id=subject_id))

        finally:
            cursor.close()
            connection.close()

    return render_template('add_homework.html', subject_id=subject_id)




# حذف الواجب
@app.route('/homework/delete/<int:homework_id>', methods=['POST'])
def delete_homework(homework_id):
    # هنا تضع كود الحذف من قاعدة البيانات
    # مثلا:
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM homeworks WHERE id = %s', (homework_id,))
    mysql.connection.commit()
    cursor.close()

    flash('تم حذف الواجب بنجاح!', 'success')
    # بعد الحذف يرجع للصفحة السابقة (صفحة المادة)
    return redirect(request.referrer)

#تفعيل او الغاء تفعيل الواجب
@app.route('/toggle_homework_submission/<int:homework_id>')
def toggle_homework_submission(homework_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # جلب الحالة الحالية
        cursor.execute("SELECT is_submission_open FROM homeworks WHERE id = %s", (homework_id,))
        homework = cursor.fetchone()

        if homework:
            # تأكد من تحويل القيمة بشكل صريح (مهم عشان بعض قواعد البيانات ترجعها None أو Decimal)
            current_status = int(homework['is_submission_open'])

            # عكس القيمة
            new_status = 0 if current_status else 1

            cursor.execute("UPDATE homeworks SET is_submission_open = %s WHERE id = %s", (new_status, homework_id))
            connection.commit()

            flash(f"تم {'تفعيل' if new_status else 'إيقاف'} رفع الواجب", "success")

        return redirect(request.referrer or url_for('subjects'))

    finally:
        cursor.close()
        connection.close()


from datetime import datetime


@app.route('/homework_details/<int:homework_id>')
def homework_details(homework_id):
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول لعرض تفاصيل الواجب!", "danger")
        return redirect(url_for('auth'))

    user_id = session.get('id')
    student_name = session.get('username')

    if not student_name:
        flash("حدث خطأ أثناء جلب بيانات الطالب!", "danger")
        return redirect(url_for('subjects'))

    connection = mysql.connection
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # ✅ جلب تفاصيل الواجب
        cursor.execute("""
            SELECT id, title, description, due_date
            FROM homeworks
            WHERE id = %s
        """, (homework_id,))
        homework = cursor.fetchone()

        if not homework:
            flash("الواجب غير موجود!", "danger")
            return redirect(url_for('subjects'))

        now = datetime.now()

        # ✅ التحقق مما إذا كان الطالب قد سلم الواجب
        cursor.execute("""
            SELECT submitted_at
            FROM homework_submissions
            WHERE student_name = %s AND homework_id = %s
        """, (student_name, homework_id))

        submission = cursor.fetchone()

        if submission:
            # الطالب قد سلم الواجب
            submission_time = submission['submitted_at']  # ✅ تصحيح اسم العمود
            remaining_time = (homework['due_date'] - submission_time).total_seconds() // 60

            status = "تم التسليم"
            details = f"تم التسليم في {submission_time.strftime('%Y-%m-%d %H:%M')}<br> تبقى {remaining_time} دقيقة قبل انتهاء المهلة."
        else:
            # الطالب لم يسلم الواجب
            remaining_time = (homework['due_date'] - now).total_seconds() // 60
            status = "لم يتم التسليم"
            details = f"الوقت المتبقي للتسليم: {remaining_time} دقيقة" if remaining_time > 0 else "انتهت المهلة"

        return render_template('homework_details.html', homework=homework, status=status, details=details)

    finally:
        cursor.close()

@app.route('/homework_submissions/<int:homework_id>', methods=['GET', 'POST'])
def homework_submissions(homework_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    connection = get_db_connection()
    cursor = connection.cursor()
    submissions = []
    error = None

    try:
        # ✅ جلب بيانات الواجب
        cursor.execute("SELECT id, title, subject_id FROM homeworks WHERE id = %s", (homework_id,))
        homework = cursor.fetchone()

        if not homework:
            flash("الواجب غير موجود!", "danger")
            return redirect(url_for('subjects'))

        subject_id = homework['subject_id']

        # ✅ معالجة الطلب من نوع POST (إدخال التقييم والتعليق)
        if request.method == 'POST':
            student_name = request.form.get('student_name')
            grade = request.form.get('grade')
            comment = request.form.get('comment')

            if student_name and grade:
                cursor.execute("""
                    UPDATE homework_submissions 
                    SET grade = %s, comment = %s 
                    WHERE homework_id = %s AND student_name = %s
                """, (grade, comment, homework_id, student_name))

                connection.commit()
                flash("تم حفظ التقييم بنجاح!", "success")
            else:
                flash("يجب إدخال التقييم قبل الحفظ.", "warning")

        # ✅ إذا كان المستخدم طالب، جلب بياناته فقط
        if session['role'] == 'student':
            student_name = session['username']
            cursor.execute("""
                SELECT filename, submitted_at, 
                       COALESCE(grade, 'لم يتم التقييم') AS grade, 
                       COALESCE(comment, 'لا يوجد تعليق') AS comment
                FROM homework_submissions 
                WHERE homework_id = %s AND student_name = %s
            """, (homework_id, student_name))
            student_submission = cursor.fetchone() or {}

            return render_template('student_homework.html',
                                   homework=homework,
                                   subject_id=subject_id,
                                   submission=student_submission)

        # ✅ إذا كان المستخدم معلمًا، جلب جميع التسليمات
        cursor.execute("""
            SELECT student_name, filename, submitted_at, 
                   COALESCE(grade, 'لم يتم التقييم') AS grade, 
                   COALESCE(comment, 'لا يوجد تعليق') AS comment
            FROM homework_submissions 
            WHERE homework_id = %s
            ORDER BY submitted_at DESC
        """, (homework_id,))
        submissions = cursor.fetchall()

    except Exception as e:
        flash(f"حدث خطأ: {str(e)}", "danger")
    finally:
        cursor.close()
        connection.close()

    return render_template('homework_submissions.html',
                           homework=homework,
                           submissions=submissions)


# Folders
PROFILE_PICTURE_FOLDER = 'static/profile_pictures'
HOMEWORK_UPLOAD_FOLDER = 'static/homework_uploads'
SUBJECT_FILES_FOLDER = 'static/uploads'

# Ensure folders exist
os.makedirs(PROFILE_PICTURE_FOLDER, exist_ok=True)
os.makedirs(HOMEWORK_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUBJECT_FILES_FOLDER, exist_ok=True)

# Allowed extensions
PROFILE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
HOMEWORK_ALLOWED_EXTENSIONS = {'pdf', 'docx'}
SUBJECT_ALLOWED_EXTENSIONS = {'pdf', 'mp4', 'avi', 'mov'}

# Function to check allowed file types
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# ============================= Profile Picture Upload =============================

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
    account = cursor.fetchone()

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form.get('password')

        profile_picture = account['profile_picture']

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename, PROFILE_ALLOWED_EXTENSIONS):
                filename = secure_filename(file.filename)
                file_path = os.path.join(PROFILE_PICTURE_FOLDER, filename)
                file.save(file_path)
                profile_picture = filename

        if password:
            hashed_password = generate_password_hash(password)
            cursor.execute('UPDATE accounts SET username = %s, email = %s, password = %s, profile_picture = %s WHERE id = %s',
                           (username, email, hashed_password, profile_picture, session['id']))
        else:
            cursor.execute('UPDATE accounts SET username = %s, email = %s, profile_picture = %s WHERE id = %s',
                           (username, email, profile_picture, session['id']))

        mysql.connection.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('auth/edit_profile.html', account=account)

# ============================= Homework Upload =============================

HOMEWORK_UPLOAD_FOLDER = 'static/homework_uploads'
os.makedirs(HOMEWORK_UPLOAD_FOLDER, exist_ok=True)
HOMEWORK_ALLOWED_EXTENSIONS = {'pdf', 'docx'}

@app.route('/submit_homework/<int:subject_id>/<int:homework_id>', methods=['POST'])
def submit_homework(subject_id, homework_id):
    if 'loggedin' not in session or session.get('role') != 'student':
        flash('Login as student to submit homework', 'danger')
        return redirect(url_for('auth'))

    student_name = session.get('username')
    file = request.files['file']

    if file and allowed_file(file.filename, HOMEWORK_ALLOWED_EXTENSIONS):
        filename = secure_filename(file.filename)
        file_path = f'homework_uploads/{filename}'  # حفظ المسار النسبي فقط
        full_path = os.path.join('static', file_path)  # مسار الحفظ الفعلي
        file.save(full_path)

        # ✅ التحقق من الحفظ
        if os.path.exists(full_path):
            print(f"✅ File successfully saved at: {full_path}")
        else:
            print(f"❌ File NOT found at: {full_path}")
            flash('Error saving file!', 'danger')
            return redirect(url_for('subject_page', subject_id=subject_id))

        # ✅ طباعة القيم
        print(f"📁 Upload Folder: {HOMEWORK_UPLOAD_FOLDER}")
        print(f"📂 Full Path: {full_path}")
        print(f"📄 File Name: {filename}")
        print(f"👤 Student: {student_name}")
        print(f"📅 Upload Date: {datetime.now()}")

        cursor = mysql.connection.cursor()

        try:
            cursor.execute('''
                INSERT INTO homework_submissions (subject_id, homework_id, student_name, filename, file_path, upload_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (subject_id, homework_id, student_name, filename, file_path, datetime.now()))
            mysql.connection.commit()

            # ✅ تحديث تقرير التقدم بعد تسليم الواجب
            from MySQLdb.cursors import DictCursor
            cursor = mysql.connection.cursor(DictCursor)
            cursor.execute("SELECT id FROM accounts WHERE username = %s", (student_name,))
            user_data = cursor.fetchone()
            if user_data:
                update_student_progress(user_data['id'], subject_id)

            flash('Homework submitted successfully!', 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error submitting homework: {str(e)}', 'danger')

        finally:
            cursor.close()

    else:
        flash('Invalid file type for homework!', 'danger')

    return redirect(url_for('subject_page', subject_id=subject_id))

# ============================= Subject File Upload =============================
@app.route('/upload_file/<int:subject_id>', methods=['POST'])
def upload_file(subject_id):
    if 'loggedin' not in session or not is_teacher_or_assistant(subject_id):
        return redirect(url_for('auth'))

    file = request.files['file']
    if not file or file.filename == '':
        flash('No file selected!', 'danger')
        return redirect(url_for('subject_page', subject_id=subject_id))

    if file and allowed_file(file.filename, SUBJECT_ALLOWED_EXTENSIONS):
        filename = secure_filename(file.filename)
        file_path = os.path.join(SUBJECT_FILES_FOLDER, filename)
        file.save(file_path)

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO subject_files (subject_id, filename, filetype) VALUES (%s, %s, %s)',
                       (subject_id, filename, file.filename.rsplit('.', 1)[1].lower()))
        mysql.connection.commit()

        flash('Subject file uploaded successfully!', 'success')

        # جلب اسم المادة
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT name FROM subjects WHERE id = %s", (subject_id,))
        subject = cursor.fetchone()
        subject_name = subject['name']

        # إرسال إشعار لكل الطلاب المسجلين في المادة
        cursor.execute('SELECT student_id FROM student_subjects WHERE subject_id = %s', (subject_id,))
        students = cursor.fetchall()

        for student in students:
            cursor.execute('''
                INSERT INTO notifications (user_id, message, notification_type, related_id)
                VALUES (%s, %s, %s, %s)
            ''', (student['student_id'], f"تم إضافة ملف جديد في مادة {subject_name}", 'subject_file', subject_id))

        mysql.connection.commit()

    else:
        flash('Invalid file type for subject files!', 'danger')

    return redirect(url_for('subject_page', subject_id=subject_id))

# =============================  بنك الاسئلة   =============================

@app.route('/question_bank/<int:subject_id>', methods=['GET', 'POST'])
def question_bank(subject_id):

    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash('يجب تسجيل الدخول كمعلم!', 'danger')
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    teacher_name = session['username']  # التعديل هنا

    try:
        if request.method == 'POST':
            # استخراج البيانات الأساسية
            subject_id = subject_id
            grade = request.form.get('grade')
            question_text = request.form.get('question_text')
            question_type = request.form.get('question_type')

            if not all([subject_id, grade, question_text, question_type]):
                flash('الرجاء ملء جميع الحقول المطلوبة', 'danger')
                return redirect(url_for('question_bank', subject_id=subject_id))

            # معالجة الإجابة الصحيحة
            correct_option = ""
            option_1 = option_2 = option_3 = option_4 = None

            if question_type == 'mcq':
                option_1 = request.form.get('option_1')
                option_2 = request.form.get('option_2')
                option_3 = request.form.get('option_3')
                option_4 = request.form.get('option_4')
                correct_option_index = int(request.form.get('correct_option', 1))
                correct_option = [option_1, option_2, option_3, option_4][correct_option_index - 1]

            elif question_type == 'true_false':
                correct_option = request.form.get('correct_option_tf', 'صح')
                option_1 = "صح"
                option_2 = "خطأ"

            # إدخال البيانات في قاعدة البيانات
            cursor.execute('''
                INSERT INTO question_bank 
                (subject_id, grade, question_text, option_1, option_2, option_3, option_4, 
                correct_option, question_type, teacher)  # التعديل هنا
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                subject_id,
                grade,
                question_text,
                option_1,
                option_2,
                option_3,
                option_4,
                correct_option,
                question_type,
                teacher_name  # التعديل هنا
            ))

            mysql.connection.commit()
            flash('تمت إضافة السؤال بنجاح!', 'success')
            return redirect(url_for('question_bank', subject_id=subject_id))

        # جلب البيانات للعرض
        cursor.execute('''
            SELECT qb.*, s.name AS subject_name 
            FROM question_bank qb
            JOIN subjects s ON qb.subject_id = s.id 
            WHERE qb.subject_id = %s  
            ORDER BY qb.created_at DESC
        ''', (subject_id,))

        questions = cursor.fetchall()

        cursor.execute('SELECT id, name FROM subjects WHERE teacher = %s', (teacher_name,))  # التعديل هنا
        subjects = cursor.fetchall()

        return render_template('question_bank.html', questions=questions, subjects=subjects)

    except Exception as e:
        mysql.connection.rollback()
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('question_bank', subject_id=subject_id))

    finally:
        cursor.close()


@app.route('/delete_question_bank/<int:question_id>', methods=['POST'])
def delete_question_bank(question_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash('يجب تسجيل الدخول كمعلم!', 'danger')
        return redirect(url_for('auth'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # ✅ جلب subject_id قبل الحذف
        cursor.execute("SELECT subject_id FROM question_bank WHERE id = %s", (question_id,))
        result = cursor.fetchone()

        if result:
            subject_id = result['subject_id']  # استخراج subject_id من قاعدة البيانات
        else:
            flash("السؤال غير موجود!", "danger")
            return redirect(url_for('home'))  # إعادة التوجيه للصفحة الرئيسية إذا لم يكن السؤال موجودًا

        # ✅ تنفيذ عملية الحذف
        cursor.execute('''
            DELETE FROM question_bank
            WHERE id = %s AND subject_id IN (SELECT id FROM subjects WHERE teacher = %s)
        ''', (question_id, session['username']))

        if cursor.rowcount == 0:
            flash('لا تملك صلاحية حذف هذا السؤال', 'danger')
        else:
            mysql.connection.commit()
            flash('تم حذف السؤال بنجاح', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')

    finally:
        cursor.close()

    return redirect(url_for('question_bank', subject_id=subject_id))

@app.route('/edit_question_bank/<int:question_id>', methods=['GET', 'POST'])
def edit_question_bank(question_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash('يجب تسجيل الدخول كمعلم!', 'danger')
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # ✅ جلب بيانات السؤال و subject_id
        cursor.execute('''
            SELECT qb.*, s.id AS subject_id, s.name AS subject_name 
            FROM question_bank qb
            JOIN subjects s ON qb.subject_id = s.id
            WHERE qb.id = %s AND s.teacher = %s
        ''', (question_id, session['username']))

        question = cursor.fetchone()

        if not question:
            flash('السؤال غير موجود أو لا تملك صلاحية التعديل', 'danger')
            return redirect(url_for('home'))  # في حال كان السؤال غير موجود

        subject_id = question['subject_id']  # ✅ استخراج subject_id بشكل مضمون

        if request.method == 'POST':
            question_text = request.form['question_text']
            correct_option = request.form['correct_option']

            # ✅ تعديل الإجابة الصحيحة إذا كان السؤال اختيار من متعدد
            if question['question_type'] == 'mcq':
                options = [question['option_1'], question['option_2'], question['option_3'], question['option_4']]
                correct_option_text = options[int(correct_option) - 1]
            else:
                correct_option_text = correct_option  # لو صح أو خطأ

            cursor.execute('''
                UPDATE question_bank 
                SET question_text = %s, correct_option = %s
                WHERE id = %s
            ''', (question_text, correct_option_text, question_id))

            mysql.connection.commit()
            flash('تم تحديث السؤال بنجاح', 'success')
            return redirect(url_for('question_bank', subject_id=subject_id))  # ✅ تمرير subject_id بشكل مضمون

        cursor.execute('SELECT id, name FROM subjects WHERE teacher = %s', (session['username'],))
        subjects = cursor.fetchall()

        return render_template('edit_question_bank.html',
                               question=question,
                               subjects=subjects)

    except Exception as e:
        mysql.connection.rollback()
        flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'danger')
        return redirect(url_for('question_bank', subject_id=subject_id))

    finally:
        cursor.close()


@app.route('/contact')
def contact():
    return render_template('contact.html')


def update_student_progress(user_id, subject_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # حساب عدد الامتحانات التي أكملها الطالب
    cursor.execute("""
        SELECT COUNT(*) AS exams_completed, AVG(score / total_questions * 100) AS average_score 
        FROM student_grades 
        JOIN exams ON student_grades.exam_id = exams.id 
        WHERE student_grades.user_id = %s AND exams.subject_id = %s
    """, (user_id, subject_id))
    exam_data = cursor.fetchone()

    # حساب عدد الواجبات التي أكملها الطالب
    cursor.execute("""
        SELECT COUNT(*) AS assignments_completed 
        FROM homework_submissions 
        WHERE student_name = (SELECT username FROM accounts WHERE id = %s) 
        AND homework_id IN (SELECT id FROM homeworks WHERE subject_id = %s)
    """, (user_id, subject_id))
    assignment_data = cursor.fetchone()

    # تحديث الجدول أو إدخال بيانات جديدة
    cursor.execute("""
        INSERT INTO student_progress (user_id, subject_id, exams_completed, average_score, assignments_completed, last_activity)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE 
            exams_completed = VALUES(exams_completed), 
            average_score = VALUES(average_score), 
            assignments_completed = VALUES(assignments_completed), 
            last_activity = NOW()
    """, (user_id, subject_id, exam_data['exams_completed'], exam_data['average_score'] or 0, assignment_data['assignments_completed'] or 0))

    mysql.connection.commit()
    cursor.close()


@app.route('/student_comparison')
def student_comparison():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ جلب معدل الطالب
    cursor.execute("""
        SELECT AVG(average_score) AS student_avg 
        FROM student_progress 
        WHERE user_id = %s
    """, (session['id'],))
    student_data = cursor.fetchone()

    # ✅ جلب متوسط الفصل بالكامل
    cursor.execute("""
        SELECT AVG(average_score) AS class_avg 
        FROM student_progress
    """)
    class_data = cursor.fetchone()

    return jsonify({
        "student_avg": student_data["student_avg"],
        "class_avg": class_data["class_avg"]
    })


@app.route('/student_progress')
def student_progress():
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT s.name AS subject_name, sp.exams_completed, sp.average_score, sp.assignments_completed, sp.last_activity
        FROM student_progress sp
        JOIN subjects s ON sp.subject_id = s.id
        WHERE sp.user_id = %s
    """, (session['id'],))
    progress_data = cursor.fetchall()

    return render_template('student_progress.html', progress_data=progress_data)

@app.route('/teacher_progress/<int:subject_id>')
def teacher_progress(subject_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT a.username, sp.exams_completed, sp.average_score, sp.assignments_completed, sp.last_activity
        FROM student_progress sp
        JOIN accounts a ON sp.user_id = a.id
        WHERE sp.subject_id = %s
        ORDER BY sp.average_score DESC
    """, (subject_id,))
    students_progress = cursor.fetchall()

    return render_template('teacher_progress.html', students_progress=students_progress, subject_id=subject_id)



@app.route('/filter_students', methods=['GET'])
def filter_students():
    performance = request.args.get('performance', 'all')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if performance == "high":
        cursor.execute("SELECT * FROM student_progress WHERE average_score >= 85 ORDER BY average_score DESC")
    elif performance == "low":
        cursor.execute("SELECT * FROM student_progress WHERE average_score < 50 ORDER BY average_score ASC")
    else:
        cursor.execute("SELECT * FROM student_progress ORDER BY average_score DESC")

    students = cursor.fetchall()
    conn.close()

    return jsonify(students)


@app.route('/delete_file/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول!", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT subject_id, filename FROM subject_files WHERE id = %s", (file_id,))
    file = cursor.fetchone()

    if not file:
        flash("الملف غير موجود!", "danger")
        return redirect(url_for('subjects'))

    subject_id = file['subject_id']

    # التحقق من الصلاحيات (المعلم أو المساعد المخصص للمادة)
    if not is_teacher_or_assistant(subject_id):
        flash("ليس لديك الصلاحية لحذف الملفات!", "danger")
        return redirect(url_for('subjects'))

    # حذف الملف من السيرفر
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file['filename'])
    if os.path.exists(file_path):
        os.remove(file_path)

    cursor.execute("DELETE FROM subject_files WHERE id = %s", (file_id,))
    mysql.connection.commit()
    cursor.close()

    flash("تم حذف الملف بنجاح!", "success")
    return redirect(url_for('subject_page', subject_id=subject_id))


@app.route('/manage_assistants/<int:subject_id>', methods=['GET', 'POST'])
def manage_assistants(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب قائمة المستخدمين الذين يمكن تعيينهم مساعدين (المستخدمين اللي دورهم "assistant")
    cursor.execute("""
        SELECT id, username FROM accounts WHERE role = 'assistant'
    """)

    users = cursor.fetchall()

    # جلب المساعدين الحاليين للمادة
    cursor.execute("""
        SELECT a.id, a.username FROM accounts a
        JOIN assistants ass ON a.id = ass.assistant_id
        WHERE ass.subject_id = %s
    """, (subject_id,))
    assistants = cursor.fetchall()

    cursor.close()

    return render_template('manage_assistants.html', users=users, assistants=assistants, subject_id=subject_id)


@app.route('/assign_assistant', methods=['POST'])
def assign_assistant():
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    teacher_id = session['id']
    assistant_id = request.form.get('assistant_id')
    subject_id = request.form.get('subject_id')

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO assistants (teacher_id, assistant_id, subject_id) VALUES (%s, %s, %s)",
                   (teacher_id, assistant_id, subject_id))
    mysql.connection.commit()
    cursor.close()

    flash("تم تعيين المساعد بنجاح!", "success")
    return redirect(url_for('subject_page', subject_id=subject_id))


@app.route('/remove_assistant/<int:assistant_id>/<int:subject_id>', methods=['POST'])
def remove_assistant(assistant_id, subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM assistants WHERE assistant_id = %s AND subject_id = %s", (assistant_id, subject_id))
    mysql.connection.commit()
    cursor.close()

    flash("تم إزالة المساعد بنجاح!", "success")
    return redirect(url_for('manage_assistants', subject_id=subject_id))


@app.route('/manage_assistant_permissions/<int:assistant_id>/<int:subject_id>', methods=['GET', 'POST'])
def manage_assistant_permissions(assistant_id, subject_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب الصلاحيات الحالية للمساعد
    cursor.execute("""
        SELECT * FROM assistant_permissions 
        WHERE assistant_id = %s AND subject_id = %s
    """, (assistant_id, subject_id))
    permissions = cursor.fetchone()

    # لو مفيش صلاحيات محفوظة، نضيفها بالقيم الافتراضية
    if not permissions:
        cursor.execute("""
            INSERT INTO assistant_permissions (assistant_id, subject_id) 
            VALUES (%s, %s)
        """, (assistant_id, subject_id))
        mysql.connection.commit()
        cursor.execute("""
            SELECT * FROM assistant_permissions 
            WHERE assistant_id = %s AND subject_id = %s
        """, (assistant_id, subject_id))
        permissions = cursor.fetchone()

    cursor.close()

    return render_template('manage_assistant_permissions.html', permissions=permissions, assistant_id=assistant_id, subject_id=subject_id)


@app.route('/update_assistant_permissions/<int:assistant_id>/<int:subject_id>', methods=['POST'])
def update_assistant_permissions(assistant_id, subject_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    permissions = {
        'can_add_homework': 'can_add_homework' in request.form,
        'can_view_submissions': 'can_view_submissions' in request.form,
        'can_view_progress': 'can_view_progress' in request.form,
        'can_manage_students': 'can_manage_students' in request.form,
        'can_edit_exams': 'can_edit_exams' in request.form,
        'can_add_exam': 'can_add_exam' in request.form,
        'can_upload_files': 'can_upload_files' in request.form
    }

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE assistant_permissions 
        SET can_add_homework = %s, can_view_submissions = %s, can_view_progress = %s, 
            can_manage_students = %s, can_edit_exams = %s, can_add_exam = %s, 
            can_upload_files = %s
        WHERE assistant_id = %s AND subject_id = %s
    """, (*permissions.values(), assistant_id, subject_id))

    mysql.connection.commit()
    cursor.close()

    flash("تم تحديث الصلاحيات بنجاح!", "success")
    return redirect(url_for('manage_assistant_permissions', assistant_id=assistant_id, subject_id=subject_id))


def has_permission(user_id, subject_id, permission):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # عشان يرجّع النتائج في شكل Dict
    cursor.execute(f"""
        SELECT {permission} FROM assistant_permissions 
        WHERE assistant_id = %s AND subject_id = %s
    """, (user_id, subject_id))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result and result[permission]  # يرجّع True لو عنده الصلاحية، وإلا False



# إضافة المسارات الخاصة بالتواصل في main.py
@app.route('/subject/<int:subject_id>/add_announcement', methods=['POST'])
def add_announcement(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("فقط المعلم يمكنه نشر الموجز!", "danger")
        return redirect(url_for('subject_page', subject_id=subject_id))

    content = request.form['content']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO announcements (subject_id, teacher_id, content) VALUES (%s, %s, %s)",
                   (subject_id, session['id'], content))
    mysql.connection.commit()
    cursor.close()

    flash("تم نشر المنشور بنجاح!", "success")
    return redirect(url_for('subject_page', subject_id=subject_id))


@app.route('/subject/<int:subject_id>/ask_question', methods=['POST'])
def ask_question(subject_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    question = request.form['question']
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO student_questions (subject_id, student_id, question, is_visible) VALUES (%s, %s, %s, %s)",
        (subject_id, session['id'], question, False))
    mysql.connection.commit()
    cursor.close()

    flash("تم إرسال سؤالك إلى المعلم!", "success")
    return redirect(url_for('subject_page', subject_id=subject_id))


@app.route('/question/<int:question_id>/answer', methods=['POST'])
def answer_question(question_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("فقط المعلم يمكنه الرد على الأسئلة!", "danger")
        return redirect(request.referrer)

    answer = request.form['answer']
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE student_questions SET answer = %s WHERE id = %s", (answer, question_id))
    mysql.connection.commit()
    cursor.close()

    flash("تم الرد على السؤال بنجاح!", "success")
    return redirect(request.referrer)


@app.route('/question/<int:question_id>/toggle_visibility', methods=['POST'])
def toggle_question_visibility(question_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("فقط المعلم يمكنه تغيير رؤية الأسئلة!", "danger")
        return redirect(request.referrer)

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT is_visible FROM student_questions WHERE id = %s", (question_id,))
    question = cursor.fetchone()

    new_visibility = not question[0]
    cursor.execute("UPDATE student_questions SET is_visible = %s WHERE id = %s", (new_visibility, question_id))
    mysql.connection.commit()
    cursor.close()

    flash("تم تحديث رؤية السؤال!", "success")
    return redirect(request.referrer)


@app.route('/subject/<int:subject_id>/send_chat_message', methods=['POST'])
def send_chat_message(subject_id):
    if 'loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'يجب تسجيل الدخول'}), 403

    message = request.form['message']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO chat_messages (subject_id, user_id, message) VALUES (%s, %s, %s)",
                   (subject_id, session['id'], message))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'status': 'success'})


@app.route('/subject/<int:subject_id>/get_chat_messages')
def get_chat_messages(subject_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT accounts.username, chat_messages.message, chat_messages.created_at 
        FROM chat_messages 
        JOIN accounts ON chat_messages.user_id = accounts.id 
        WHERE chat_messages.subject_id = %s 
        ORDER BY chat_messages.created_at ASC
    """, (subject_id,))
    messages = cursor.fetchall()
    cursor.close()
    return jsonify(messages)


def get_chat_messages(subject_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT accounts.username, chat_messages.message FROM chat_messages JOIN accounts ON chat_messages.user_id = accounts.id WHERE chat_messages.subject_id = %s ORDER BY chat_messages.created_at ASC",
        (subject_id,))
    messages = cursor.fetchall()
    cursor.close()

    return jsonify(messages)



@app.route('/exam_report/<int:exam_id>')
def exam_report(exam_id):
    if 'loggedin' not in session or session['role'] != 'teacher':
        flash("يجب تسجيل الدخول كمدرس!", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    print(f"Exam ID received: {exam_id}")

    # جلب بيانات الامتحان
    cursor.execute("""
        SELECT e.exam_name, e.subject_id, es.start_time, es.end_time, es.exam_duration
        FROM exams e
        LEFT JOIN exam_settings es ON e.id = es.exam_id
        WHERE e.id = %s
    """, (exam_id,))
    exam = cursor.fetchone()

    print(f"Exam data: {exam}")

    if not exam:
        flash("الامتحان غير موجود!", "danger")
        return redirect(url_for('subjects'))

    # جلب تفاصيل الطلاب الذين أجروا الامتحان
    cursor.execute("""
        SELECT a.username, 
               IFNULL(sg.score, 0) AS score, 
               IFNULL(sg.total_questions, 0) AS total_questions, 
               IFNULL(DATE_FORMAT(sg.grade_date, '%%Y-%%m-%%d'), 'لم يتم التصحيح بعد') AS grade_date, 
               IFNULL(sg.start_time, 'غير متوفر') AS start_time, 
               IFNULL(sg.end_time, 'غير متوفر') AS end_time,
               IFNULL(TIMESTAMPDIFF(MINUTE, sg.start_time, sg.end_time), 0) AS duration
        FROM student_grades sg
        JOIN accounts a ON sg.user_id = a.id
        WHERE sg.exam_id = %s
        ORDER BY sg.grade_date DESC
    """, (exam_id,))
    students = cursor.fetchall()

    print(f"Students: {students}")

    # تحليل أداء كل سؤال
    cursor.execute("""
        SELECT q.id, q.question_text,
            COUNT(a.user_id) AS total_answers,
            SUM(CASE WHEN a.is_correct THEN 1 ELSE 0 END) AS correct_answers,
            SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) AS wrong_answers,
            IFNULL(ROUND(SUM(CASE WHEN a.is_correct THEN 1 ELSE 0 END) / NULLIF(COUNT(a.user_id), 0) * 100, 2), 0) AS accuracy_percentage
        FROM exam_questions eq
        JOIN questions q ON eq.question_id = q.id
        LEFT JOIN answers a ON q.id = a.question_id
        WHERE eq.exam_id = %s
        GROUP BY q.id, q.question_text
    """, (exam_id,))
    questions_analysis = cursor.fetchall()

    print(f"Questions Analysis: {questions_analysis}")

    cursor.close()

    return render_template('exam_report.html', exam=exam, exam_id=exam_id, students=students, questions_analysis=questions_analysis)



@app.route('/start_exam/<int:exam_id>', methods=['GET', 'POST'])
def start_exam(exam_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth'))

    user_id = session['id']
    cursor = mysql.connection.cursor()

    # تسجيل وقت بدء الامتحان
    cursor.execute("""
        INSERT INTO student_grades (user_id, exam_id, start_time) 
        VALUES (%s, %s, NOW())
        ON DUPLICATE KEY UPDATE start_time = NOW();
    """, (user_id, exam_id))

    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('take_exam', exam_id=exam_id))


@app.route('/detailed_report/<int:exam_id>')
def detailed_report(exam_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ جلب الطلاب الذين قاموا بحل هذا الامتحان
    cursor.execute("""
   SELECT DISTINCT a.id, a.username 
FROM accounts a 
JOIN answers sa ON a.id = sa.user_id 
JOIN exam_questions eq ON sa.question_id = eq.question_id 
WHERE eq.exam_id = %s;


    """, (exam_id,))

    students = cursor.fetchall()
    cursor.close()

    return render_template('detailed_report.html', students=students, exam_id=exam_id)


@app.route('/student_report/<int:exam_id>', methods=['POST'])
def show_student_report(exam_id):
    student_id = request.form.get('student_id')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ جلب بيانات الطالب
    cursor.execute("SELECT username FROM accounts WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    # ✅ جلب إجابات الطالب وتحليلها لهذا الامتحان فقط
    cursor.execute("""
        SELECT q.question_text, q.correct_answer, sa.user_answer, 
               (sa.user_answer = q.correct_answer) AS is_correct
        FROM answers sa
        JOIN questions q ON sa.question_id = q.id
        JOIN exam_questions eq ON q.id = eq.question_id  -- الربط الصحيح مع جدول الامتحان
        WHERE sa.user_id = %s AND eq.exam_id = %s
    """, (student_id, exam_id))

    answers = cursor.fetchall()

    total_questions = len(answers)
    correct_answers = sum(1 for a in answers if a['is_correct'])
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    cursor.close()
    return render_template('student_report.html', student=student, answers=answers,
                           student_score=correct_answers, total_questions=total_questions,
                           percentage=percentage, exam_id=exam_id)



@app.route('/suggest', methods=['GET', 'POST'])
def suggest():
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول لإرسال اقتراح!", "danger")
        return redirect(url_for('auth'))

    if request.method == 'POST':
        suggestion = request.form['suggestion']

        if not suggestion.strip():
            flash("لا يمكن إرسال اقتراح فارغ!", "danger")
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO suggestions (user_id, suggestion) VALUES (%s, %s)", (session['id'], suggestion))
            mysql.connection.commit()
            cursor.close()
            flash("تم إرسال اقتراحك بنجاح!", "success")

    return render_template('suggest.html')



@app.route('/admin/suggestions')
def view_suggestions():
    if 'loggedin' not in session or session.get('role') != 'admin':
        flash("ليس لديك الصلاحية للوصول لهذه الصفحة!", "danger")
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT suggestions.id, suggestions.suggestion, suggestions.created_at, accounts.username 
        FROM suggestions
        JOIN accounts ON suggestions.user_id = accounts.id
        ORDER BY suggestions.created_at DESC
    """)
    suggestions = cursor.fetchall()
    cursor.close()

    return render_template('view_suggestions.html', suggestions=suggestions)




@app.route('/toggle_evaluation/<int:subject_id>', methods=['POST'])
def toggle_evaluation(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT evaluation_status FROM subjects WHERE id = %s", (subject_id,))
    status = cursor.fetchone()[0]

    new_status = not status
    cursor.execute("UPDATE subjects SET evaluation_status = %s WHERE id = %s", (new_status, subject_id))
    mysql.connection.commit()
    cursor.close()

    flash("تم تحديث حالة التقييم!", "success")
    return redirect(url_for('subjects'))


@app.route('/add_evaluation_question/<int:subject_id>', methods=['GET', 'POST'])
def add_evaluation_question(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # 🔹 جلب بيانات المادة
    cursor.execute("SELECT * FROM subjects WHERE id = %s", (subject_id,))
    subject = cursor.fetchone()

    if not subject:
        flash("المادة غير موجودة!", "danger")
        return redirect(url_for('subjects'))

    if request.method == 'POST':
        question_text = request.form['question_text']
        question_type = request.form['question_type']

        cursor.execute("INSERT INTO evaluation_questions (subject_id, question_text, question_type) VALUES (%s, %s, %s)",
                       (subject_id, question_text, question_type))
        mysql.connection.commit()
        flash("تمت إضافة السؤال بنجاح!", "success")

    # 🔹 جلب جميع الأسئلة الخاصة بالمادة
    cursor.execute("SELECT * FROM evaluation_questions WHERE subject_id = %s", (subject_id,))
    questions = cursor.fetchall()
    cursor.close()

    return render_template('add_evaluation_question.html', subject=subject, questions=questions)


@app.route('/evaluate_subject/<int:subject_id>', methods=['GET', 'POST'])
def evaluate_subject(subject_id):
    if 'loggedin' not in session or session.get('role') != 'student':
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # التحقق من أن التقييم مفعّل
    cursor.execute("SELECT evaluation_status FROM subjects WHERE id = %s", (subject_id,))
    status = cursor.fetchone()

    if not status or not status['evaluation_status']:
        flash("التقييم غير متاح حاليًا!", "warning")
        return redirect(url_for('subjects'))

    # جلب أسئلة التقييم
    cursor.execute("SELECT * FROM evaluation_questions WHERE subject_id = %s", (subject_id,))
    questions = cursor.fetchall()

    if request.method == 'POST':
        for question in questions:
            answer = request.form.get(f"q{question['id']}")
            cursor.execute(
                "INSERT INTO evaluation_answers (student_id, subject_id, question_id, answer) VALUES (%s, %s, %s, %s)",
                (session['id'], subject_id, question['id'], answer))

        mysql.connection.commit()
        flash("تم تقديم التقييم بنجاح!", "success")
        return redirect(url_for('subjects'))

    return render_template('evaluate_subject.html', questions=questions, subject_id=subject_id)


@app.route('/view_evaluations/<int:subject_id>')
def view_evaluations(subject_id):
    if 'loggedin' not in session or session.get('role') not in ['teacher', 'admin']:
        flash("ليس لديك الصلاحية!", "danger")
        return redirect(url_for('subjects'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب أسئلة التقييم
    cursor.execute("SELECT * FROM evaluation_questions WHERE subject_id = %s", (subject_id,))
    questions = cursor.fetchall()

    # جلب إجابات التقييم
    cursor.execute("""
        SELECT ea.question_id, ea.answer, a.username 
        FROM evaluation_answers ea
        JOIN accounts a ON ea.student_id = a.id
        WHERE ea.subject_id = %s
    """, (subject_id,))
    answers = cursor.fetchall()

    cursor.close()

    # تنظيم البيانات
    evaluations = {}
    for question in questions:
        evaluations[question['id']] = {
            'question_text': question['question_text'],
            'type': question['question_type'],
            'responses': []
        }

    for answer in answers:
        evaluations[answer['question_id']]['responses'].append({
            'answer': answer['answer'],
            'student': answer['username']
        })

    return render_template('view_evaluations.html', evaluations=evaluations, subject_id=subject_id)





import json

@app.route('/add_lesson/<int:subject_id>', methods=['GET', 'POST'])
def add_lesson(subject_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية لإضافة الدروس!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        video_url = request.form.get('video_url', '')  # رابط الفيديو اختياري

        # تجميع الأسئلة من الفورم وتحويلها إلى JSON
        questions = []
        num_questions = int(request.form['num_questions'])

        for i in range(num_questions):
            q_text = request.form.get(f'question_{i}')
            q_type = request.form.get(f'type_{i}')
            correct_answer = request.form.get(f'correct_{i}')
            feedback = request.form.get(f'feedback_{i}', '')  # ✅ حفظ التغذية الراجعة

            question_data = {
                "question": q_text,
                "type": q_type,
                "correct_answer": correct_answer,
                "feedback": feedback  # ✅ إضافة التغذية الراجعة
            }

            # إذا كان السؤال اختيار من متعدد، نجمع الخيارات
            if q_type == "mcq":
                options = [
                    request.form.get(f'option_{i}_1'),
                    request.form.get(f'option_{i}_2'),
                    request.form.get(f'option_{i}_3'),
                    request.form.get(f'option_{i}_4')
                ]
                question_data["options"] = [opt for opt in options if opt]  # تجاهل القيم الفارغة

            questions.append(question_data)

        # تحويل الأسئلة إلى JSON
        quiz_json = json.dumps(questions)

        cursor = mysql.connection.cursor()
        cursor.execute(''' 
            INSERT INTO lessons (title, content, video_url, quiz, subject_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', (title, content, video_url, quiz_json, subject_id))
        mysql.connection.commit()
        cursor.close()

        flash("تمت إضافة الدرس بنجاح مع الأسئلة!", "success")
        return redirect(url_for('subject_page', subject_id=subject_id))

    return render_template('add_lesson.html')




@app.route('/lessons/<int:subject_id>')
def lessons(subject_id):
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول!", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM lessons WHERE subject_id = %s ORDER BY created_at DESC", (subject_id,))
    lessons = cursor.fetchall()
    cursor.close()

    return render_template('lessons.html', lessons=lessons)



@app.route('/lesson/<int:lesson_id>')
def lesson_details(lesson_id):
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول!", "danger")
        return redirect(url_for('auth'))

    user_id = session['id']  # الحصول على ID الطالب

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب معلومات الدرس
    cursor.execute("SELECT * FROM lessons WHERE id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash("الدرس غير موجود!", "danger")
        return redirect(url_for('lessons'))

    # تحويل `quiz` من JSON إلى قائمة Python
    quiz_data = json.loads(lesson['quiz']) if lesson['quiz'] else []
    # التحقق مما إذا كان الطالب قد بدأ هذا الدرس من قبل
    cursor.execute("SELECT * FROM lesson_progress WHERE student_id = %s AND lesson_id = %s", (user_id, lesson_id))
    progress = cursor.fetchone()

    if not progress:
        # إدراج سجل جديد للطالب عند بداية الدرس
        cursor.execute("INSERT INTO lesson_progress (student_id, lesson_id, progress) VALUES (%s, %s, %s)",
                       (user_id, lesson_id, 10))  # يبدأ بنسبة 10% عند فتح الدرس
        mysql.connection.commit()

    cursor.close()

    return render_template('lesson_details.html', lesson=lesson, quiz_data=quiz_data, enumerate=enumerate)


import json

from flask import render_template, redirect, url_for

@app.route('/update_progress/<int:lesson_id>', methods=['POST'])
def update_progress(lesson_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))  # إعادة توجيه إلى تسجيل الدخول إذا لم يكن الطالب مسجلًا

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # الحصول على بيانات الدرس
    cursor.execute("SELECT * FROM lessons WHERE id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        return "الدرس غير موجود!", 404

    # استخراج بيانات الكويز
    quiz_data = json.loads(lesson['quiz']) if lesson['quiz'] else []
    total_questions = len(quiz_data)
    correct_answers = 0
    feedback = []

    # حساب الإجابات الصحيحة وإضافة التغذية الراجعة
    for index, question in enumerate(quiz_data):
        user_answer = request.form.get(f'q{index + 1}')

        if user_answer:
            if question["type"] == "mcq" and user_answer == question["correct_answer"]:
                correct_answers += 1
            elif question["type"] == "true_false" and user_answer == question["correct_answer"]:
                correct_answers += 1
            elif question["type"] == "short_answer" and user_answer.strip().lower() == question["correct_answer"].strip().lower():
                correct_answers += 1
            else:
                feedback.append({"question": question["question"], "feedback": question.get("feedback", "لا توجد تغذية راجعة لهذا السؤال.")})

    # حساب التقدم
    progress = 10 + ((correct_answers / total_questions) * 90)

    # تحديث التقدم في قاعدة البيانات
    cursor.execute("UPDATE lesson_progress SET progress = %s WHERE student_id = %s AND lesson_id = %s",
                   (progress, user_id, lesson_id))
    mysql.connection.commit()
    cursor.close()

    # **🔄 إعادة التوجيه إلى صفحة التغذية الراجعة**
    return render_template('feedback.html', feedback=feedback, lesson_id=lesson_id)


@app.route('/teacher_dashboards')
def teacher_dashboards():
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("ليس لديك الصلاحية لرؤية هذه الصفحة!", "danger")
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT lp.student_id, a.username, lp.lesson_id, l.title, lp.progress, lp.completed 
        FROM lesson_progress lp
        JOIN accounts a ON lp.student_id = a.id
        JOIN lessons l ON lp.lesson_id = l.id
        ORDER BY lp.last_updated DESC
    """)
    progress_data = cursor.fetchall()
    cursor.close()

    return render_template('teacher_dashboards.html', progress_data=progress_data)


@app.route('/lesson/delete/<int:lesson_id>', methods=['POST'])
def delete_lesson(lesson_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("يجب أن تكون معلماً لتنفيذ هذا الإجراء!", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # 🛑 حذف تقدم الطلاب المرتبط بالدرس أولًا
        cursor.execute("DELETE FROM lesson_progress WHERE lesson_id = %s", (lesson_id,))

        # ✅ حذف الدرس بعد حذف التقدم المرتبط به
        cursor.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))

        mysql.connection.commit()
        flash("تم حذف الدرس بنجاح!", "success")

    except MySQLdb.IntegrityError as e:
        mysql.connection.rollback()
        flash("حدث خطأ أثناء الحذف: " + str(e), "danger")

    cursor.close()
    return redirect(request.referrer or url_for('lessons'))


@app.route('/lesson/edit/<int:lesson_id>', methods=['GET', 'POST'])
def edit_lesson(lesson_id):
    if 'loggedin' not in session or session.get('role') != 'teacher':
        flash("يجب أن تكون معلماً لتنفيذ هذا الإجراء!", "danger")
        return redirect(url_for('auth'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # ✅ جلب بيانات الدرس الحالي
    cursor.execute("SELECT * FROM lessons WHERE id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash("الدرس غير موجود!", "danger")
        return redirect(url_for('lessons'))

    # ✅ تحويل `quiz` من JSON إلى قائمة أسئلة
    quiz_data = json.loads(lesson['quiz']) if lesson['quiz'] else []

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        video_url = request.form.get('video_url', '')

        # ✅ تجميع الأسئلة الجديدة من النموذج
        updated_questions = []
        num_questions = int(request.form['num_questions'])

        for i in range(num_questions):
            q_text = request.form.get(f'question_{i}')
            q_type = request.form.get(f'type_{i}')
            correct_answer = request.form.get(f'correct_{i}')
            feedback = request.form.get(f'feedback_{i}', '')

            question_data = {
                "question": q_text,
                "type": q_type,
                "correct_answer": correct_answer,
                "feedback": feedback
            }

            # ✅ إذا كان السؤال اختيار من متعدد، نحفظ الخيارات
            if q_type == "mcq":
                options = [
                    request.form.get(f'option_{i}_1'),
                    request.form.get(f'option_{i}_2'),
                    request.form.get(f'option_{i}_3'),
                    request.form.get(f'option_{i}_4')
                ]
                question_data["options"] = [opt for opt in options if opt]

            updated_questions.append(question_data)

        # ✅ تحويل الأسئلة الجديدة إلى JSON
        quiz_json = json.dumps(updated_questions)

        # ✅ تحديث بيانات الدرس في قاعدة البيانات
        cursor.execute("UPDATE lessons SET title = %s, content = %s, video_url = %s, quiz = %s WHERE id = %s",
                       (title, content, video_url, quiz_json, lesson_id))
        mysql.connection.commit()
        cursor.close()

        flash("تم تحديث الدرس والأسئلة بنجاح!", "success")
        return redirect(url_for('lesson_details', lesson_id=lesson_id))

    cursor.close()
    return render_template('edit_lesson.html', lesson=lesson, quiz_data=quiz_data , enumerate=enumerate)


@app.route('/lesson_progress_report/<int:lesson_id>')
def lesson_progress_report(lesson_id):
    if 'loggedin' not in session:
        flash("يجب تسجيل الدخول!", "danger")
        return redirect(url_for('auth'))

    user_id = session['id']
    user_role = session['role']  # التحقق من دور المستخدم (طالب / معلم)
    username = session['username']  # اسم المستخدم الحالي

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب معلومات الدرس
    cursor.execute("SELECT * FROM lessons WHERE id = %s", (lesson_id,))
    lesson = cursor.fetchone()

    if not lesson:
        flash("الدرس غير موجود!", "danger")
        return redirect(url_for('lessons'))

    # استعلام مختلف حسب دور المستخدم
    if user_role == 'teacher':
        # المعلم يرى جميع الطلاب
        cursor.execute("""
            SELECT a.username, lp.progress, lp.completed, lp.last_updated
            FROM lesson_progress lp
            JOIN accounts a ON lp.student_id = a.id
            WHERE lp.lesson_id = %s
            ORDER BY lp.last_updated DESC
        """, (lesson_id,))
    else:
        # الطالب يرى تقريره فقط
        cursor.execute("""
            SELECT a.username, lp.progress, lp.completed, lp.last_updated
            FROM lesson_progress lp
            JOIN accounts a ON lp.student_id = a.id
            WHERE lp.lesson_id = %s AND a.username = %s
        """, (lesson_id, username))

    progress_data = cursor.fetchall()
    cursor.close()

    return render_template('lesson_progress_report.html', lesson=lesson, progress_data=progress_data)


@app.route('/generate_report/<int:subject_id>')
def generate_report(subject_id):
    if 'loggedin' not in session or session.get('role') not in ['teacher', 'admin']:
        flash("ليس لديك الصلاحيات للوصول إلى هذا التقرير!", "danger")
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # جلب عدد الطلاب المسجلين في المادة
    cursor.execute('''
        SELECT COUNT(DISTINCT a.id) AS total_students
        FROM accounts a
        JOIN student_grades sg ON sg.user_id = a.id
        JOIN exams e ON sg.exam_id = e.id
        WHERE e.subject_id = %s
    ''', (subject_id,))
    total_students = cursor.fetchone()['total_students']

    # جلب عدد الامتحانات الكلية للمادة
    cursor.execute('SELECT COUNT(*) AS total_exams FROM exams WHERE subject_id = %s', (subject_id,))
    total_exams = cursor.fetchone()['total_exams']

    # جلب درجات الطلاب في الامتحانات
    cursor.execute('''
        SELECT a.id AS student_id, a.username, sg.score, sg.total_questions
        FROM student_grades sg
        JOIN accounts a ON sg.user_id = a.id
        JOIN exams e ON sg.exam_id = e.id
        WHERE e.subject_id = %s
    ''', (subject_id,))
    exam_grades = cursor.fetchall()

    # جلب عدد الواجبات الكلية للمادة
    cursor.execute('SELECT COUNT(*) AS total_homeworks FROM homeworks WHERE subject_id = %s', (subject_id,))
    total_homeworks = cursor.fetchone()['total_homeworks']

    # جلب درجات الطلاب في الواجبات
    cursor.execute('''
        SELECT a.id AS student_id, a.username, hs.grade AS homework_score
        FROM homework_submissions hs
        JOIN accounts a ON TRIM(LOWER(hs.student_name)) = TRIM(LOWER(a.username))
        JOIN homeworks h ON hs.homework_id = h.id
        WHERE h.subject_id = %s
    ''', (subject_id,))
    homework_grades = cursor.fetchall()

    cursor.close()

    # إنشاء تقرير الطلاب
    student_reports = {}
    total_percentage = 0  # لحساب متوسط النسبة العامة

    for row in exam_grades:
        student_id = row['student_id']
        if student_id not in student_reports:
            student_reports[student_id] = {
                'student_name': row['username'],
                'exam_count': 0, 'total_exam_percentage': 0,
                'homework_count': 0, 'total_homework_percentage': 0
            }
        percentage = (row['score'] / row['total_questions']) * 100 if row['total_questions'] > 0 else 0
        student_reports[student_id]['total_exam_percentage'] += percentage
        student_reports[student_id]['exam_count'] += 1

    for row in homework_grades:
        student_id = row['student_id']
        if student_id not in student_reports:
            student_reports[student_id] = {
                'student_name': row['username'],
                'exam_count': 0, 'total_exam_percentage': 0,
                'homework_count': 0, 'total_homework_percentage': 0
            }
        percentage = ((row.get('homework_score', 0) or 0) / 10) * 100
        student_reports[student_id]['total_homework_percentage'] += percentage
        student_reports[student_id]['homework_count'] += 1

    for student_id, data in student_reports.items():
        final_exam_percentage = (
                    (data.get('total_exam_percentage', 0) or 0) / (total_exams or 1)) if total_exams > 0 else 0
        final_homework_percentage = ((data.get('total_homework_percentage', 0) or 0) / (
                    total_homeworks or 1)) if total_homeworks > 0 else 0
        final_grade = (final_exam_percentage * 0.5) + (final_homework_percentage * 0.5)

        student_reports[student_id]['final_exam_percentage'] = round(final_exam_percentage, 2)
        student_reports[student_id]['final_homework_percentage'] = round(final_homework_percentage, 2)
        student_reports[student_id]['final_grade'] = round(final_grade, 2)
        total_percentage += final_grade

    # حساب متوسط النسبة العامة
    average_percentage = round(total_percentage / total_students, 2) if total_students > 0 else 0

    return render_template('report.html', student_reports=student_reports,
                           total_exams=total_exams, total_homeworks=total_homeworks,
                           total_students=total_students, average_percentage=average_percentage,
                           title="تقرير الأداء الطلابي للمادة")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

