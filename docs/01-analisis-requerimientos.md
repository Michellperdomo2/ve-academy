# Fase 1 · Análisis de requerimientos

Fuente: *PGC V&E Academy — Prototipo de aplicación educativa para el fortalecimiento de la comprensión lectora en estudiantes de primer grado de una institución educativa urbana* (Sossa Perdomo y Velázquez Pineda, Universidad de Cundinamarca, 2025).

Convención de este documento:

- **[DOC]**: el requerimiento aparece en el documento original (se cita la sección).
- **[SOL]**: lo pidió el cliente en el enunciado de desarrollo, pero no aparece en el documento.
- **[PROP]**: es una decisión o propuesta del equipo de desarrollo para cubrir un vacío.

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Implementación |
|----|---------------|--------|----------------|
| RF-01 | Lecturas cortas graduadas por nivel de complejidad | [DOC] Introducción, 1.3 | `readings.difficulty` (1-3), catálogo con filtros |
| RF-02 | Ejercicios de comprensión literal, inferencial y crítica | [DOC] Introducción, Marco conceptual 2.1 | `questions.skill ∈ {literal, inferential, critical}`; cada lectura trae su actividad con los tres niveles |
| RF-03 | Retroalimentación inmediata ("andamiaje digital") | [DOC] Introducción, 1.2 | `POST /attempts/{id}/answers`: pista tras el 1.er error, explicación y respuesta tras el 2.º |
| RF-04 | Sílabas directas e inversas, palabras de uso frecuente | [DOC] Introducción, 2.2 | Actividades "Sílabas directas", "Sílabas inversas", "Encuentra la palabra" |
| RF-05 | Conciencia fonológica: reconocimiento silábico, rimas, segmentación | [DOC] 2.3 | Actividades de sílabas, completar palabras y rimas (`skill = phonological_awareness`) |
| RF-06 | Actividades lúdicas multimedia e interactivas | [DOC] Introducción, 1.4 | 8 tipos de actividad; ilustraciones; audio con síntesis de voz |
| RF-07 | Gamificación: puntos, niveles, recompensas, retos, retroalimentación | [DOC] 2.4, 1.4 | Libro de puntos, niveles, insignias, retos y avatares/stickers desbloqueables |
| RF-08 | Personajes animados | [DOC] 1.4 | Mascota original "Lumi" (SVG animado) |
| RF-09 | Instrucciones de voz o audio; navegación que no requiera lectura fluida | [DOC] 2.5 | Botón 🔊 en instrucciones, preguntas y párrafos; tocar una palabra la pronuncia (Web Speech API); navegación con íconos grandes |
| RF-10 | Backend con API REST para obtener contenidos, registrar el progreso y autenticar a docentes y padres | [DOC] 4.3 (Django) | API FastAPI con JWT |
| RF-11 | Panel para gestionar lecturas, actividades y preguntas | [DOC] 4.3 ("panel de administración de Django") | Módulo de administración en Angular |
| RF-12 | Base de datos con usuarios, lecturas, actividades, resultados e historial de progreso | [DOC] 4.3 (MySQL) | PostgreSQL normalizado (25 tablas) |
| RF-13 | Niño: escoger avatar, elegir contenido de lectura, ver avances | [DOC] Diagrama de clases (`Niño`) | `/me/avatar`, biblioteca, "Mis logros → Mi avance" |
| RF-14 | Padre/Docente: recibir reportes e informe de avances | [DOC] Diagrama de clases (`PadreDocente`, `ReporteProgreso`) | Reporte de progreso por estudiante y estadísticas por aula |
| RF-15 | Desarrollador: agregar contenido, actualizar el sistema | [DOC] Diagrama de clases | Rol Administrador con CRUD de contenido |
| RF-16 | Herramienta de apoyo real para docentes y familias | [DOC] Objetivos específicos | Paneles de docente y acudiente |
| RF-17 | Registro, login, logout, recuperación de contraseña, perfiles | [SOL] | Módulo de autenticación |
| RF-18 | Cuatro roles con permisos separados | [SOL] | `admin`, `teacher`, `guardian`, `student` |
| RF-19 | Catálogo filtrable por dificultad, edad, temática, extensión y tipo de comprensión | [SOL] (el [DOC] solo menciona la dificultad) | `GET /readings?difficulty&age&category_id&length&comprehension` |
| RF-20 | Actividades: identificar sílabas, reconocer palabras, formar oraciones, asociar imagen y palabra, completar palabras, ordenar secuencias, rimas, textos cortos | [SOL] (varias coinciden con el [DOC] 2.3) | `activity_type` con 8 valores |
| RF-21 | Registro de intentos, aciertos y errores, porcentaje de avance, habilidades fortalecidas o por reforzar | [SOL] (el [DOC] solo habla de "avance" y "calificación") | `attempts`, `attempt_answers` y cálculo por habilidad |
| RF-22 | Recomendaciones de refuerzo | [SOL] | Motor de recomendaciones por habilidad |
| RF-23 | Acompañante con IA | [SOL] como **propuesta futura** | Solo arquitectura, ver [05-ai-companion.md](05-ai-companion.md) |

