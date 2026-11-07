"""Administración de insignias y retos; consulta de niveles y estadísticas generales."""

from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.models import Badge, Challenge
from app.schemas.gamification import BadgeRead, BadgeWrite, ChallengeRead, ChallengeWrite, LevelRead
from app.schemas.learning import OverviewStats
from app.services.gamification_service import GamificationService
from app.services.stats_service import StatsService

router = APIRouter(tags=["Gamificación"])
stats = APIRouter(prefix="/stats", tags=["Estadísticas"])


@router.get("/levels", response_model=list[LevelRead])
def levels(_: CurrentUser, db: DbSession) -> list[LevelRead]:
    return [LevelRead.model_validate(lvl) for lvl in GamificationService(db).repo.levels()]


@router.get("/badges", response_model=list[BadgeRead])
def list_badges(_: AdminUser, db: DbSession) -> list[BadgeRead]:
    return [BadgeRead.model_validate(b) for b in GamificationService(db).repo.all_badges()]


@router.post("/badges", response_model=BadgeRead, status_code=status.HTTP_201_CREATED)
def create_badge(data: BadgeWrite, _: AdminUser, db: DbSession) -> BadgeRead:
    badge = Badge(**data.model_dump())
    db.add(badge)
    db.commit()
    return BadgeRead.model_validate(badge)


@router.put("/badges/{badge_id}", response_model=BadgeRead)
def update_badge(badge_id: int, data: BadgeWrite, _: AdminUser, db: DbSession) -> BadgeRead:
    badge = db.get(Badge, badge_id)
    if not badge:
        raise NotFoundError("Insignia no encontrada.")
    for k, v in data.model_dump().items():
        setattr(badge, k, v)
    db.commit()
    return BadgeRead.model_validate(badge)


@router.get("/challenges", response_model=list[ChallengeRead])
def list_challenges(_: AdminUser, db: DbSession) -> list[ChallengeRead]:
    return [ChallengeRead.model_validate(c) for c in GamificationService(db).repo.all_challenges()]


@router.post("/challenges", response_model=ChallengeRead, status_code=status.HTTP_201_CREATED)
def create_challenge(data: ChallengeWrite, _: AdminUser, db: DbSession) -> ChallengeRead:
    ch = Challenge(**data.model_dump())
    db.add(ch)
    db.commit()
    return ChallengeRead.model_validate(ch)


@router.put("/challenges/{challenge_id}", response_model=ChallengeRead)
def update_challenge(challenge_id: int, data: ChallengeWrite, _: AdminUser, db: DbSession) -> ChallengeRead:
    ch = db.get(Challenge, challenge_id)
    if not ch:
        raise NotFoundError("Reto no encontrado.")
    for k, v in data.model_dump().items():
        setattr(ch, k, v)
    db.commit()
    return ChallengeRead.model_validate(ch)


@stats.get("/overview", response_model=OverviewStats, summary="Estadísticas generales (administrador)")
def overview(_: AdminUser, db: DbSession) -> OverviewStats:
    return StatsService(db).overview()
