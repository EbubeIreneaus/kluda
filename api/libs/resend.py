import resend
import httpx
from setting import settings


if hasattr(settings, "RESEND_API_KEY") and settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY

resend_client = resend


def fetch_resend_email_details(email_id: str) -> dict:
    try:
        if hasattr(resend.Emails, "Receiving") and hasattr(resend.Emails.Receiving, "get"):
            return resend.Emails.Receiving.get(email_id=email_id)
        elif hasattr(resend.Emails, "get"):
            return resend.Emails.get(email_id)
        return {}
    except Exception:
        return {}


async def download_raw_email(url: str) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url)
        res.raise_for_status()
        return res.text
