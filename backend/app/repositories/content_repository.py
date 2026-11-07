from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.models import Activity, AnswerOption, Category, Question, Reading, ReadingParagraph
from app.models.enums import ActivityType, ComprehensionLevel, ReadingLength, Skill
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    def list_all(self) -> list[Category]:
        return list(self.db.scalars(select(Category).order_by(Category.name)))

    def by_slug(self, slug: str) -> Category | None:
        return self.db.scalar(select(Category).where(Category.slug == slug))

    def in_use(self, category_id: int) -> bool:
        return bool(self.db.scalar(select(func.count(Reading.id)).where(Reading.category_id == category_id)))


class ReadingRepository(BaseRepository[Reading]):
    model = Reading

    def get_full(self, reading_id: int) -> Reading | None:
        return self.db.scalar(
            select(Reading)
            .where(Reading.id == reading_id)
            .options(selectinload(Reading.paragraphs), selectinload(Reading.activities))
        )

    def by_slug(self, slug: str) -> Reading | None:
        return self.db.scalar(select(Reading).where(Reading.slug == slug))

    def search_stmt(
        self,
        *,
        published_only: bool,
        category_id: int | None = None,
        difficulty: int | None = None,
        age: int | None = None,
        length: ReadingLength | None = None,
        comprehension: ComprehensionLevel | None = None,
        q: str | None = None,
    ) -> Select:
        stmt = select(Reading).options(selectinload(Reading.paragraphs)).order_by(Reading.difficulty, Reading.title)
        if published_only:
            stmt = stmt.where(Reading.is_published.is_(True))
        if category_id:
            stmt = stmt.where(Reading.category_id == category_id)
        if difficulty:
            stmt = stmt.where(Reading.difficulty == difficulty)
        if age:
            stmt = stmt.where(Reading.min_age <= age, Reading.max_age >= age)
        if length:
            stmt = stmt.where(Reading.length == length)
        if comprehension:
            stmt = stmt.where(Reading.comprehension_focus == comprehension)
        if q:
            stmt = stmt.where(func.lower(Reading.title).like(f"%{q.lower()}%"))
        return stmt

    def count_published(self) -> int:
        return self.db.scalar(select(func.count(Reading.id)).where(Reading.is_published.is_(True))) or 0


class ActivityRepository(BaseRepository[Activity]):
    model = Activity

    def get_full(self, activity_id: int) -> Activity | None:
        return self.db.scalar(
            select(Activity)
            .where(Activity.id == activity_id)
            .options(selectinload(Activity.questions).selectinload(Question.options), selectinload(Activity.reading))
        )

    def by_slug(self, slug: str) -> Activity | None:
        return self.db.scalar(select(Activity).where(Activity.slug == slug))

    def search_stmt(
        self,
        *,
        published_only: bool,
        activity_type: ActivityType | None = None,
        skill: Skill | None = None,
        difficulty: int | None = None,
        reading_id: int | None = None,
    ) -> Select:
        stmt = select(Activity).options(selectinload(Activity.questions)).order_by(Activity.difficulty, Activity.id)
        if published_only:
            stmt = stmt.where(Activity.is_published.is_(True))
        if activity_type:
            stmt = stmt.where(Activity.activity_type == activity_type)
        if skill:
            stmt = stmt.where(Activity.skill == skill)
        if difficulty:
            stmt = stmt.where(Activity.difficulty == difficulty)
        if reading_id:
            stmt = stmt.where(Activity.reading_id == reading_id)
        return stmt

    def published_by_skill(self, skills: list[Skill]) -> list[Activity]:
        if not skills:
            return []
        stmt = (
            select(Activity)
            .join(Question, Question.activity_id == Activity.id)
            .where(Activity.is_published.is_(True), Question.skill.in_(skills))
            .distinct()
            .order_by(Activity.difficulty, Activity.id)
        )
        return list(self.db.scalars(stmt))

    def count_published(self) -> int:
        return self.db.scalar(select(func.count(Activity.id)).where(Activity.is_published.is_(True))) or 0

    def option(self, option_id: int) -> AnswerOption | None:
        return self.db.get(AnswerOption, option_id)


__all__ = ["ActivityRepository", "CategoryRepository", "ReadingRepository", "ReadingParagraph"]
