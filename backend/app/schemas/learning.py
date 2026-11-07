"""Esquemas de intentos, respuestas, progreso y estadísticas."""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ActivityType, AttemptStatus, Skill
from app.schemas.gamification import BadgeBrief, ChallengeBrief, LevelRead


class AttemptStart(BaseModel):
    attempt_id: int
    attempt_number: int
    total_questions: int


class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_id: int | None = None
    ordered_option_ids: list[int] | None = Field(default=None, max_length=8)

    @model_validator(mode="after")
    def _one_answer(self) -> "AnswerSubmit":
        if (self.selected_option_id is None) == (self.ordered_option_ids is None):
            raise ValueError("Envía selected_option_id o ordered_option_ids (solo uno).")
        return self


class AnswerFeedback(BaseModel):
    """Retroalimentación inmediata tras cada respuesta."""

    is_correct: bool
    try_number: int
    message: str
    explanation: str | None = Field(description="Se muestra al acertar o tras el 2.º intento fallido")
    hint: str | None = Field(description="Pista tras el primer error")
    correct_option_ids: list[int] | None = Field(
        description="Se revela solo después del 2.º intento fallido (andamiaje, no castigo)"
    )
    can_retry: bool


class Recommendation(BaseModel):
    activity_id: int
    title: str
    icon: str
    skill: Skill
    reason: str


class AttemptResult(BaseModel):
    attempt_id: int
    activity_id: int
    status: AttemptStatus
    total_questions: int
    correct_first_try: int
    score: float
    points_awarded: int
    message: str
    stars: int = Field(ge=0, le=3)
    new_badges: list[BadgeBrief]
    completed_challenges: list[ChallengeBrief]
    level_up: LevelRead | None
    recommendations: list[Recommendation]


class AttemptHistoryItem(BaseModel):
    attempt_id: int
    activity_id: int
    activity_title: str
    activity_type: ActivityType
    skill: Skill
    attempt_number: int
    status: AttemptStatus
    score: float | None
    correct_first_try: int | None
    total_questions: int
    total_tries: int
    points_awarded: int
    started_at: datetime
    completed_at: datetime | None


class ReadingHistoryItem(BaseModel):
    session_id: int
    reading_id: int
    reading_title: str
    cover_emoji: str
    completed_at: datetime
    points_awarded: int


class SkillProgress(BaseModel):
    skill: Skill
    label: str
    answered: int
    correct_first_try: int
    accuracy: float | None
    status: str = Field(description="strong | developing | needs_support | not_started")


class ProgressSummary(BaseModel):
    student_id: int
    display_name: str
    avatar: str
    total_points: int
    level: LevelRead
    next_level: LevelRead | None
    points_to_next_level: int | None
    readings_completed: int
    readings_total: int
    activities_completed: int
    activities_total: int
    progress_percent: float
    total_attempts: int
    total_answers: int
    correct_answers: int
    incorrect_answers: int
    average_score: float | None
    badges_earned: int
    skills: list[SkillProgress]
    strengths: list[str]
    needs_support: list[str]
    recommendations: list[Recommendation]
    weekly_activity: list["DailyActivity"]


class DailyActivity(BaseModel):
    date: str
    readings: int
    activities: int
    points: int


class StudentDashboard(BaseModel):
    greeting: str
    progress: ProgressSummary
    continue_reading: list[dict]
    suggested_activities: list[dict]
    active_challenges: list[dict]
    recent_badges: list[BadgeBrief]


class OverviewStats(BaseModel):
    users_by_role: dict[str, int]
    active_students_7d: int
    readings_published: int
    activities_published: int
    reading_sessions_completed: int
    attempts_completed: int
    average_score: float | None
    skills: list[SkillProgress]
    ai_companion_enabled: bool


class ClassroomStudentRow(BaseModel):
    student_id: int
    display_name: str
    avatar: str
    total_points: int
    level_number: int
    readings_completed: int
    activities_completed: int
    average_score: float | None
    needs_support: list[str]
    last_activity_at: datetime | None


class ClassroomStats(BaseModel):
    classroom_id: int
    classroom_name: str
    student_count: int
    average_score: float | None
    skills: list[SkillProgress]
    students: list[ClassroomStudentRow]


ProgressSummary.model_rebuild()
