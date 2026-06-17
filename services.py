from sqlalchemy.orm import Session
import httpx
import models

POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon/"

class PokemonService:
    
    @staticmethod
    def get_all_saved(db: Session):
        return db.query(models.Pokemon).all()

    @staticmethod
    async def fetch_and_store(pokemon_name: str, db: Session):
        pokemon_name = pokemon_name.lower().strip()
        
        # 1. Verificar si ya existe
        db_pokemon = db.query(models.Pokemon).filter(models.Pokemon.name == pokemon_name).first()
        if db_pokemon:
            return {"success": False, "error": "El Pokémon ya está en la base de datos"}

        # 2. Consultar la PokeAPI de forma asíncrona
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{POKEAPI_URL}{pokemon_name}")
            if response.status_code == 404:
                return {"success": False, "error": "Pokémon no encontrado en la PokeAPI"}
            data = response.json()

        # 3. Mapear y guardar
        new_pokemon = models.Pokemon(
            id=data["id"],
            name=data["name"],
            sprite=data["sprites"]["front_default"],
            type=data["types"][0]["type"]["name"]
        )
        db.add(new_pokemon)
        db.commit()
        db.refresh(new_pokemon)
        
        return {"success": True, "pokemon": new_pokemon}