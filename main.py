from fastapi import FastAPI, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import engine, get_db
import models
from services import PokemonService  # Importamos nuestro nuevo servicio

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Poke-FastAPI")
templates = Jinja2Templates(directory="templates")

# --- LOGIN EN MEMORIA (Usuario Único) ---
USER_CREDS = {"username": "admin", "password": "123"}

def is_authenticated(request: Request) -> bool:
    """Helper para verificar si la cookie de sesión existe"""
    return request.cookies.get("session_user") == USER_CREDS["username"]


# --- RUTAS DE AUTENTICACIÓN ---

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    # Si ya está logueado, mandarlo al index
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html", {"error": None})

@app.post("/login")
def login_action(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == USER_CREDS["username"] and password == USER_CREDS["password"]:
        # Credenciales correctas: redirige al index e inyecta la cookie de sesión
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_user", value=username, httponly=True)
        return response
    
    # Credenciales incorrectas
    return templates.TemplateResponse(request, "login.html", {"error": "Usuario o contraseña incorrectos"})

@app.get("/logout")
def logout_action():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("session_user") # Borramos la cookie
    return response


# --- RUTAS DE POKÉMON (PROTEGIDAS) ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Llamamos a la lógica limpia desde el servicio
    pokemons = PokemonService.get_all_saved(db)
    return templates.TemplateResponse(request, "index.html", {"pokemons": pokemons})

@app.post("/fetch-pokemon/")
async def fetch_and_save_pokemon(request: Request, pokemon_name: str = Form(...), db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Usamos el servicio asíncrono
    result = await PokemonService.fetch_and_store(pokemon_name, db)
    
    if not result["success"]:
        # Si falló, volvemos a renderizar el index pasándole el error de forma bonita
        pokemons = PokemonService.get_all_saved(db)
        return templates.TemplateResponse(request, "index.html", {"pokemons": pokemons, "error": result["error"]})

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
