🧩 Estándar para mensajes de commit — ProteinTrack
🔹 Estructura general
<tipo>(<área opcional>): <título breve y claro>

<descripción detallada del cambio>

🔹 Tipos de commit
Tipo	Uso recomendado
feat	Nueva funcionalidad o módulo agregado
fix	Corrección de errores o fallos
docs	Cambios en documentación (README, comentarios, etc.)
style	Cambios de formato o estilo (sin afectar lógica)
refactor	Mejora o reestructuración del código existente
test	Cambios o adición de pruebas (unitarias, conexión, etc.)
chore	Mantenimiento, dependencias, configuraciones o tareas menores
sql	Cambios en la base de datos o scripts SQL
🔹 Ejemplos

1. Actualización de SQL

sql(schema): added base measurement units table with sample inserts

Created table unidades_medida with auto-increment ID and predefined units.


2. Conexión a base de datos

feat(database): implemented PostgreSQL connection module

Added conexion.py and test_connection.py to verify database connectivity using psycopg2.


3. Documentación

docs(readme): added full project overview, features, and tech stack

Defined vision, overview, features, acknowledgments, and license for the ProteinTrack project.


4. Mantenimiento

chore(env): updated .gitignore and virtual environment settings

Moved .gitignore to project root and excluded venv directory correctly.

🔹 Reglas básicas

Usa inglés para mantener consistencia internacional.

El título debe ir en minúsculas, sin punto final y máximo 72 caracteres.

La descripción (segunda línea) puede ser en inglés o español según contexto, y debe explicar el motivo y alcance del cambio.

Se deja una línea en blanco entre el título y la descripción.