"""Lecturas realizadas, intentos de actividades, evaluación y retroalimentación inmediata."""

import random
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models import Attempt, AttemptAnswer, Question, ReadingSession, StudentProfile
from app.models.enums import AttemptStatus, PointReason, QuestionType
from app.repositories.content_repository import ActivityRepository, ReadingRepository
from app.repositories.learning_repository import AttemptRepository, ReadingSessionRepository
from app.schemas.content import ReadingCompletionResult, ReadingSessionRead
from app.schemas.gamification import BadgeBrief, ChallengeBrief, LevelRead
from app.schemas.learning import AnswerFeedback, AnswerSubmit, AttemptResult, AttemptStart
from app.services.gamification_service import GamificationService
from app.services.progress_service import ProgressService, skill_rows

FIRST_READING_POINTS = 10
REREAD_POINTS = 2
MAX_TRIES_PER_QUESTION = 2  # tras el 2.º error se muestra la respuesta y se explica

PRAISE = ["¡Muy bien!", "¡Excelente!", "¡Lo lograste!", "¡Genial!", "¡Súper!"]
ENCOURAGE = ["¡Casi! Mira la pista e inténtalo otra vez.", "¡Buen intento! Lee la pista y prueba de nuevo."]


class LearningService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sessions = ReadingSessionRepository(db)
        self.attempts = AttemptRepository(db)
        self.readings = ReadingRepository(db)
        self.activities = ActivityRepository(db)
        self.gamification = GamificationService(db)
        self.progress = ProgressService(db)

    # ---------- Lecturas ----------
    def start_reading(self, student: StudentProfile, reading_id: int) -> ReadingSession:
        reading = self.readings.get(reading_id)
        if not reading or not reading.is_published:
            raise NotFoundError("Lectura no encontrada.")
        session = ReadingSession(student_id=student.id, reading_id=reading.id)
        self.sessions.add(session)
        self.db.commit()
        return session

    def complete_reading(self, student: StudentProfile, session_id: int) -> ReadingCompletionResult:
        session = self.sessions.get(session_id)
        if not session or session.student_id != student.id:
            raise NotFoundError("Sesión de lectura no encontrada.")
        if session.completed_at is not None:
            raise ConflictError("Esta lectura ya fue registrada como terminada.")
        first_time = not self.sessions.has_completed(student.id, session.reading_id)
        points = FIRST_READING_POINTS if first_time else REREAD_POINTS
        session.completed_at = datetime.now(UTC)
        session.points_awarded = points
        self.db.flush()
        title = session.reading.title
        self.gamification.award_points(
            student.id, points, PointReason.READING_COMPLETED,
            f"{'Leíste' if first_time else 'Releíste'} «{title}»", reading_session_id=session.id,
        )
        outcome = self.gamification.evaluate(student.id)
        self.db.commit()
        acts = sorted((a for a in session.reading.activities if a.is_published), key=lambda a: a.id)
        return ReadingCompletionResult(
            session=ReadingSessionRead.model_validate(session), points_awarded=points, first_time=first_time,
            new_badges=[BadgeBrief.model_validate(b) for b in outcome.new_badges],
            completed_challenges=[ChallengeBrief.model_validate(c) for c in outcome.completed_challenges],
            next_activity_id=acts[0].id if acts else None,
        )

    # ---------- Actividades ----------
    def start_attempt(self, student: StudentProfile, activity_id: int) -> AttemptStart:
        activity = self.activities.get_full(activity_id)
        if not activity or not activity.is_published:
            raise NotFoundError("Actividad no encontrada.")
        attempt = Attempt(
            student_id=student.id, activity_id=activity.id,
            attempt_number=self.attempts.next_attempt_number(student.id, activity.id),
            total_questions=len(activity.questions), status=AttemptStatus.IN_PROGRESS,
        )
        self.attempts.add(attempt)
        self.db.commit()
        return AttemptStart(attempt_id=attempt.id, attempt_number=attempt.attempt_number, total_questions=attempt.total_questions)

    def _own_attempt(self, student: StudentProfile, attempt_id: int) -> Attempt:
        attempt = self.attempts.get_with_answers(attempt_id)
        if not attempt or attempt.student_id != student.id:
            raise NotFoundError("Intento no encontrado.")
        return attempt

    @staticmethod
    def _evaluate(question: Question, data: AnswerSubmit) -> bool:
        option_ids = {o.id for o in question.options}
        if question.question_type == QuestionType.SINGLE_CHOICE:
            if data.selected_option_id is None or data.selected_option_id not in option_ids:
                raise AppError("La opción no pertenece a esta pregunta.")
            return next(o for o in question.options if o.id == data.selected_option_id).is_correct
        ordered = data.ordered_option_ids or []
        if sorted(ordered) != sorted(option_ids):
            raise AppError("Debes ordenar todas las opciones de la pregunta.")
        expected = [o.id for o in sorted(question.options, key=lambda o: o.correct_position or 0)]
        return ordered == expected

    @staticmethod
    def _correct_ids(question: Question) -> list[int]:
        if question.question_type == QuestionType.SINGLE_CHOICE:
            return [o.id for o in question.options if o.is_correct]
        return [o.id for o in sorted(question.options, key=lambda o: o.correct_position or 0)]

    def answer(self, student: StudentProfile, attempt_id: int, data: AnswerSubmit) -> AnswerFeedback:
        attempt = self._own_attempt(student, attempt_id)
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ConflictError("Este intento ya terminó.")
        activity = self.activities.get_full(attempt.activity_id)
        assert activity is not None
        question = next((q for q in activity.questions if q.id == data.question_id), None)
        if question is None:
            raise AppError("La pregunta no pertenece a esta actividad.")
        previous = [a for a in attempt.answers if a.question_id == question.id]
        if any(a.is_correct for a in previous) or len(previous) >= MAX_TRIES_PER_QUESTION:
            raise ConflictError("Esta pregunta ya fue resuelta. ¡Pasa a la siguiente!")

        is_correct = self._evaluate(question, data)
        try_number = len(previous) + 1
        self.db.add(AttemptAnswer(
            attempt_id=attempt.id, question_id=question.id, try_number=try_number,
            selected_option_id=data.selected_option_id, ordered_option_ids=data.ordered_option_ids, is_correct=is_correct,
        ))
        self.db.commit()

        if is_correct:
            return AnswerFeedback(is_correct=True, try_number=try_number, message=random.choice(PRAISE),
                                  explanation=question.explanation, hint=None, correct_option_ids=None, can_retry=False)
        if try_number < MAX_TRIES_PER_QUESTION:
            return AnswerFeedback(is_correct=False, try_number=try_number, message=random.choice(ENCOURAGE),
                                  explanation=None, hint=question.hint or "Vuelve a leer con calma.",
                                  correct_option_ids=None, can_retry=True)
        return AnswerFeedback(is_correct=False, try_number=try_number,
                              message="¡No pasa nada! Equivocarse también es aprender. Mira la respuesta:",
                              explanation=question.explanation, hint=None,
                              correct_option_ids=self._correct_ids(question), can_retry=False)

    def finish(self, student: StudentProfile, attempt_id: int) -> AttemptResult:
        attempt = self._own_attempt(student, attempt_id)
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ConflictError("Este intento ya terminó.")
        activity = self.activities.get_full(attempt.activity_id)
        assert activity is not None
        answered = {a.question_id for a in attempt.answers}
        missing = [q.position for q in activity.questions if q.id not in answered]
        if missing:
            raise ConflictError("Aún faltan preguntas por responder.", details={"missing_positions": missing})

        correct_first = sum(1 for a in attempt.answers if a.try_number == 1 and a.is_correct)
        score = round(correct_first * 100 / attempt.total_questions, 2)
        points_before = self.gamification.total_points(student.id)
        level_before, _ = self.gamification.level_for(points_before)

        earned = round(activity.points_reward * score / 100)
        already = self.attempts.best_points_before(student.id, activity.id, attempt.id)
        awarded = max(0, earned - already)

        attempt.status = AttemptStatus.COMPLETED
        attempt.completed_at = datetime.now(UTC)
        attempt.correct_first_try = correct_first
        attempt.score = Decimal(str(score))
        attempt.points_awarded = awarded
        self.db.flush()
        self.gamification.award_points(student.id, awarded, PointReason.ACTIVITY_COMPLETED,
                                       f"Actividad «{activity.title}»", attempt_id=attempt.id)
        outcome = self.gamification.evaluate(student.id)
        level_after, _ = self.gamification.level_for(self.gamification.total_points(student.id))
        self.db.commit()

        stars = 3 if score == 100 else 2 if score >= 60 else 1
        message = {
            3: "¡Perfecto! Respondiste todo bien a la primera.",
            2: "¡Muy buen trabajo! Sigue practicando y serás un gran lector.",
            1: "¡Lo terminaste! Cada intento te hace más fuerte. Te dejamos unas actividades para practicar.",
        }[stars]
        recs = []
        if score < 80:
            wrong_skills = {next(q.skill for q in activity.questions if q.id == a.question_id)
                            for a in attempt.answers if a.try_number == 1 and not a.is_correct}
            skills = [s for s in skill_rows(self.attempts.skill_stats([student.id])) if s.skill in wrong_skills]
            for s in skills:
                s.status = "needs_support"
            recs = self.progress.recommendations(student.id, skills, exclude_activity_id=activity.id)
        return AttemptResult(
            attempt_id=attempt.id, activity_id=activity.id, status=attempt.status,
            total_questions=attempt.total_questions, correct_first_try=correct_first, score=score,
            points_awarded=awarded, message=message, stars=stars,
            new_badges=[BadgeBrief.model_validate(b) for b in outcome.new_badges],
            completed_challenges=[ChallengeBrief.model_validate(c) for c in outcome.completed_challenges],
            level_up=LevelRead.model_validate(level_after) if level_after.number > level_before.number else None,
            recommendations=recs,
        )
