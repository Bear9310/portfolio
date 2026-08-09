from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-me-to-a-very-long-random-secret-key-please'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# Allowed extensions
ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_FILE_EXT = {'zip', 'rar', '7z', 'apk', 'exe', 'dmg', 'pdf', 'doc', 'docx', 'txt', 'py', 'js', 'html', 'css'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# ---------- Models ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_desc = db.Column(db.String(250))  # for cards
    category = db.Column(db.String(50), default='Other')
    image = db.Column(db.String(200))
    file = db.Column(db.String(200))
    link = db.Column(db.String(400))
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------- Helpers ----------
def allowed_file(filename, allowed):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def save_image(file_storage):
    """Save and resize image, return filename"""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename, ALLOWED_IMAGE_EXT):
        flash('Invalid image type. Allowed: png, jpg, jpeg, gif, webp', 'danger')
        return None
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    # Resize if large
    try:
        img = Image.open(file_storage.stream)
        img = img.convert('RGB') if ext in ('jpg', 'jpeg') else img
        # Max width 1200px, keep aspect
        max_w = 1200
        if img.width > max_w:
            ratio = max_w / img.width
            new_size = (max_w, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(path, optimize=True, quality=85)
        return filename
    except Exception as e:
        flash(f'Image processing error: {e}', 'danger')
        return None

def save_file(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename, ALLOWED_FILE_EXT):
        flash('Invalid file type for download.', 'danger')
        return None
    filename = secure_filename(file_storage.filename)
    # Make unique
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_storage.save(path)
    return filename

# ---------- Public Routes ----------
@app.route('/')
def home():
    q = request.args.get('q', '').strip()
    cat = request.args.get('category', '').strip()
    query = Project.query
    if q:
        query = query.filter(
            db.or_(
                Project.title.ilike(f'%{q}%'),
                Project.description.ilike(f'%{q}%'),
                Project.short_desc.ilike(f'%{q}%')
            )
        )
    if cat and cat != 'All':
        query = query.filter_by(category=cat)
    projects = query.order_by(Project.featured.desc(), Project.created_at.desc()).all()
    categories = db.session.query(Project.category).distinct().all()
    categories = sorted([c[0] for c in categories if c[0]])
    return render_template('home.html', projects=projects, categories=categories,
                           current_q=q, current_cat=cat or 'All')

@app.route('/project/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)
    return render_template('project_detail.html', project=project)

@app.route('/download/<filename>')
def download(filename):
    # Security: only allow files that exist in uploads and are referenced? (simple check)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip() or 'General Inquiry'
        message = request.form.get('message', '').strip()
        if not name or not email or not message:
            flash('Please fill in name, email and message.', 'danger')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            flash('Please enter a valid email address.', 'danger')
        else:
            msg = ContactMessage(name=name, email=email, subject=subject, message=message)
            db.session.add(msg)
            db.session.commit()
            flash('Thank you! Your message has been sent. I will get back to you soon.', 'success')
            return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')
@app.route('/ads.txt')
def ads_txt():
    ads_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ads.txt')
    if os.path.exists(ads_path):
        with open(ads_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "google.com, pub-3329636071936518, DIRECT, f08c47fec0942fa0\n"
    return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

# ---------- Auth ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

# ---------- Admin ----------
@app.route('/admin')
@login_required
def admin():
    projects = Project.query.order_by(Project.featured.desc(), Project.created_at.desc()).all()
    return render_template('admin.html', projects=projects)

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        short_desc = request.form.get('short_desc', '').strip() or (description[:200] + '...' if len(description) > 200 else description)
        category = request.form.get('category', 'Other').strip() or 'Other'
        link = request.form.get('link', '').strip() or None
        featured = bool(request.form.get('featured'))

        if not title or not description:
            flash('Title and description are required', 'danger')
            return render_template('add_edit.html', project=None)

        image_name = save_image(request.files.get('image'))
        file_name = save_file(request.files.get('file'))

        project = Project(
            title=title,
            description=description,
            short_desc=short_desc,
            category=category,
            image=image_name,
            file=file_name,
            link=link,
            featured=featured
        )
        db.session.add(project)
        db.session.commit()
        flash('Project added successfully!', 'success')
        return redirect(url_for('admin'))

    return render_template('add_edit.html', project=None)

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    project = Project.query.get_or_404(id)
    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.description = request.form.get('description', '').strip()
        project.short_desc = request.form.get('short_desc', '').strip() or project.description[:200]
        project.category = request.form.get('category', 'Other').strip() or 'Other'
        project.link = request.form.get('link', '').strip() or None
        project.featured = bool(request.form.get('featured'))

        # New image?
        new_img = save_image(request.files.get('image'))
        if new_img:
            # delete old
            if project.image:
                old = os.path.join(app.config['UPLOAD_FOLDER'], project.image)
                if os.path.exists(old):
                    os.remove(old)
            project.image = new_img

        # New file?
        new_file = save_file(request.files.get('file'))
        if new_file:
            if project.file:
                old = os.path.join(app.config['UPLOAD_FOLDER'], project.file)
                if os.path.exists(old):
                    os.remove(old)
            project.file = new_file

        # Remove file checkbox
        if request.form.get('remove_file') and project.file:
            old = os.path.join(app.config['UPLOAD_FOLDER'], project.file)
            if os.path.exists(old):
                os.remove(old)
            project.file = None

        if request.form.get('remove_image') and project.image:
            old = os.path.join(app.config['UPLOAD_FOLDER'], project.image)
            if os.path.exists(old):
                os.remove(old)
            project.image = None

        db.session.commit()
        flash('Project updated!', 'success')
        return redirect(url_for('admin'))

    return render_template('add_edit.html', project=project)

@app.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    project = Project.query.get_or_404(id)
    if project.image:
        path = os.path.join(app.config['UPLOAD_FOLDER'], project.image)
        if os.path.exists(path):
            os.remove(path)
    if project.file:
        path = os.path.join(app.config['UPLOAD_FOLDER'], project.file)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if not check_password_hash(current_user.password, current):
            flash('Current password is wrong', 'danger')
        elif len(new) < 6:
            flash('New password must be at least 6 characters', 'danger')
        elif new != confirm:
            flash('New passwords do not match', 'danger')
        else:
            current_user.password = generate_password_hash(new)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('admin'))
    return render_template('change_password.html')

@app.route('/admin/messages')
@login_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)

@app.route('/admin/messages/<int:id>/read', methods=['POST'])
@login_required
def mark_message_read(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<int:id>/delete', methods=['POST'])
@login_required
def delete_message(id):
    msg = ContactMessage.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted', 'success')
    return redirect(url_for('admin_messages'))

# ---------- Setup ----------
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('Naim@9310')
            )
            db.session.add(admin)
            db.session.commit()
            print("=" * 50)
            print("Admin account created!")
            print("Username: admin")
            print("Password: admin123")
            print(">>> CHANGE THE PASSWORD IMMEDIATELY after first login <<<")
            print("=" * 50)

# Create tables when the app starts (needed for Render / gunicorn)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin account created: admin / admin123")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
