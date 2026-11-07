"""Pruebas de extremo a extremo (navegador real -> Angular -> FastAPI -> PostgreSQL).

Requisitos: la aplicación en marcha (docker compose up, o ng serve + uvicorn) con
SEED_DEMO_USERS=true y ADMIN_PASSWORD conocido.

    pip install pytest playwright && playwright install chromium
    E2E_BASE_URL=http://localhost:4200 E2E_ADMIN_PASSWORD=... pytest e2e -q
"""

import os
import re
import uuid
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright

BASE = os.environ.get("E2E_BASE_URL", "http://localhost:4200")
ADMIN_USER = os.environ.get("E2E_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("E2E_ADMIN_PASSWORD", "Admin12345!")
SHOTS = Path(os.environ.get("E2E_SCREENSHOTS", Path(__file__).parent / "screenshots"))
SHOTS.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 860}, locale="es-CO")
    pg = ctx.new_page()
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    yield pg
    ctx.close()
    assert not errors, f"Errores de JavaScript: {errors}"


def login(page: Page, user: str, password: str) -> None:
    page.goto(f"{BASE}/ingresar")
    page.fill("#username", user)
    page.fill("#password", password)
    page.click("button[type=submit]")


def shot(page: Page, name: str) -> None:
    page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=True)


def test_guard_redirects_to_login(page: Page):
    page.goto(f"{BASE}/estudiante")
    expect(page).to_have_url(re.compile(r"/ingresar"))
    shot(page, "01-login")


def test_wrong_credentials_show_error(page: Page):
    login(page, "sofia.demo", "incorrecta")
    expect(page.get_by_role("alert")).to_contain_text("incorrectos")


def test_teacher_creates_student_who_reads_and_plays(page: Page, browser):
    # 1) El docente crea un estudiante en su aula
    suffix = uuid.uuid4().hex[:4]
    username = f"e2e.{suffix}"
    name = f"Lucía {suffix}"
    login(page, "docente.demo", "Docente123")
    expect(page).to_have_url(re.compile(r"/panel$"))
    page.get_by_role("button", name="Agregar estudiante").click()
    page.fill("#dn", name)
    page.fill("#un", username)
    page.fill("#pw", "lectura1")
    page.get_by_role("button", name="Crear cuenta").click()
    expect(page.get_by_text(name)).to_be_visible()
    shot(page, "02-panel-docente")
    page.get_by_role("button", name="Cerrar sesión").click()

    # 2) El estudiante ingresa, lee un cuento y lo termina
    login(page, username, "lectura1")
    expect(page).to_have_url(re.compile(r"/estudiante$"))
    expect(page.get_by_text("¿Qué quieres hacer hoy?")).to_be_visible()
    shot(page, "03-inicio-estudiante")
    page.locator(".bottom").get_by_role("link", name=re.compile("Leer")).click()
    page.get_by_role("link", name=re.compile("El gato Tito")).click()
    expect(page.get_by_role("heading", name="El gato Tito")).to_be_visible()
    shot(page, "04-lector-cuaderno")
    page.get_by_role("button", name=re.compile("Terminé de leer")).click()
    expect(page.get_by_text("+10 ⭐")).to_be_visible()
    shot(page, "05-lectura-terminada")

    # 3) Responde las preguntas de comprensión (primera opción en cada una)
    page.get_by_role("link", name=re.compile("Responder preguntas")).click()
    for _ in range(4):
        page.locator(".option").first.click()
        expect(page.locator(".feedback")).to_be_visible()
        if page.get_by_role("button", name="Intentar otra vez").is_visible():
            page.get_by_role("button", name="Intentar otra vez").click()
            page.locator(".option").nth(1).click()
            if page.get_by_role("button", name="Intentar otra vez").is_visible():
                page.get_by_role("button", name="Intentar otra vez").click()
                page.locator(".option").nth(2).click()
        shot(page, "06-retroalimentacion")
        page.locator("button.next").click()
    expect(page.locator(".result")).to_be_visible()
    shot(page, "07-resultado-actividad")

    # 4) Actividad de ordenamiento (formar oraciones)
    page.goto(f"{BASE}/estudiante/actividades")
    page.get_by_role("link", name=re.compile("Arma la oración")).click()
    expect(page.locator(".pieces .piece").first).to_be_visible()
    for _ in range(page.locator(".pieces .piece").count()):
        page.locator(".pieces .piece").first.click()
    page.get_by_role("button", name="Comprobar").click()
    expect(page.locator(".feedback")).to_be_visible()
    shot(page, "08-ordenar")

    # 5) Logros
    page.goto(f"{BASE}/estudiante/logros")
    expect(page.get_by_text("Primer cuento")).to_be_visible()
    shot(page, "09-logros")
    page.get_by_role("tab", name=re.compile("Avatares")).click()
    page.get_by_role("button", name="Gatito").click()
    expect(page.locator(".top .avatar")).to_have_text("🐱")
    page.get_by_role("button", name="Salir").click()

    # 6) El docente ve el progreso registrado en la base de datos
    login(page, "docente.demo", "Docente123")
    page.get_by_role("link", name=re.compile(name)).click()
    expect(page.get_by_text("Lecturas completadas")).to_be_visible()
    expect(page.locator(".kpi").nth(1)).to_contain_text("1")
    expect(page.get_by_role("cell", name="Comprendo: El gato Tito")).to_be_visible()
    shot(page, "10-reporte-progreso")


def test_guardian_sees_only_linked_child(page: Page):
    login(page, "acudiente.demo", "Acudiente123")
    expect(page.get_by_role("heading", name="Mis niños")).to_be_visible()
    expect(page.locator(".student")).to_have_count(1)
    expect(page.get_by_text("Sofía")).to_be_visible()


def test_admin_manages_content(page: Page):
    login(page, ADMIN_USER, ADMIN_PASSWORD)
    expect(page.get_by_role("heading", name="Resumen general")).to_be_visible()
    expect(page.get_by_text("Propuesta futura").first).to_be_visible()
    shot(page, "11-admin-resumen")
    title = f"Cuento E2E {uuid.uuid4().hex[:4]}"
    page.goto(f"{BASE}/admin/lecturas/nueva")
    page.fill("#t", title)
    page.fill("#s", "Un cuento de prueba.")
    page.fill("#pt0", "Había una vez un sapo.")
    page.get_by_role("button", name="Guardar lectura").click()
    expect(page).to_have_url(re.compile(r"/admin/lecturas$"))
    expect(page.get_by_text(title)).to_be_visible()
    shot(page, "12-admin-lecturas")
    page.goto(f"{BASE}/admin/actividades/nueva")
    expect(page.get_by_role("heading", name="Nueva actividad")).to_be_visible()
    shot(page, "13-admin-editor-actividad")


def test_mobile_layout(browser):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    login(page, "sofia.demo", "lectura1")
    expect(page.get_by_text("¿Qué quieres hacer hoy?")).to_be_visible()
    shot(page, "14-movil-inicio")
    page.goto(f"{BASE}/estudiante/lecturas/2")
    expect(page.get_by_role("heading", name="Mi escuela")).to_be_visible()
    shot(page, "15-movil-lector")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    ctx.close()
