import httpx

from src.config import get_settings


async def predict(label_scores: list[dict]) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.risk_engine_url}/risk",
            json={"Labels": label_scores},
        )
        resp.raise_for_status()
        return resp.json()
