# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# Reemplaza la línea de SQLite con esta configuración para MariaDB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/gestion_usuarios_seguridad'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos basados en tu estructura de base de datos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    roles = db.relationship('Rol', secondary='usuario_rol', back_populates='usuarios')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Rol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    
    usuarios = db.relationship('Usuario', secondary='usuario_rol', back_populates='roles')
    permisos = db.relationship('Permiso', secondary='rol_permiso', back_populates='roles')

class Permiso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    
    roles = db.relationship('Rol', secondary='rol_permiso', back_populates='permisos')

# Tablas de relación
usuario_rol = db.Table('usuario_rol',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('rol.id'), primary_key=True)
)

rol_permiso = db.Table('rol_permiso',
    db.Column('rol_id', db.Integer, db.ForeignKey('rol.id'), primary_key=True),
    db.Column('permiso_id', db.Integer, db.ForeignKey('permiso.id'), primary_key=True)
)

# Crear tablas en la base de datos
with app.app_context():
    db.create_all()
    
    # Crear datos iniciales si no existen
    if not Rol.query.first():
        # Crear roles
        admin_rol = Rol(nombre='administrador')
        editor_rol = Rol(nombre='editor')
        lector_rol = Rol(nombre='lector')
        
        # Crear permisos
        permiso_crear = Permiso(nombre='crear')
        permiso_leer = Permiso(nombre='leer')
        permiso_editar = Permiso(nombre='editar')
        permiso_eliminar = Permiso(nombre='eliminar')
        
        # Asignar permisos a roles
        admin_rol.permisos.extend([permiso_crear, permiso_leer, permiso_editar, permiso_eliminar])
        editor_rol.permisos.extend([permiso_crear, permiso_leer, permiso_editar])
        lector_rol.permisos.extend([permiso_leer])
        
        # Crear usuario administrador
        admin = Usuario(username='admin')
        admin.set_password('admin123')
        admin.roles.append(admin_rol)
        
        # Guardar en base de datos
        db.session.add_all([admin_rol, editor_rol, lector_rol, 
                           permiso_crear, permiso_leer, permiso_editar, permiso_eliminar,
                           admin])
        db.session.commit()

