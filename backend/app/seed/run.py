"""Carga idempotente de datos iniciales.

Uso:  python -m app.seed.run

- Siempre: roles, niveles, recompensas, insignias, retos (catálogo del sistema).
- SEED_CONTENT=true: categorías, lecturas y actividades originales.
- ADMIN_PASSWORD definido: crea el administrador inicial si no existe.
- SEED_DEMO_USERS=true: crea un docente, un acudiente y dos estudiantes de demostración
  SIN progreso inventado (el progreso solo se genera usando la aplicación).
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    Activity,
    AnswerOption,
    Badge,
    Category,
    Challenge,
    Classroom,
    GuardianStudent,
    Level,
    Question,
    Reading,
    ReadingParagraph,
    Reward,
    Role,
    StudentProfile,
    User,
)
from app.models.enums import (
    ActivityType,
    BadgeCriteria,
    ChallengeType,
    ComprehensionLevel,
    QuestionType,
    RewardKind,
    RoleCode,
    Skill,
)
from app.seed.activities import ACTIVITIES
from app.seed.catalog import BADGES, CATEGORIES, CHALLENGES, LEVELS, REWARDS, ROLES
from app.seed.readings import READINGS
from app.services.utils import length_for_words, slugify

logger = logging.getLogger("ve_academy.seed")


def seed_catalog(db: Session) -> None:
    for code, name, desc in ROLES:
        if not db.scalar(select(Role).where(Role.code == RoleCode(code))):
            db.add(Role(code=RoleCode(code), name=name, description=desc))
    for number, name, min_points, icon in LEVELS:
        if not db.scalar(select(Level).where(Level.number == number)):
            db.add(Level(number=number, name=name, min_points=min_points, icon=icon))
    for code, name, kind, icon, lvl in REWARDS:
        if not db.scalar(select(Reward).where(Reward.code == code)):
            db.add(Reward(code=code, name=name, kind=RewardKind(kind), icon=icon, required_level=lvl))
    for code, name, desc, icon, ctype, value, skill, bonus in BADGES:
        if not db.scalar(select(Badge).where(Badge.code == code)):
            db.add(Badge(code=code, name=name, description=desc, icon=icon, criteria_type=BadgeCriteria(ctype),
                         criteria_value=value, criteria_skill=Skill(skill) if skill else None, points_bonus=bonus))
    for title, desc, icon, ctype, target, skill, points in CHALLENGES:
        if not db.scalar(select(Challenge).where(Challenge.title == title)):
            db.add(Challenge(title=title, description=desc, icon=icon, challenge_type=ChallengeType(ctype),
                             target=target, skill=Skill(skill) if skill else None, points_reward=points))
    db.commit()


def _build_question(position: int, raw: tuple) -> Question:
    if raw[0] == "ordering":
        _, prompt, ill, skill, hint, expl, options = raw
        q = Question(position=position, prompt=prompt, prompt_illustration=ill, question_type=QuestionType.ORDERING,
                     skill=Skill(skill), hint=hint, explanation=expl)
        for i, (text, o_ill, correct_pos) in enumerate(options, start=1):
            q.options.append(AnswerOption(position=i, text=text, illustration=o_ill, correct_position=correct_pos))
        return q
    prompt, ill, skill, hint, expl, options = raw
    q = Question(position=position, prompt=prompt, prompt_illustration=ill, question_type=QuestionType.SINGLE_CHOICE,
                 skill=Skill(skill), hint=hint, explanation=expl)
    for i, (text, o_ill, correct) in enumerate(options, start=1):
        q.options.append(AnswerOption(position=i, text=text, illustration=o_ill, is_correct=correct))
    return q


def seed_content(db: Session) -> None:
    cats: dict[str, Category] = {}
    for name, desc, icon in CATEGORIES:
        cat = db.scalar(select(Category).where(Category.slug == slugify(name)))
        if not cat:
            cat = Category(name=name, slug=slugify(name), description=desc, icon=icon)
            db.add(cat)
            db.flush()
        cats[name] = cat

    for data in READINGS:
        slug = slugify(data["title"])
        if db.scalar(select(Reading).where(Reading.slug == slug)):
            continue
        words = sum(len(t.split()) for t, _ in data["paragraphs"])
        reading = Reading(
            title=data["title"], slug=slug, summary=data["summary"], category_id=cats[data["category"]].id,
            difficulty=data["difficulty"], min_age=data["min_age"], max_age=data["max_age"],
            length=length_for_words(words), comprehension_focus=ComprehensionLevel(data["focus"]),
            cover_emoji=data["cover_emoji"], cover_color=data["cover_color"],
        )
        for i, (text, ill) in enumerate(data["paragraphs"], start=1):
            reading.paragraphs.append(ReadingParagraph(position=i, text=text, illustration=ill))
        db.add(reading)
        db.flush()
        activity = Activity(
            title=f"Comprendo: {data['title']}", slug=slugify(f"comprendo {data['title']}"),
            activity_type=ActivityType.READING_COMPREHENSION, skill=Skill(data["focus"]),
            difficulty=data["difficulty"], icon="📝", points_reward=15, reading_id=reading.id,
            instructions="Responde las preguntas sobre la lectura. Si lo necesitas, vuelve a leer el cuento.",
        )
        for i, raw in enumerate(data["questions"], start=1):
            activity.questions.append(_build_question(i, raw))
        db.add(activity)

    for data in ACTIVITIES:
        slug = slugify(data["title"])
        if db.scalar(select(Activity).where(Activity.slug == slug)):
            continue
        activity = Activity(
            title=data["title"], slug=slug, activity_type=ActivityType(data["type"]), skill=Skill(data["skill"]),
            difficulty=data["difficulty"], icon=data["icon"], points_reward=data["points"],
            instructions=data["instructions"],
        )
        for i, raw in enumerate(data["questions"], start=1):
            activity.questions.append(_build_question(i, raw))
        db.add(activity)
    db.commit()


def _role(db: Session, code: RoleCode) -> Role:
    role = db.scalar(select(Role).where(Role.code == code))
    assert role is not None
    return role


def seed_admin(db: Session) -> None:
    s = get_settings()
    if not s.ADMIN_PASSWORD:
        logger.warning("ADMIN_PASSWORD no definido: no se crea el administrador inicial.")
        return
    if db.scalar(select(User).where(User.username == s.ADMIN_USERNAME)):
        return
    db.add(User(username=s.ADMIN_USERNAME, email=s.ADMIN_EMAIL, full_name="Administrador V&E",
                password_hash=hash_password(s.ADMIN_PASSWORD), role=_role(db, RoleCode.ADMIN)))
    db.commit()
    logger.info("Administrador '%s' creado.", s.ADMIN_USERNAME)


DEMO_PASSWORDS = {"docente.demo": "Docente123", "acudiente.demo": "Acudiente123", "sofia.demo": "lectura1", "mateo.demo": "lectura1"}


def seed_demo_users(db: Session) -> None:
    if db.scalar(select(User).where(User.username == "docente.demo")):
        return
    teacher = User(username="docente.demo", email="docente.demo@example.com", full_name="Docente Demo",
                   password_hash=hash_password(DEMO_PASSWORDS["docente.demo"]), role=_role(db, RoleCode.TEACHER))
    guardian = User(username="acudiente.demo", email="acudiente.demo@example.com", full_name="Acudiente Demo",
                    password_hash=hash_password(DEMO_PASSWORDS["acudiente.demo"]), role=_role(db, RoleCode.GUARDIAN))
    db.add_all([teacher, guardian])
    db.flush()
    classroom = Classroom(name="Primero A", grade="Primero", school_year=date.today().year,
                          institution="Institución educativa de demostración", teacher_id=teacher.id)
    db.add(classroom)
    db.flush()
    student_role = _role(db, RoleCode.STUDENT)
    for username, name, avatar in (("sofia.demo", "Sofía", "owl"), ("mateo.demo", "Mateo", "dog")):
        user = User(username=username, full_name=name, password_hash=hash_password(DEMO_PASSWORDS[username]), role=student_role)
        db.add(user)
        db.flush()
        profile = StudentProfile(user_id=user.id, display_name=name, avatar=avatar, age=6,
                                 classroom_id=classroom.id, created_by_id=teacher.id)
        db.add(profile)
        db.flush()
        if username == "sofia.demo":
            db.add(GuardianStudent(guardian_id=guardian.id, student_id=profile.id, relationship_label="Madre"))
    db.commit()
    logger.info("Usuarios de demostración creados (sin progreso inventado).")


def run(db: Session) -> None:
    s = get_settings()
    seed_catalog(db)
    if s.SEED_CONTENT:
        seed_content(db)
    seed_admin(db)
    if s.SEED_DEMO_USERS:
        seed_demo_users(db)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with SessionLocal() as db:
        run(db)
    logger.info("Datos iniciales listos.")


if __name__ == "__main__":
    main()
