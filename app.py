from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import secrets
import string
import shutil
# from flask_sslify import SSLify

app = Flask(__name__)
# sslify = SSLify(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = os.urandom(24)
key = "clipluck-bee"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(256), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now())
    filename = db.Column(db.String(255), nullable=True)


# Ensure the 'uploads' folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def generate_random_alphanumeric():
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(12))
    return random_string


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        password = request.form['password']
        if password == key:
            session['authenticated'] = True
            return redirect('/clip')
        return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/clip', methods=['POST', 'GET'])
def clip():
    if session.get('authenticated'):
        if request.method == 'POST':
            content = request.form['content']
            file = request.files.get('file')
            if file:
                filename = secure_filename(file.filename)
                filename_after_splitting = filename.split('.')
                file_extension = filename_after_splitting[-1]
                random_name = generate_random_alphanumeric()
                hashed_filename = random_name + '.' + file_extension
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], hashed_filename))
                new_clip = Task(content=content, filename=hashed_filename)
            else:
                new_clip = Task(content=content)
            try:
                db.session.add(new_clip)
                db.session.commit()
                return redirect('/clip')
            except Exception as e:
                return e
        else:
            clips = Task.query.order_by(Task.date_created).all()
            return render_template('index.html', clips=clips)
    else:
        return redirect('/')


@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/view/<filename>')
def view(filename):
    if filename:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    

@app.route('/delete/<int:id>')
def delete(id):
    clip_to_delete = Task.query.get_or_404(id)
    try:
        db.session.delete(clip_to_delete)
        db.session.commit()
        return redirect('/clip')
    except Exception as e:
        return e


@app.route('/delete_all')
def delete_all():
    Task.query.delete()
    db.session.commit()
    shutil.rmtree(app.config['UPLOAD_FOLDER'])
    os.makedirs(app.config['UPLOAD_FOLDER'])
    return redirect('/clip')


@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect('/')


if __name__ == "__main__":
    # app.run(debug=True, host='0.0.0.0')
    app.run(debug=True)
    # , ssl_context = ('cert.pem', 'key.pem')
