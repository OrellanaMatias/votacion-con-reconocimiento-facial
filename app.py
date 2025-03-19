from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import sqlite3
import json
from datetime import datetime
import base64
import cv2
import numpy as np
from PIL import Image
import io

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super_clave_secreta_tengosueño')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database/votacion.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db = SQLAlchemy(app)

# Configurar el sistema de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Asegurar que existan los directorios necesarios
@app.before_first_request
def create_directories():
    os.makedirs('database', exist_ok=True)
    os.makedirs('static/faces', exist_ok=True)

# Modelos de la base de datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    candidates = db.relationship('Candidate', backref='election', lazy=True)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    photo = db.Column(db.String(200))  # Ruta a la foto del candidato
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    votes = db.relationship('Vote', backref='candidate', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.String(8), unique=True, nullable=False)  # DNI argentino de 8 dígitos
    face_encoding = db.Column(db.Text)  # Codificación facial almacenada como JSON
    votes = db.relationship('Vote', backref='student', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rutas para la aplicación
@app.route('/')
def index():
    active_election = Election.query.filter_by(is_active=True).first()
    return render_template('index.html', election=active_election)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # En producción usar hash de contraseñas
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciales incorrectas')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Acceso no autorizado')
        return redirect(url_for('index'))
    
    elections = Election.query.all()
    return render_template('admin/dashboard.html', elections=elections)

@app.route('/admin/election/new', methods=['GET', 'POST'])
@login_required
def new_election():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        
        election = Election(title=title, description=description, start_date=start_date, end_date=end_date)
        db.session.add(election)
        db.session.commit()
        
        flash('Elección creada correctamente')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/new_election.html')

