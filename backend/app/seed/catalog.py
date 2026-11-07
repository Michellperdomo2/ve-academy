"""Catálogo base de gamificación: roles, niveles, recompensas, insignias y retos."""

ROLES = [
    ("admin", "Administrador", "Gestiona usuarios, contenidos y estadísticas generales."),
    ("teacher", "Docente", "Gestiona sus aulas y hace seguimiento a sus estudiantes."),
    ("guardian", "Acudiente", "Padre, madre o acudiente: acompaña el progreso de sus niños."),
    ("student", "Estudiante", "Niño o niña de primer grado que lee y juega aprendiendo."),
]

LEVELS = [
    (1, "Semillita lectora", 0, "🌱"),
    (2, "Brote lector", 40, "🌿"),
    (3, "Explorador de cuentos", 100, "🧭"),
    (4, "Aventurero de palabras", 200, "🚀"),
    (5, "Gran lector", 350, "🦉"),
    (6, "Maestro de historias", 550, "👑"),
]

# (code, name, kind, icon, required_level)
REWARDS = [
    ("owl", "Búho sabio", "avatar", "🦉", 1),
    ("cat", "Gatito", "avatar", "🐱", 1),
    ("dog", "Perrito", "avatar", "🐶", 1),
    ("bunny", "Conejita", "avatar", "🐰", 2),
    ("fox", "Zorrito", "avatar", "🦊", 2),
    ("panda", "Panda", "avatar", "🐼", 3),
    ("lion", "León", "avatar", "🦁", 3),
    ("unicorn", "Unicornio", "avatar", "🦄", 4),
    ("dragon", "Dragón amigable", "avatar", "🐉", 5),
    ("astronaut", "Astronauta", "avatar", "🧑‍🚀", 6),
    ("rainbow", "Arcoíris", "sticker", "🌈", 2),
    ("balloon", "Globo", "sticker", "🎈", 3),
    ("train", "Tren", "sticker", "🚂", 4),
    ("castle", "Castillo", "sticker", "🏰", 5),
    ("star", "Estrella brillante", "sticker", "🌟", 6),
]

# (code, name, description, icon, criteria_type, value, skill, bonus)
BADGES = [
    ("primer_cuento", "Primer cuento", "Terminaste tu primera lectura.", "📖", "readings_completed", 1, None, 5),
    ("lector_curioso", "Lector curioso", "Terminaste 5 lecturas diferentes.", "🐛", "readings_completed", 5, None, 10),
    ("explorador", "Explorador", "Completaste 3 actividades diferentes.", "🧭", "activities_completed", 3, None, 5),
    ("campeon_actividades", "Campeón de actividades", "Completaste 10 actividades diferentes.", "🏆", "activities_completed", 10, None, 15),
    ("estrella_perfecta", "Estrella perfecta", "Respondiste toda una actividad bien a la primera.", "⭐", "perfect_scores", 1, None, 5),
    ("super_estrella", "Súper estrella", "Lograste 5 actividades perfectas.", "🌟", "perfect_scores", 5, None, 15),
    ("cazador_silabas", "Cazador de sílabas", "10 respuestas correctas de sílabas y rimas.", "🔤", "skill_correct_answers", 10, "phonological_awareness", 10),
    ("detective_lector", "Detective lector", "5 respuestas correctas de comprensión inferencial.", "🔍", "skill_correct_answers", 5, "inferential", 10),
    ("pensador", "Pequeño pensador", "5 respuestas correctas de comprensión crítica.", "💭", "skill_correct_answers", 5, "critical", 10),
    ("coleccionista", "Coleccionista de puntos", "Reuniste 100 puntos.", "💎", "total_points", 100, None, 10),
]

# (title, description, icon, type, target, skill, points)
CHALLENGES = [
    ("Tres cuentos", "Lee 3 cuentos diferentes.", "📚", "complete_readings", 3, None, 15),
    ("Cinco aventuras", "Completa 5 actividades diferentes.", "🎯", "complete_activities", 5, None, 20),
    ("Doble perfecto", "Consigue 2 actividades perfectas.", "✨", "perfect_scores", 2, None, 15),
    ("Juego de sílabas", "Acierta 8 preguntas de sílabas o rimas.", "🧩", "skill_practice", 8, "phonological_awareness", 10),
]

CATEGORIES = [
    ("Animales", "Historias de animales y mascotas.", "🐾"),
    ("Naturaleza", "Plantas, ríos, el clima y el cuidado del ambiente.", "🌳"),
    ("Familia y amigos", "Historias de casa, familia y amistad.", "👨‍👩‍👧"),
    ("Escuela", "Aventuras en el colegio.", "🏫"),
    ("Imaginación", "Cuentos de fantasía y mundos mágicos.", "✨"),
]
