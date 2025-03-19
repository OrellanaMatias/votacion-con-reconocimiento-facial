# Sistema de Votación con Reconocimiento Facial

Un sistema avanzado de votación que utiliza reconocimiento facial para garantizar la integridad y seguridad del proceso electoral en entornos educativos. Ideal para elecciones de representantes estudiantiles, consejos escolares y otros procesos de votación que requieran verificación de identidad.

## Características Principales

- 🔐 Autenticación biométrica mediante reconocimiento facial
- 🚫 Sistema anti-fraude con prevención de votos duplicados
- 📊 Panel de administración intuitivo
- 📈 Visualización de resultados en tiempo real
- 🌐 Funcionamiento local sin necesidad de conexión a internet
- 👥 Gestión de estudiantes y candidatos
- 📅 Programación de elecciones con fechas específicas

## Requisitos Previos

- Python 3.8 o superior
- Cámara web funcional
- Navegador web moderno (Chrome, Firefox, Edge)
- 2GB de RAM mínimo
- 500MB de espacio en disco

## Tecnologías Utilizadas

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5.1.3 para el diseño responsivo
- Face-api.js para el reconocimiento facial
- Flatpickr para la selección de fechas

### Backend
- Python 3.8+
- Flask como framework web
- SQLite para la base de datos
- Bibliotecas Python (ver requirements.txt)

## Instalación

1. **Preparación del Entorno**
   ```bash
   # Clonar el repositorio
   git clone [URL_del_repositorio]
   cd votacion

   # Crear y activar entorno virtual
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

2. **Instalación de Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuración Inicial**
   - Verificar que la carpeta `/database` existe
   - Asegurar permisos de escritura en `/static/faces`
   - Configurar credenciales de administrador en `config.py` (si existe)

4. **Iniciar la Aplicación**
   ```bash
   python app.py
   ```

5. **Acceder al Sistema**
   - Abrir navegador web
   - Acceder a: `http://localhost:5000`

## Guía de Uso

### Panel de Administración
1. Acceder a `/admin`
   - Usuario predeterminado: admin
   - Contraseña predeterminada: admin
2. Funciones principales:
   - Crear/editar elecciones
   - Gestionar candidatos
   - Administrar estudiantes
   - Monitorear votaciones
   - Ver estadísticas

### Proceso de Votación
1. Acceder a la página principal
2. Permitir acceso a la cámara web
3. Completar verificación facial
4. Seleccionar candidato
5. Confirmar voto

## Seguridad

- Los datos biométricos se procesan localmente
- No se almacenan imágenes faciales completas
- Acceso restringido al panel de administración
- Registros de auditoría de todas las acciones

## Solución de Problemas

### Problemas Comunes
1. **Error de Cámara Web**
   - Verificar permisos del navegador
   - Comprobar conexión de la cámara
   - Actualizar drivers si es necesario

2. **Fallo en Reconocimiento Facial**
   - Mejorar iluminación
   - Ajustar posición de la cámara
   - Verificar calidad de imagen

3. **Errores de Base de Datos**
   - Verificar permisos de escritura
   - Comprobar integridad de la base de datos

## Desarrollo

### Estructura del Proyecto
```
/votacion
├── app.py           # Aplicación principal
├── database/        # Base de datos SQLite
├── static/          # Archivos estáticos
│   ├── css/         # Estilos
│   ├── images/      # Imágenes
│   └── faces/       # Datos biométricos
├── templates/       # Plantillas HTML
└── requirements.txt # Dependencias
```
