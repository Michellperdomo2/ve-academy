from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import BadgeCriteria, ChallengeType, RewardKind, Skill
from app.schemas.common import ORMModel


class BadgeBrief(ORMModel):
    id: int
    code: str
    name: str
    icon: str


class ChallengeBrief(ORMModel):
    id: int
    title: str
    icon: str
    points_reward: int


class LevelRead(ORMModel):
    id: int
    number: int
    name: str
    min_points: int
    icon: str


class BadgeWrite(BaseModel):
    code: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=2, max_length=255)
    icon: str = Field(min_length=1, max_length=16)
    criteria_type: BadgeCriteria
    criteria_value: int = Field(gt=0)
    criteria_skill: Skill | None = None
    points_bonus: int = Field(default=0, ge=0, le=100)
    is_active: bool = True


class BadgeRead(ORMModel):
    id: int
    code: str
    name: str
    description: str
    icon: str
    criteria_type: BadgeCriteria
    criteria_value: int
    criteria_skill: Skill | None
    points_bonus: int
    is_active: bool


class StudentBadgeRead(BaseModel):
    badge: BadgeRead
    earned: bool
    awarded_at: datetime | None
    progress: int
    target: int


class ChallengeWrite(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=2, max_length=255)
    icon: str = Field(min_length=1, max_length=16)
    challenge_type: ChallengeType
    target: int = Field(gt=0, le=100)
    skill: Skill | None = None
    points_reward: int = Field(default=10, ge=1, le=200)
    is_active: bool = True


class ChallengeRead(ORMModel):
    id: int
    title: str
    description: str
    icon: str
    challenge_type: ChallengeType
    target: int
    skill: Skill | None
    points_reward: int
    is_active: bool


class StudentChallengeRead(BaseModel):
    challenge: ChallengeRead
    progress: int
    completed: bool
    completed_at: datetime | None


class RewardRead(BaseModel):
    id: int
    code: str
    name: str
    kind: RewardKind
    icon: str
    required_level: int
    unlocked: bool


class PointTransactionRead(ORMModel):
    id: int
    amount: int
    reason: str
    description: str
    created_at: datetime
