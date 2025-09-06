# Sistema Académico

Sistema de información académico implementado con arquitectura SOA (Service Oriented Architecture).

## Estructura del Proyecto

```
SOA-TALLER/
├── api_gateway.py              # API Gateway / Orquestador
├── students_service.py         # Servicio de Estudiantes
├── courses_service.py          # Servicio de Cursos
├── enrollments_service.py      # Servicio de Matrículas
├── memory_storage.py           # Almacenamiento en memoria
├── start_services.py           # Script para iniciar servicios
├── requirements.txt            # Dependencias Python
├── templates/                  # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── students.html
│   ├── courses.html
│   ├── enrollments.html
│   └── error.html
└── README.md
```

## Instalación y Ejecución

### 1. Crear y activar entorno virtual

```bash
# Crear entorno virtual
python -m venv soa_env

# Activar (Windows PowerShell)
soa_env\Scripts\Activate.ps1

# Activar (Windows CMD)
soa_env\Scripts\activate.bat

# Activar (Linux/Mac)
source soa_env/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el sistema

```bash
python start_services.py
```

### 4. Acceder a la aplicación

- **Interfaz Web**: <http://localhost:5000>

### 5. Desactivar entorno (al terminar)

```bash
deactivate
```