# Decorador para verificar permisos
def requiere_permiso(permiso_nombre):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Debes iniciar sesión primero', 'danger')
                return redirect(url_for('login'))
            
            # Usamos una consulta más eficiente con joins
            tiene_permiso = db.session.query(Permiso).join(rol_permiso).join(Rol).join(usuario_rol).filter(
                usuario_rol.c.usuario_id == session['user_id'],
                Permiso.nombre == permiso_nombre
            ).first() is not None
            
            if not tiene_permiso:
                flash('No tienes permiso para acceder a esta página', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rutas de la aplicación
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'login_attempts' not in session:
        session['login_attempts'] = 0
        session['lockout_time'] = None

    # Comprobar si hay bloqueo activo
    if session.get('lockout_time'):
        lockout_time = datetime.strptime(session['lockout_time'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() < lockout_time:
            tiempo_restante = (lockout_time - datetime.now()).seconds
            minutos = tiempo_restante // 60
            segundos = tiempo_restante % 60
            flash(f'Demasiados intentos fallidos. Inténtalo nuevamente en {minutos}m {segundos}s.', 'danger')
            return render_template('login.html')
        else:
            # Se acabó el bloqueo, reiniciamos
            session['login_attempts'] = 0
            session['lockout_time'] = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Usuario.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Acceso exitoso
            session['user_id'] = user.id
            session['username'] = user.username
            session['login_attempts'] = 0
            session['lockout_time'] = None
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            session['login_attempts'] += 1
            intentos_restantes = 3 - session['login_attempts']

            if session['login_attempts'] >= 3:
                # Bloqueo por 5 minutos
                bloqueo = datetime.now() + timedelta(minutes=5)
                session['lockout_time'] = bloqueo.strftime('%Y-%m-%d %H:%M:%S')
                flash('Demasiados intentos fallidos. Intenta nuevamente más tarde.', 'danger')
            else:
                flash(f'Usuario o contraseña incorrectos. Intentos restantes: {intentos_restantes}', 'warning')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@requiere_permiso('leer')
def dashboard():
    user = Usuario.query.get(session['user_id'])
    roles = [rol.nombre for rol in user.roles]
    
    permisos = set()
    for rol in user.roles:
        for permiso in rol.permisos:
            permisos.add(permiso.nombre)
    
    return render_template('dashboard.html', roles=roles, permisos=list(permisos))

@app.route('/usuarios')
@requiere_permiso('leer')
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios/listar.html', usuarios=usuarios)

@app.route('/usuarios/crear', methods=['GET', 'POST'])
@requiere_permiso('crear')
def crear_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'danger')
            return render_template('usuarios/crear.html')
        
        nuevo_usuario = Usuario(username=username)
        nuevo_usuario.set_password(password)
        
        # Asignar roles seleccionados
        roles_seleccionados = request.form.getlist('roles')
        for rol_id in roles_seleccionados:
            rol = Rol.query.get(rol_id)
            nuevo_usuario.roles.append(rol)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario creado exitosamente', 'success')
        return redirect(url_for('listar_usuarios'))
    
    roles = Rol.query.all()
    return render_template('usuarios/crear.html', roles=roles)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@requiere_permiso('editar')
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        # Actualizar roles
        roles_seleccionados = request.form.getlist('roles')
        usuario.roles = []
        
        for rol_id in roles_seleccionados:
            rol = Rol.query.get(rol_id)
            usuario.roles.append(rol)
        
        db.session.commit()
        flash('Usuario actualizado exitosamente', 'success')
        return redirect(url_for('listar_usuarios'))
    
    roles = Rol.query.all()
    return render_template('usuarios/editar.html', usuario=usuario, roles=roles)

@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('eliminar')
def eliminar_usuario(id):
    if id == session.get('user_id'):
        flash('No puedes eliminar tu propia cuenta', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('listar_usuarios'))

@app.route('/roles')
@requiere_permiso('leer')
def listar_roles():
    roles = Rol.query.all()
    return render_template('roles/listar.html', roles=roles)

@app.route('/roles/crear', methods=['GET', 'POST'])
@requiere_permiso('crear')
def crear_rol():
    if request.method == 'POST':
        nombre = request.form['nombre']
        
        if Rol.query.filter_by(nombre=nombre).first():
            flash('El nombre del rol ya existe', 'danger')
            return render_template('roles/crear.html')
        
        nuevo_rol = Rol(nombre=nombre)
        
        # Asignar permisos seleccionados
        permisos_seleccionados = request.form.getlist('permisos')
        for permiso_id in permisos_seleccionados:
            permiso = Permiso.query.get(permiso_id)
            nuevo_rol.permisos.append(permiso)
        
        db.session.add(nuevo_rol)
        db.session.commit()
        
        flash('Rol creado exitosamente', 'success')
        return redirect(url_for('listar_roles'))
    
    permisos = Permiso.query.all()
    return render_template('roles/crear.html', permisos=permisos)

@app.route('/roles/editar/<int:id>', methods=['GET', 'POST'])
@requiere_permiso('editar')
def editar_rol(id):
    rol = Rol.query.get_or_404(id)
    
    if request.method == 'POST':
        # Actualizar permisos
        permisos_seleccionados = request.form.getlist('permisos')
        rol.permisos = []
        
        for permiso_id in permisos_seleccionados:
            permiso = Permiso.query.get(permiso_id)
            rol.permisos.append(permiso)
        
        db.session.commit()
        flash('Rol actualizado exitosamente', 'success')
        return redirect(url_for('listar_roles'))
    
    permisos = Permiso.query.all()
    return render_template('roles/editar.html', rol=rol, permisos=permisos)

@app.route('/permisos')
@requiere_permiso('leer')
def listar_permisos():
    permisos = Permiso.query.all()
    return render_template('permisos/listar.html', permisos=permisos)

@app.route('/permisos/crear', methods=['GET', 'POST'])
@requiere_permiso('crear')
def crear_permiso():
    if request.method == 'POST':
        nombre = request.form['nombre'].lower()
        
        if Permiso.query.filter_by(nombre=nombre).first():
            flash('Este permiso ya existe', 'danger')
            return redirect(url_for('crear_permiso'))
        
        nuevo_permiso = Permiso(nombre=nombre)
        db.session.add(nuevo_permiso)
        db.session.commit()
        
        flash(f'Permiso "{nombre}" creado exitosamente', 'success')
        return redirect(url_for('listar_permisos'))
    
    return render_template('permisos/crear.html')

@app.route('/permisos/editar/<int:id>', methods=['GET', 'POST'])
@requiere_permiso('editar')
def editar_permiso(id):
    permiso = Permiso.query.get_or_404(id)
    
    if request.method == 'POST':
        nuevo_nombre = request.form['nombre'].lower()
        
        if nuevo_nombre != permiso.nombre and Permiso.query.filter_by(nombre=nuevo_nombre).first():
            flash('Ya existe un permiso con ese nombre', 'danger')
        else:
            permiso.nombre = nuevo_nombre
            db.session.commit()
            flash('Permiso actualizado', 'success')
        
        return redirect(url_for('listar_permisos'))
    
    return render_template('permisos/editar.html', permiso=permiso)

@app.route('/permisos/eliminar/<int:id>', methods=['POST'])
@requiere_permiso('eliminar')
def eliminar_permiso(id):
    permiso = Permiso.query.get_or_404(id)
    
    if permiso.nombre in ['crear', 'leer', 'editar', 'eliminar']:
        flash('No se pueden eliminar los permisos básicos del sistema', 'danger')
    else:
        db.session.delete(permiso)
        db.session.commit()
        flash('Permiso eliminado exitosamente', 'success')
    
    return redirect(url_for('listar_permisos'))

@app.route('/registros')
@requiere_permiso('leer')
def ver_registros():
    # Simulando acceso a registros con diferentes permisos
    user = Usuario.query.get(session['user_id'])
    tiene_permiso_editar = False
    
    for rol in user.roles:
        for permiso in rol.permisos:
            if permiso.nombre == 'editar':
                tiene_permiso_editar = True
                break
        if tiene_permiso_editar:
            break
    
    # Registros de ejemplo
    registros = [
        {'id': 1, 'nombre': 'Registro 1', 'fecha': '2023-05-01'},
        {'id': 2, 'nombre': 'Registro 2', 'fecha': '2023-05-02'},
        {'id': 3, 'nombre': 'Registro 3', 'fecha': '2023-05-03'},
    ]
    
    return render_template('registros.html', registros=registros, puede_editar=tiene_permiso_editar)

@app.route('/registros/editar/<int:id>', methods=['GET', 'POST'])
@requiere_permiso('editar')
def editar_registro(id):
    # Simulación de edición de registro
    if request.method == 'POST':
        flash(f'Registro {id} actualizado exitosamente', 'success')
        return redirect(url_for('ver_registros'))
    
    registro = {'id': id, 'nombre': f'Registro {id}', 'fecha': '2023-05-01'}
    return render_template('editar_registro.html', registro=registro)

@app.route('/registros/crear', methods=['GET', 'POST'])
@requiere_permiso('editar')  # Asumiendo que crear requiere permiso de edición
def crear_registro():
    if request.method == 'POST':
        # Lógica para guardar el nuevo registro
        flash('Registro creado exitosamente', 'success')
        return redirect(url_for('ver_registros'))
    
    return render_template('registros/crear_registro.html')

if __name__ == '__main__':
    with app.app_context():
        # Forzar el reinicio de los autoincrementos
        #db.engine.execute("SET FOREIGN_KEY_CHECKS = 0;")
        #db.create_all()
        #db.engine.execute("SET FOREIGN_KEY_CHECKS = 1;")
        app.run(debug=True)