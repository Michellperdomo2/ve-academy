"""Catálogo de categorías, lecturas y actividades (consulta y administración)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import (
    Activity,
    AnswerOption,
    Attempt,
    Category,
    Question,
    Reading,
    ReadingParagraph,
    ReadingSession,
    User,
)
from app.models.enums import ActivityType, ComprehensionLevel, ReadingLength, Skill
from app.repositories.content_repository import ActivityRepository, CategoryRepository, ReadingRepository
from app.schemas.common import Page
from app.schemas.content import (
    ActivityAdminDetail,
    ActivityDetail,
    ActivitySummary,
    ActivityWrite,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    OptionAdmin,
    OptionPublic,
    ParagraphRead,
    QuestionAdmin,
    QuestionPublic,
    ReadingDetail,
    ReadingSummary,
    ReadingWrite,
)
from app.services.utils import length_for_words, slugify


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoryRepository(db)

    def list(self) -> list[Category]:
        return self.repo.list_all()

    def get(self, category_id: int) -> Category:
        c = self.repo.get(category_id)
        if not c:
            raise NotFoundError("Categoría no encontrada.")
        return c

    def create(self, data: CategoryCreate) -> Category:
        slug = slugify(data.name)
        if self.repo.by_slug(slug):
            raise ConflictError("Ya existe una categoría con ese nombre.")
        c = Category(slug=slug, **data.model_dump())
        self.repo.add(c)
        self.db.commit()
        return c

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        c = self.get(category_id)
        fields = data.model_dump(exclude_unset=True)
        if "name" in fields and fields["name"]:
            slug = slugify(fields["name"])
            other = self.repo.by_slug(slug)
            if other and other.id != c.id:
                raise ConflictError("Ya existe una categoría con ese nombre.")
            c.slug = slug
        for k, v in fields.items():
            setattr(c, k, v)
        self.db.commit()
        return c

    def delete(self, category_id: int) -> None:
        c = self.get(category_id)
        if self.repo.in_use(c.id):
            raise ConflictError("La categoría tiene lecturas asociadas.")
        self.repo.delete(c)
        self.db.commit()


def _unique_slug(base: str, exists) -> str:
    slug, n = base, 2
    while exists(slug):
        slug, n = f"{base}-{n}", n + 1
    return slug


class ReadingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReadingRepository(db)
        self.categories = CategoryService(db)

    @staticmethod
    def to_summary(r: Reading, completed: set[int] | None = None) -> ReadingSummary:
        return ReadingSummary(
            id=r.id, title=r.title, slug=r.slug, summary=r.summary, category=CategoryRead.model_validate(r.category),
            difficulty=r.difficulty, min_age=r.min_age, max_age=r.max_age, length=r.length,
            comprehension_focus=r.comprehension_focus, cover_emoji=r.cover_emoji, cover_color=r.cover_color,
            is_published=r.is_published, word_count=r.word_count,
            completed_by_me=(r.id in completed) if completed is not None else None,
        )

    def to_detail(self, r: Reading, completed: set[int] | None, published_only: bool) -> ReadingDetail:
        acts = [a.id for a in sorted(r.activities, key=lambda a: a.id) if a.is_published or not published_only]
        return ReadingDetail(
            **self.to_summary(r, completed).model_dump(),
            paragraphs=[ParagraphRead.model_validate(p) for p in r.paragraphs],
            activity_ids=acts, created_at=r.created_at, updated_at=r.updated_at,
        )

    def search(
        self, *, published_only: bool, page: int, size: int, completed: set[int] | None = None,
        category_id: int | None = None, difficulty: int | None = None, age: int | None = None,
        length: ReadingLength | None = None, comprehension: ComprehensionLevel | None = None, q: str | None = None,
    ) -> Page[ReadingSummary]:
        stmt = self.repo.search_stmt(
            published_only=published_only, category_id=category_id, difficulty=difficulty, age=age,
            length=length, comprehension=comprehension, q=q,
        )
        items, total = self.repo.paginate(stmt, page, size)
        return Page(items=[self.to_summary(r, completed) for r in items], total=total, page=page, size=size)

    def get(self, reading_id: int, published_only: bool) -> Reading:
        r = self.repo.get_full(reading_id)
        if not r or (published_only and not r.is_published):
            raise NotFoundError("Lectura no encontrada.")
        return r

    def _apply(self, r: Reading, data: ReadingWrite) -> None:
        self.categories.get(data.category_id)
        r.title = data.title.strip()
        r.summary = data.summary.strip()
        r.category_id = data.category_id
        r.difficulty = data.difficulty
        r.min_age, r.max_age = data.min_age, data.max_age
        r.comprehension_focus = data.comprehension_focus
        r.cover_emoji, r.cover_color = data.cover_emoji, data.cover_color
        r.is_published = data.is_published
        r.paragraphs.clear()
        self.db.flush()
        for i, p in enumerate(data.paragraphs, start=1):
            r.paragraphs.append(ReadingParagraph(position=i, text=p.text.strip(), illustration=p.illustration, image_url=p.image_url))
        r.length = length_for_words(sum(len(p.text.split()) for p in data.paragraphs))

    def create(self, actor: User, data: ReadingWrite) -> Reading:
        r = Reading(slug=_unique_slug(slugify(data.title), lambda s: self.repo.by_slug(s) is not None), created_by_id=actor.id)
        self._apply(r, data)
        self.repo.add(r)
        self.db.commit()
        return self.get(r.id, published_only=False)

    def update(self, reading_id: int, data: ReadingWrite) -> Reading:
        r = self.get(reading_id, published_only=False)
        self._apply(r, data)
        self.db.commit()
        return self.get(r.id, published_only=False)

    def delete(self, reading_id: int) -> None:
        r = self.get(reading_id, published_only=False)
        has_history = self.db.scalar(select(func.count(ReadingSession.id)).where(ReadingSession.reading_id == r.id))
        if has_history:
            raise ConflictError("Esta lectura ya tiene historial de estudiantes. Despublícala en lugar de eliminarla.")
        self.repo.delete(r)
        self.db.commit()


class ActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ActivityRepository(db)
        self.readings = ReadingRepository(db)

    @staticmethod
    def to_summary(a: Activity, best: dict[int, float] | None = None) -> ActivitySummary:
        return ActivitySummary(
            id=a.id, title=a.title, slug=a.slug, activity_type=a.activity_type, skill=a.skill,
            difficulty=a.difficulty, instructions=a.instructions, icon=a.icon, points_reward=a.points_reward,
            reading_id=a.reading_id, is_published=a.is_published, question_count=len(a.questions),
            best_score=best.get(a.id) if best is not None else None,
        )

    def to_public(self, a: Activity, best: dict[int, float] | None = None) -> ActivityDetail:
        return ActivityDetail(
            **self.to_summary(a, best).model_dump(),
            reading_title=a.reading.title if a.reading else None,
            questions=[
                QuestionPublic(
                    id=q.id, position=q.position, prompt=q.prompt, prompt_illustration=q.prompt_illustration,
                    question_type=q.question_type, skill=q.skill, has_hint=bool(q.hint),
                    # Las opciones de ordenamiento se entregan en orden de "position" (desordenado a propósito).
                    options=[OptionPublic(id=o.id, text=o.text, illustration=o.illustration) for o in q.options],
                )
                for q in a.questions
            ],
        )

    def to_admin(self, a: Activity) -> ActivityAdminDetail:
        return ActivityAdminDetail(
            **self.to_summary(a).model_dump(),
            reading_title=a.reading.title if a.reading else None,
            attempt_count=self._attempt_count(a.id),
            questions=[
                QuestionAdmin(
                    id=q.id, position=q.position, prompt=q.prompt, prompt_illustration=q.prompt_illustration,
                    question_type=q.question_type, skill=q.skill, hint=q.hint, explanation=q.explanation,
                    options=[
                        OptionAdmin(id=o.id, text=o.text, illustration=o.illustration, is_correct=o.is_correct, correct_position=o.correct_position)
                        for o in q.options
                    ],
                )
                for q in a.questions
            ],
        )

    def search(
        self, *, published_only: bool, page: int, size: int, best: dict[int, float] | None = None,
        activity_type: ActivityType | None = None, skill: Skill | None = None,
        difficulty: int | None = None, reading_id: int | None = None,
    ) -> Page[ActivitySummary]:
        stmt = self.repo.search_stmt(
            published_only=published_only, activity_type=activity_type, skill=skill,
            difficulty=difficulty, reading_id=reading_id,
        )
        items, total = self.repo.paginate(stmt, page, size)
        return Page(items=[self.to_summary(a, best) for a in items], total=total, page=page, size=size)

    def get(self, activity_id: int, published_only: bool) -> Activity:
        a = self.repo.get_full(activity_id)
        if not a or (published_only and not a.is_published):
            raise NotFoundError("Actividad no encontrada.")
        return a

    def _attempt_count(self, activity_id: int) -> int:
        return self.db.scalar(select(func.count(Attempt.id)).where(Attempt.activity_id == activity_id)) or 0

    def _has_attempts(self, activity_id: int) -> bool:
        return self._attempt_count(activity_id) > 0

    def _apply_meta(self, a: Activity, data: ActivityWrite) -> None:
        if data.reading_id is not None and not self.readings.get(data.reading_id):
            raise NotFoundError("La lectura asociada no existe.")
        a.title = data.title.strip()
        a.activity_type, a.skill, a.difficulty = data.activity_type, data.skill, data.difficulty
        a.instructions, a.icon, a.points_reward = data.instructions.strip(), data.icon, data.points_reward
        a.reading_id, a.is_published = data.reading_id, data.is_published

    def _apply_questions(self, a: Activity, data: ActivityWrite) -> None:
        a.questions.clear()
        self.db.flush()
        for qi, q in enumerate(data.questions, start=1):
            question = Question(
                position=qi, prompt=q.prompt.strip(), prompt_illustration=q.prompt_illustration,
                question_type=q.question_type, skill=q.skill, hint=q.hint, explanation=q.explanation,
            )
            for oi, o in enumerate(q.options, start=1):
                question.options.append(
                    AnswerOption(position=oi, text=o.text.strip(), illustration=o.illustration,
                                 is_correct=o.is_correct, correct_position=o.correct_position)
                )
            a.questions.append(question)

    def create(self, actor: User, data: ActivityWrite) -> Activity:
        a = Activity(slug=_unique_slug(slugify(data.title), lambda s: self.repo.by_slug(s) is not None), created_by_id=actor.id)
        self._apply_meta(a, data)
        self._apply_questions(a, data)
        self.repo.add(a)
        self.db.commit()
        return self.get(a.id, published_only=False)

    def update(self, activity_id: int, data: ActivityWrite) -> Activity:
        """Si ya hay intentos, solo se actualizan los metadatos para preservar el historial."""
        a = self.get(activity_id, published_only=False)
        self._apply_meta(a, data)
        if self._has_attempts(a.id):
            current = [(q.prompt, q.question_type, q.skill, [(o.text, o.is_correct, o.correct_position) for o in q.options]) for q in a.questions]
            incoming = [(q.prompt.strip(), q.question_type, q.skill, [(o.text.strip(), o.is_correct, o.correct_position) for o in q.options]) for q in data.questions]
            if current != incoming:
                self.db.rollback()
                raise ConflictError(
                    "La actividad ya tiene intentos registrados; no se pueden cambiar sus preguntas. "
                    "Crea una nueva actividad o despublica esta."
                )
            for q, qd in zip(a.questions, data.questions, strict=True):
                q.hint, q.explanation, q.prompt_illustration = qd.hint, qd.explanation, qd.prompt_illustration
        else:
            self._apply_questions(a, data)
        self.db.commit()
        return self.get(a.id, published_only=False)

    def delete(self, activity_id: int) -> None:
        a = self.get(activity_id, published_only=False)
        if self._has_attempts(a.id):
            raise ConflictError("Esta actividad tiene intentos registrados. Despublícala en lugar de eliminarla.")
        self.repo.delete(a)
        self.db.commit()
