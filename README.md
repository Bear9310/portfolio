# Personal Portfolio Web App

A clean, modern, user-friendly portfolio to showcase your websites, apps and projects.

Users can browse projects, open live demos, and download files.  
You manage everything from a simple admin panel.

## Features

### Public side
- Beautiful dark theme with 3D tilt effect on project cards
- Search + category filter
- Featured projects (shown first)
- Project detail pages
- Live demo links + file downloads
- About section + social links in footer
- **Contact form** (messages stored for admin)
- **Privacy Policy** & **Terms of Service** pages (AdSense-ready)
- Fully responsive (mobile friendly)
- Toast notifications

### Admin side
- Secure login
- Add / Edit / Delete projects
- Upload cover images (auto-resized & optimized)
- Upload downloadable files (zip, apk, pdf, etc.)
- Categories + Featured flag
- Change password
- View & manage contact messages
- Clean dashboard with thumbnails

## Quick Start

```bash
# 1. Go into the folder
cd portfolio

# 2. Create virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python app.py
```

Open **http://127.0.0.1:5000**

### Default Admin Login
- **Username:** `admin`
- **Password:** `admin123`

> **Important:** Change the password immediately after first login  
> (Admin → Password button)

## How to use

1. Login → go to Admin
2. Click **Add Project**
3. Fill title, description, category
4. Optionally:
   - Upload a cover image
   - Upload a downloadable file (zip / apk / etc.)
   - Add a live demo URL
   - Mark as Featured
5. Save → it appears on the homepage

## Project Structure

```
portfolio/
├── app.py                 # Main application
├── requirements.txt
├── README.md
├── static/
│   ├── css/style.css
│   ├── js/tilt.js
│   └── uploads/           # Images & download files (auto-created)
└── templates/
    ├── base.html
    ├── home.html
    ├── project_detail.html
    ├── login.html
    ├── admin.html
    ├── add_edit.html
    └── change_password.html
```

## Customization

- **Social links & email** → edit `templates/base.html` (footer)
- **About text** → edit `templates/home.html` (About section)
- **Colors** → edit CSS variables in `static/css/style.css`
- **Secret key** → change `SECRET_KEY` in `app.py` (important for production)

## Production Tips

- Change the default admin password
- Set a strong random `SECRET_KEY`
- Use a production WSGI server (Gunicorn / Waitress)
- Put the app behind HTTPS
- Consider moving uploads to cloud storage (S3, etc.) for larger scale

## Allowed file types

**Images:** png, jpg, jpeg, gif, webp  
**Downloads:** zip, rar, 7z, apk, exe, dmg, pdf, doc, docx, txt, py, js, html, css

Enjoy showcasing your work!
