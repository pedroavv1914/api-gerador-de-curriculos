from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Home page
@app.route('/')
def home():
    return render_template('base.html')

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

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
