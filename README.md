# Sistema de Gestión de Usuarios con Flask

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Un sistema completo de gestión de usuarios con autenticación, roles y permisos implementado en Flask.

## Características Principales

✅ Autenticación segura de usuarios  
✅ Gestión de roles y permisos  
✅ CRUD completo para usuarios  
✅ Autorización basada en permisos  
✅ Interfaz administrativa responsive  
✅ Base de datos SQLite (listo para producción con otros DBMS)  

## Estructura del Proyecto
```bash
gestion_usuarios/
├── app.py # Aplicación principal
├── requirements.txt # Dependencias
├── instance/
│ └── gestion_usuarios.db # Base de datos SQLite
└── templates/
├── auth/ # Plantillas de autenticación
├── usuarios/ # Gestión de usuarios
├── roles/ # Gestión de roles
├── permisos/ # Gestión de permisos
└── registros/ # Ejemplo de módulo con control de acceso
```

## Requisitos

- Python 3.8+
- pip

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/gestion-usuarios-flask.git
cd gestion-usuarios-flask
```
Instalar dependencias:

```bash
pip install -r requirements.txt`
```
# Configuración
Configuración básica en app.py:

```python
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'  # Cambiar en producción!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestion_usuarios.db'
```
Para otros sistemas de base de datos:

```python
# MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://usuario:contraseña@localhost/nombre_db'

# PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:contraseña@localhost/nombre_db'
```
Uso
Iniciar la aplicación:

```bash
flask run
```
Acceder en el navegador:
```bash
http://localhost:5000
```
Credenciales iniciales:
```bash
Administrador: admin / admin123

Editor: editor / editor123

Lector: lector / lector123
```
# Módulos Disponibles
Gestión de Usuarios
- Crear, editar y eliminar usuarios

- Asignar múltiples roles a usuarios

- Cambiar contraseñas

# Gestión de Roles
- Definir roles (ej: admin, editor, lector)

- Asignar permisos a roles

- Jerarquía de permisos

# Gestión de Permisos
- Permisos básicos: crear, leer, editar, eliminar

- Posibilidad de añadir permisos personalizados

# Registros (Ejemplo)
- Ejemplo práctico de control de acceso

- Demostración de permisos en acción

# Tecnologías Utilizadas
Backend:

- Flask

- Flask-SQLAlchemy

- Flask-Login

- Werkzeug (para hash de contraseñas)

# Frontend:

- Bootstrap 5

- Bootstrap Icons

- Jinja2 (templating)