from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Form page
@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Here you would process and save form data
        session['resume_data'] = request.form.to_dict()
        # Handle file uploads (photo, signature)
        for file_key in ['photo', 'signature']:
            file = request.files.get(file_key)
            if file and file.filename:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                session[file_key+'_path'] = filepath
        return redirect(url_for('preview'))
    return render_template('form.html')

# Preview page
@app.route('/preview')
def preview():
    data = session.get('resume_data', {})
    photo_path = session.get('photo_path', None)
    signature_path = session.get('signature_path', None)
    # Convert static/uploads/ to relative path for HTML
    def rel_path(path):
        if path and 'static' in path:
            return path.replace('\\', '/').split('static/',1)[-1].replace('\\','/')
        return None
    return render_template('preview.html', data=data, photo_path=rel_path(photo_path), signature_path=rel_path(signature_path))

from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

@app.route('/generate', methods=['POST'])
def generate():
    data = session.get('resume_data', {})
    photo_path = session.get('photo_path', None)
    signature_path = session.get('signature_path', None)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Name and Contact
    p.setFont('Helvetica-Bold', 18)
    p.drawString(50, y, data.get('name', ''))
    y -= 24
    p.setFont('Helvetica', 12)
    p.drawString(50, y, data.get('contact', ''))
    y -= 24

    # Photo
    if photo_path and os.path.exists(photo_path):
        try:
            p.drawImage(photo_path, width - 120, height - 150, width=70, height=70, mask='auto')
        except Exception:
            pass

    # Summary
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, 'Professional Summary:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in data.get('summary', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
    y -= 8

    # Experience
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, 'Experience:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in data.get('experience', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
    y -= 8

    # Skills
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, 'Skills:')
    y -= 18
    p.setFont('Helvetica', 12)
    p.drawString(60, y, data.get('skills', ''))
    y -= 24

    # Projects
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, 'Projects:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in data.get('projects', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
    y -= 8

    # Education
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, 'Education:')
    y -= 18
    p.setFont('Helvetica', 12)
    for line in data.get('education', '').split('\n'):
        p.drawString(60, y, line)
        y -= 16
    y -= 8

    # Links
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, 'Links:')
    y -= 18
    p.setFont('Helvetica', 12)
    if data.get('github'):
        p.drawString(60, y, f"GitHub: {data.get('github')}")
        y -= 16
    if data.get('linkedin'):
        p.drawString(60, y, f"LinkedIn: {data.get('linkedin')}")
        y -= 16
    if data.get('portfolio'):
        p.drawString(60, y, f"Portfolio: {data.get('portfolio')}")
        y -= 16
    y -= 8

    # Signature
    if signature_path and os.path.exists(signature_path):
        try:
            p.drawImage(signature_path, 50, 60, width=100, height=40, mask='auto')
        except Exception:
            pass

    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='resume.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