@app.route('/admin/election/<int:election_id>')
@login_required
def view_election(election_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    election = Election.query.get_or_404(election_id)
    return render_template('admin/view_election.html', election=election)

@app.route('/admin/election/<int:election_id>/toggle', methods=['POST'])
@login_required
def toggle_election(election_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    election = Election.query.get_or_404(election_id)
    
    # Si vamos a activar esta elección, desactivamos todas las demás
    if not election.is_active:
        active_elections = Election.query.filter_by(is_active=True).all()
        for active_election in active_elections:
            active_election.is_active = False
    
    election.is_active = not election.is_active
    db.session.commit()
    
    status = 'activada' if election.is_active else 'desactivada'
    flash(f'Elección {status} correctamente')
    return redirect(url_for('view_election', election_id=election_id))

@app.route('/admin/election/<int:election_id>/candidate/new', methods=['GET', 'POST'])
@login_required
def new_candidate(election_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    election = Election.query.get_or_404(election_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        photo = request.files.get('photo')
        
        photo_filename = None
        if photo and photo.filename:
            # Guardar la foto del candidato
            photo_filename = f'candidate_{election_id}_{name.replace(" ", "_")}.jpg'
            photo.save(os.path.join('static/images', photo_filename))
        
        candidate = Candidate(name=name, description=description, photo=photo_filename, election_id=election_id)
        db.session.add(candidate)
        db.session.commit()
        
        flash('Candidato añadido correctamente')
        return redirect(url_for('view_election', election_id=election_id))
    
    return render_template('admin/new_candidate.html', election=election)

@app.route('/admin/students')
@login_required
def manage_students():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    students = Student.query.all()
    return render_template('admin/students.html', students=students)

@app.route('/admin/student/new', methods=['GET', 'POST'])
@login_required
def new_student():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        dni = request.form.get('dni')
        face_data = request.form.get('face_data')  # Datos de codificación facial en formato JSON
        
        print(f"Datos recibidos - Nombre: {name}, DNI: {dni}, Face Data presente: {'Sí' if face_data else 'No'}")
        
        # Validar DNI
        if not dni or not dni.isdigit() or len(dni) != 8:
            flash('El DNI debe ser un número de 8 dígitos')
            return render_template('admin/new_student.html')
        
        # Verificar si el DNI ya existe
        existing_student = Student.query.filter_by(dni=dni).first()
        if existing_student:
            flash('Ya existe un estudiante registrado con ese DNI')
            return render_template('admin/new_student.html')
        
        if not face_data:
            flash('No se pudo capturar el rostro correctamente')
            return render_template('admin/new_student.html')
        
        try:
            # Verificar que face_data sea un JSON válido
            face_data_json = json.loads(face_data)
            if not isinstance(face_data_json, dict) or 'descriptor' not in face_data_json:
                flash('Los datos faciales no tienen el formato correcto')
                return render_template('admin/new_student.html')
            
            student = Student(name=name, dni=dni, face_encoding=face_data)
            db.session.add(student)
            db.session.commit()
            print(f"Estudiante registrado exitosamente - ID: {student.id}")
            flash('Estudiante registrado correctamente')
            return redirect(url_for('manage_students'))
            
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON de datos faciales: {str(e)}")
            flash('Error en el formato de los datos faciales')
            return render_template('admin/new_student.html')
        except Exception as e:
            print(f"Error al registrar estudiante: {str(e)}")
            db.session.rollback()
            flash('Error al registrar el estudiante')
            return render_template('admin/new_student.html')
    
    return render_template('admin/new_student.html')

@app.route('/vote/<int:election_id>', methods=['GET', 'POST'])
def vote(election_id):
    election = Election.query.get_or_404(election_id)
    
    if not election.is_active:
        flash('Esta elección no está activa actualmente')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        face_data = request.form.get('face_data')  # Datos de la imagen facial capturada
        candidate_id = request.form.get('candidate_id')
        
        # Aquí iría la lógica de reconocimiento facial para identificar al estudiante
        # Por simplicidad, asumimos que el reconocimiento fue exitoso y devuelve un student_id
        student_id = verify_face(face_data)
        
        if student_id:
            # Verificar si el estudiante ya votó en esta elección
            existing_vote = Vote.query.filter_by(student_id=student_id, election_id=election_id).first()
            
            if existing_vote:
                flash('Ya has emitido tu voto en esta elección')
            else:
                vote = Vote(student_id=student_id, candidate_id=candidate_id, election_id=election_id)
                db.session.add(vote)
                db.session.commit()
                flash('¡Voto registrado correctamente!')
        else:
            flash('No se pudo verificar tu identidad')
    
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    return render_template('vote.html', election=election, candidates=candidates)

@app.route('/results/<int:election_id>')
def results(election_id):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    
    results = []
    for candidate in candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
        results.append({
            'name': candidate.name,
            'votes': vote_count
        })
    
    return render_template('results.html', election=election, results=results)

# Función para verificar la identidad mediante reconocimiento facial
def verify_face(face_data):
    # Aquí iría la implementación real del reconocimiento facial
    # Por ahora, es una implementación simulada
    
    # Decodificar la imagen base64
    try:
        # Eliminar el prefijo 'data:image/jpeg;base64,' si existe
        if 'base64,' in face_data:
            face_data = face_data.split('base64,')[1]
        
        # Decodificar la imagen
        face_bytes = base64.b64decode(face_data)
        face_image = Image.open(io.BytesIO(face_bytes))
        
        # Convertir a formato OpenCV
        face_array = np.array(face_image)
        face_array = cv2.cvtColor(face_array, cv2.COLOR_RGB2BGR)
        
        # Aquí iría el código real de reconocimiento facial
        # Por ahora, simulamos la verificación
        
        # Obtener todos los estudiantes
        students = Student.query.all()
        
        # En una implementación real, compararíamos la codificación facial
        # con las almacenadas en la base de datos
        # Por ahora, devolvemos el primer estudiante como ejemplo
        if students:
            return students[0].id
        
        return None
    except Exception as e:
        print(f"Error en reconocimiento facial: {e}")
        return None

# Rutas API para el reconocimiento facial en el frontend
@app.route('/api/register-face', methods=['POST'])
def register_face_api():
    data = request.json
    face_data = data.get('faceData')
    student_name = data.get('name')
    
    if face_data and student_name:
        # Guardar la codificación facial en la base de datos
        student = Student(name=student_name, face_encoding=json.dumps(face_data))
        db.session.add(student)
        db.session.commit()
        return jsonify({'success': True, 'student_id': student.id})
    
    return jsonify({'success': False, 'error': 'Datos incompletos'})

@app.route('/api/verify-face', methods=['POST'])
def verify_face_api():
    data = request.json
    face_data = data.get('faceData')
    
    if face_data:
        # Verificar la identidad del estudiante
        student_id = verify_face(face_data)
        
        if student_id:
            student = Student.query.get(student_id)
            return jsonify({
                'success': True, 
                'student_id': student_id,
                'student_name': student.name
            })
    
    return jsonify({'success': False, 'error': 'No se pudo verificar la identidad'})

# Inicializar la base de datos y crear usuario administrador
@app.before_first_request
def initialize_database():
    db.create_all()
    
    # Crear usuario administrador si no existe
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()

# Iniciar la aplicación
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)