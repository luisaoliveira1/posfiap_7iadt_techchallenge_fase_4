import httpx

from src.config import get_settings


async def predict(text: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.nlp_model_url}/predict",
            json={"text": text},
        )
        resp.raise_for_status()
        return resp.json()
