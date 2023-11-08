from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/students'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
db = SQLAlchemy(app)

# 定义学生信息表
class StudentInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    birthday = db.Column(db.Date)
    placeofbirth = db.Column(db.String(255))
    college = db.Column(db.String(255))
    major = db.Column(db.String(255))
    gender = db.Column(db.String(10))

# 定义课程信息表
class LessonInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    teacher = db.Column(db.String(255))
    major = db.Column(db.String(255))
    grade = db.Column(db.String(10))

# 定义学生选课关系表
class StudentLesson(db.Model):
    __tablename__ = 'studentlesson'  # 指定表名
    student_id = db.Column(db.Integer, db.ForeignKey('student_info.id'), primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson_info.id'), primary_key=True)
# 定义管理员账号密码表
class Manager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))

# 定义学生账号密码表
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))

@app.route('/', methods=['GET'])
def root():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            if user.username == 'admin':
                return redirect(url_for('index'))
            else:
                return login()  # 调用login()函数来跳转到登录页面
    return login()  # 调用login()函数来跳转到登录页面
@app.route('/return_to_enroll_course')
def return_to_enroll_course():
    return redirect(url_for('enroll_course'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 处理登录逻辑，根据用户输入的账号密码验证登录信息
        username = request.form['username']
        password = request.form['password']

        # 查询数据库中的管理员用户
        admin_user = Manager.query.filter_by(username=username, password=password).first()

        if admin_user:
            # 管理员登录成功后可以进入主页
            session['user_id'] = admin_user.id  # 存储管理员用户的 ID 到 session 中
            return redirect(url_for('index'))

        # 查询数据库中的学生用户
        student_user = User.query.filter_by(username=username, password=password).first()

        if student_user:
            # 学生登录成功后可以进入选课页面
            session['user_id'] = student_user.id  # 存储学生用户的 ID 到 session 中
            return redirect(url_for('enroll_course'))

        flash('登录失败，请检查用户名和密码', 'error')

    return render_template('login.html')
@app.route('/index')
def index():
    # 检查用户是否登录，如果没有登录，重定向到登录页面
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
    return render_template('index.html')
@app.route('/view_students')
def view_students():
    students = StudentInfo.query.all()
    return render_template('view_students.html', students=students)

# 新增路由和函数以查看课程信息
@app.route('/view_lessons')
def view_lessons():
    lessons = LessonInfo.query.all()
    return render_template('view_lessons.html', lessons=lessons)


@app.route('/enroll_course', methods=['GET', 'POST'])
def enroll_course():
    if request.method == 'POST':
        selected_lessons = request.form.getlist('lesson_id')
        student_id = session['user_id']

        # 先清除学生已选的课程
        StudentLesson.query.filter_by(student_id=student_id).delete()

        # 保存学生新选的课程
        for lesson_id in selected_lessons:
            student_lesson = StudentLesson(student_id=student_id, lesson_id=lesson_id)
            db.session.add(student_lesson)
        db.session.commit()
        flash('选课成功', 'success')
        return redirect(url_for('lesson_index', student_id=student_id))

    # 查询当前学生的专业，然后获取该专业开设的课程
    student_id = session['user_id']
    student = StudentInfo.query.get(student_id)
    if student:
        major = student.major
        available_lessons = LessonInfo.query.filter_by(major=major).all()
    else:
        flash('学生不存在')
        return redirect(url_for('index'))

    return render_template('enroll_course.html', available_lessons=available_lessons)


@app.route('/create_student', methods=['GET', 'POST'])
def create_student():
    if request.method == 'POST':
        # 处理添加学生信息逻辑，将表单中的数据保存到StudentInfo表中
        name = request.form['name']
        birthday = request.form['birthday']
        placeofbirth = request.form['placeofbirth']
        college = request.form['college']
        major = request.form['major']
        gender = request.form['gender']

        student = StudentInfo(name=name, birthday=birthday, placeofbirth=placeofbirth,
                              college=college, major=major, gender=gender)
        db.session.add(student)
        db.session.commit()
        flash('学生信息添加成功')

    return render_template('create_student.html')


@app.route('/delete_student/<int:id>', methods=['GET', 'POST'])
def delete_student(id):
    student = StudentInfo.query.get(id)
    if student:
        db.session.delete(student)
        db.session.commit()
        flash('学生信息删除成功')
    return redirect(url_for('index'))


@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = StudentInfo.query.get(id)
    if request.method == 'POST':
        # 处理编辑学生信息逻辑，更新StudentInfo表中的数据
        student.name = request.form['name']
        student.birthday = request.form['birthday']
        student.placeofbirth = request.form['placeofbirth']
        student.college = request.form['college']
        student.major = request.form['major']
        student.gender = request.form['gender']
        db.session.commit()
        flash('学生信息编辑成功')
        return redirect(url_for('view_students'))  # 编辑成功后返回到查看学生信息的页面

    return render_template('edit_student.html', student=student)

    return render_template('edit_student.html', student=student)


# 添加课程信息管理模块的路由和逻辑
@app.route('/create_lesson', methods=['GET', 'POST'])
def create_lesson():
    if request.method == 'POST':
        # 处理添加课程信息逻辑，将表单中的数据保存到LessonInfo表中
        name = request.form['name']
        teacher = request.form['teacher']
        major = request.form['major']
        grade = request.form['grade']

        lesson = LessonInfo(name=name, teacher=teacher, major=major, grade=grade)
        db.session.add(lesson)
        db.session.commit()
        flash('课程信息添加成功')

    return render_template('create_lesson.html')


@app.route('/delete_lesson/<int:id>', methods=['GET', 'POST'])
def delete_lesson(id):
    lesson = LessonInfo.query.get(id)
    if lesson:
        db.session.delete(lesson)
        db.session.commit()
        flash('课程信息删除成功')
    return redirect(url_for('view_lessons'))  # 修改为返回到查看课程信息的页面


@app.route('/edit_lesson/<int:id>', methods=['GET', 'POST'])
def edit_lesson(id):
    lesson = LessonInfo.query.get(id)
    if request.method == 'POST':
        # 处理编辑课程信息逻辑，更新LessonInfo表中的数据
        lesson.name = request.form['name']
        lesson.teacher = request.form['teacher']
        lesson.major = request.form['major']
        lesson.grade = request.form['grade']
        db.session.commit()
        flash('课程信息编辑成功')
        return redirect(url_for('view_lessons'))  # 编辑成功后返回到查看课程信息的页面

    return render_template('edit_lesson.html', lesson=lesson)



@app.route('/lesson_index/<int:student_id>')
def lesson_index(student_id):
    student = StudentInfo.query.get(student_id)
    if student:
        student_lessons = StudentLesson.query.filter_by(student_id=student.id).all()
        selected_lessons = []

        for student_lesson in student_lessons:
            lesson = LessonInfo.query.get(student_lesson.lesson_id)
            if lesson:
                selected_lessons.append(lesson)

        total_credit = sum(int(lesson.grade) for lesson in selected_lessons)

        return render_template('lesson_index.html', student=student, student_lessons=selected_lessons, total_credit=total_credit)
    else:
        flash('学生不存在')
        return redirect(url_for('index'))

# 添加其他路由和逻辑来实现学生信息管理和课程信息管理模块
# ...

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