## 2. Requerimientos no funcionales

| ID | Requerimiento | Origen |
|----|---------------|--------|
| RNF-01 | Interfaz amigable para 6-7 años: tipografía grande, colores atractivos, iconografía clara | [DOC] 2.5 |
| RNF-02 | Autonomía del niño y curva de aprendizaje tecnológico baja | [DOC] 2.5 |
| RNF-03 | Multiplataforma (Android, iOS, web) | [DOC] 4.1 (Flutter) → se cubre con web responsive [SOL] |
| RNF-04 | Control de versiones con Git, ramas por funcionalidad | [DOC] 4.5 |
| RNF-05 | Metodología iterativa con incrementos demostrables | [DOC] 4.4 (Scrum) |
| RNF-06 | Proyección de despliegue en la nube | [DOC] Fase 4 → Docker Compose [SOL] |
| RNF-07 | Seguridad: JWT, hash de contraseñas, roles, protección de datos de menores | [SOL] + Ley 1581 de 2012 [PROP] |
| RNF-08 | Pruebas automatizadas, migraciones, documentación OpenAPI | [SOL] |
| RNF-09 | Evitar comparaciones negativas entre niños | [SOL]; coherente con la motivación intrínseca del [DOC] 1.4 |

## 3. Contradicciones, ambigüedades y vacíos

| # | Hallazgo | Decisión |
|---|----------|----------|
| C-1 | **Stack tecnológico.** El documento usa Flutter + Django + XAMPP/MySQL; el enunciado exige Angular + FastAPI + PostgreSQL. | Se sigue el enunciado. Los conceptos del documento (API REST, ORM, panel de contenidos) se conservan con las nuevas tecnologías. |
| C-2 | **Aplicación móvil frente a web.** El documento habla de "aplicación móvil"; Angular produce una aplicación web. | Web *responsive* (probada a 390 px de ancho). Queda la opción de empaquetarla como PWA o con Capacitor más adelante. |
| C-3 | **Roles.** El diagrama de clases une `PadreDocente` en una sola clase y agrega `Desarrollador`; el enunciado pide Administrador, Docente, Acudiente y Estudiante. | Docente y Acudiente quedan como roles separados con permisos distintos. `Desarrollador` → `Administrador` (gestión de contenido). |
| C-4 | **Edad en `Usuario`.** El diagrama guarda la edad de todos los usuarios. | La edad solo se guarda (opcional) en el perfil del estudiante. Minimización de datos de menores. |
| C-5 | **Dos clases `ReporteProgreso`** con atributos distintos (una con `calificacion`). | Un único reporte calculado en tiempo real desde los intentos (`GET /students/{id}/progress`), sin duplicar datos. |
| C-6 | **Autenticación "de docentes y padres de familia"** (4.3): no dice cómo ingresa el niño. | El niño ingresa con usuario y contraseña sencilla. Su cuenta la crea un adulto (docente o acudiente), nunca él mismo. |
| C-7 | **Relación docente/acudiente ↔ niño no definida.** | Aulas (docente → estudiantes) y vínculo N:M acudiente ↔ estudiante, más un **código de vinculación** de un solo uso que el docente entrega al acudiente. [PROP] |
| C-8 | **Reglas de puntos, niveles y retos no definidas.** | Reglas documentadas en [03-modelo-datos.md](03-modelo-datos.md#reglas-de-negocio). [PROP] |
| C-9 | **No existe banco de lecturas.** | 8 lecturas y 17 actividades originales escritas para el proyecto, incluida una ambientada en el río Magdalena por el contexto de Girardot. [PROP] |
| C-10 | **"Inteligencia artificial básica" y "aprendizaje adaptativo"** aparecen en el póster como "tecnologías emergentes", sin especificación funcional. | No se presentan como requerimiento. El "aprendizaje adaptativo" se cubre de forma **determinista** (recomendaciones según la precisión por habilidad). La IA queda como propuesta futura. |
| C-11 | **"Instrucciones de voz o audio"** sin especificar si son audios grabados o voz sintética. | Se usa la síntesis de voz del navegador (sin costo y sin enviar datos del niño). Los audios grabados se pueden añadir después. |
| C-12 | **Objetivo "Evaluar la aceptación por parte de docentes y padres"** no es una funcionalidad del software. | Queda fuera del alcance del sistema. Los reportes y estadísticas sirven como insumo para esa evaluación. |
| C-13 | **Recuperación de contraseña** depende de un servicio de correo que el documento no menciona. | Funciona si se configura SMTP; si no, la API lo informa con honestidad. Los adultos pueden restablecer la contraseña de los niños a su cargo. |

## 4. Funcionalidades adicionales propuestas (no están en el documento)

- Código de vinculación entre acudiente y estudiante (C-7).
- Bloqueo temporal tras 5 intentos fallidos de inicio de sesión.
- Revocación de tokens al cerrar sesión (lista de revocación).
- Avatares y stickers desbloqueables por nivel (concreta las "recompensas" del documento).
- Tocar una palabra para escucharla (apoyo a la decodificación).
- Historial semanal de actividad en los reportes.
- V&E AI Companion (solo arquitectura).
