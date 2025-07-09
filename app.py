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

    # Cabeçalho colorido
    header_height = 70
    p.setFillColorRGB(0.18, 0.36, 0.65)  # Azul escuro
    p.rect(0, height - header_height, width, header_height, fill=1, stroke=0)

    # Nome e contato no cabeçalho
    p.setFillColorRGB(1, 1, 1)
    p.setFont('Helvetica-Bold', 22)
    p.drawString(40, height - 40, data.get('name', ''))
    p.setFont('Helvetica', 12)
    p.drawString(40, height - 60, data.get('contact', ''))

    # Foto no cabeçalho
    if photo_path and os.path.exists(photo_path):
        try:
            p.drawImage(photo_path, width - 90, height - header_height + 10, width=50, height=50, mask='auto')
        except Exception:
            pass

    y = height - header_height - 30

    # Linha separadora
    p.setStrokeColorRGB(0.7, 0.7, 0.7)
    p.setLineWidth(1)
    p.line(40, y, width - 40, y)
    y -= 20

    # Função para seções
    def section(title):
        nonlocal y
        p.setFont('Helvetica-Bold', 14)
        p.setFillColorRGB(0.18, 0.36, 0.65)
        p.drawString(40, y, title)
        y -= 16
        p.setFillColorRGB(0, 0, 0)
        p.setFont('Helvetica', 12)

    # Professional Summary
    if data.get('summary'):
        section('Professional Summary')
        for line in data.get('summary', '').split('\n'):
            p.drawString(50, y, line)
            y -= 15
        y -= 8

    # Experience
    if data.get('experience'):
        section('Experience')
        for line in data.get('experience', '').split('\n'):
            p.drawString(50, y, line)
            y -= 15
        y -= 8

    # Skills
    if data.get('skills'):
        section('Skills')
        p.drawString(50, y, data.get('skills', ''))
        y -= 22

    # Projects
    if data.get('projects'):
        section('Projects')
        for line in data.get('projects', '').split('\n'):
            p.drawString(50, y, line)
            y -= 15
        y -= 8

    # Education
    if data.get('education'):
        section('Education')
        for line in data.get('education', '').split('\n'):
            p.drawString(50, y, line)
            y -= 15
        y -= 8

    # Links
    if data.get('github') or data.get('linkedin') or data.get('portfolio'):
        section('Links')
        if data.get('github'):
            p.drawString(50, y, f"GitHub: {data.get('github')}")
            y -= 15
        if data.get('linkedin'):
            p.drawString(50, y, f"LinkedIn: {data.get('linkedin')}")
            y -= 15
        if data.get('portfolio'):
            p.drawString(50, y, f"Portfolio: {data.get('portfolio')}")
            y -= 15
        y -= 8

    # Linha separadora final
    if y > 80:
        p.setStrokeColorRGB(0.7, 0.7, 0.7)
        p.setLineWidth(0.5)
        p.line(40, y, width - 40, y)
        y -= 20

    # Assinatura
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
