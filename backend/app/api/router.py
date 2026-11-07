"""Agrega todos los routers bajo /api/v1."""

from fastapi import APIRouter

from app.routers import auth, content, gamification, me, students, system, users

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(students.classrooms)
api_router.include_router(students.students)
api_router.include_router(me.router)
api_router.include_router(content.categories)
api_router.include_router(content.readings)
api_router.include_router(content.activities)
api_router.include_router(content.attempts)
api_router.include_router(gamification.router)
api_router.include_router(gamification.stats)
