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
    error = None
    if request.method == 'POST':
        data = request.form.to_dict()
        required_fields = ['name', 'contact', 'summary', 'experience', 'skills', 'projects', 'education']
        missing = [field for field in required_fields if not data.get(field, '').strip()]
        if missing:
            error = 'Please fill in all required fields.'
            return render_template('form.html', error=error, data=data, missing=missing)
        session['resume_data'] = data
        for file_key in ['photo', 'signature']:
            file = request.files.get(file_key)
            if file and file.filename:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                session[file_key+'_path'] = filepath
        return redirect(url_for('preview'))
    data = session.get('resume_data')
    return render_template('form.html', error=error, data=data)

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

    # Cabeçalho moderno
    header_height = 120
    p.setFillColorRGB(0.18, 0.36, 0.65)  # Azul escuro
    p.rect(0, height - header_height, width, header_height, fill=1, stroke=0)

    # Nome grande
    p.setFillColorRGB(1, 1, 1)
    p.setFont('Helvetica-Bold', 28)
    p.drawString(55, height - 55, data.get('name', ''))
    # Contato
    p.setFont('Helvetica', 14)
    p.drawString(55, height - 80, data.get('contact', ''))

    # Foto circular à direita
    if photo_path and os.path.exists(photo_path):
        try:
            p.saveState()
            p.setFillColorRGB(1, 1, 1)
            p.circle(width - 95, height - header_height//2 + 10, 45, fill=1, stroke=0)
            p.clipPath(p.beginPath().circle(width - 95, height - header_height//2 + 10, 45), stroke=0)
            p.drawImage(photo_path, width - 140, height - header_height + 15, width=90, height=90, mask='auto')
            p.restoreState()
        except Exception:
            pass

    y = height - header_height - 20

    # Função para divisória
    def divider():
        nonlocal y
        p.setStrokeColorRGB(0.88, 0.91, 0.95)
        p.setLineWidth(1.5)
        p.line(55, y, width - 55, y)
        y -= 18

    # Função para título de seção
    def section(title):
        nonlocal y
        p.setFont('Helvetica-Bold', 16)
        p.setFillColorRGB(0.18, 0.36, 0.65)
        p.drawString(55, y, title)
        y -= 22
        p.setFillColorRGB(0, 0, 0)
        p.setFont('Helvetica', 12)

    # Seções
    if data.get('summary'):
        section('Resumo Profissional')
        for line in data.get('summary', '').split('\n'):
            p.drawString(65, y, line)
            y -= 15
        divider()
    if data.get('experience'):
        section('Experiência')
        for line in data.get('experience', '').split('\n'):
            p.drawString(65, y, line)
            y -= 15
        divider()
    if data.get('skills'):
        section('Habilidades')
        p.drawString(65, y, data.get('skills', ''))
        y -= 18
        divider()
    if data.get('projects'):
        section('Projetos')
        for line in data.get('projects', '').split('\n'):
            p.drawString(65, y, line)
            y -= 15
        divider()
    if data.get('education'):
        section('Formação')
        for line in data.get('education', '').split('\n'):
            p.drawString(65, y, line)
            y -= 15
        divider()
    if data.get('github') or data.get('linkedin') or data.get('portfolio'):
        section('Links')
        if data.get('github'):
            p.drawString(65, y, f"GitHub: {data.get('github')}")
            y -= 15
        if data.get('linkedin'):
            p.drawString(65, y, f"LinkedIn: {data.get('linkedin')}")
            y -= 15
        if data.get('portfolio'):
            p.drawString(65, y, f"Portfólio: {data.get('portfolio')}")
            y -= 15
        divider()

    # Assinatura centralizada
    if signature_path and os.path.exists(signature_path):
        try:
            p.drawImage(signature_path, width//2 - 60, 55, width=120, height=40, mask='auto')
        except Exception:
            pass

    p.showPage()
    p.save()
    buffer.seek(0)
    # Limpar dados da sessão após download
    session.pop('resume_data', None)
    session.pop('photo_path', None)
    session.pop('signature_path', None)
    return send_file(buffer, as_attachment=True, download_name='curriculo.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
