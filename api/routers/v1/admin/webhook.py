import json
import structlog
from fastapi import APIRouter, Request, HTTPException, status
from svix.webhooks import Webhook, WebhookVerificationError
from setting import settings
from worker.config import get_arq_pool

logger = structlog.get_logger()

router = APIRouter(prefix="/webhook", tags=["Inbound Webhook"])


async def handle_webhook_payload(request: Request):
    try:
        payload = await request.body()
        headers = dict(request.headers)

        if hasattr(settings, "RESEND_SIGNING_SECRET") and settings.RESEND_SIGNING_SECRET:
            try:
                wh = Webhook(settings.RESEND_SIGNING_SECRET)
                req = wh.verify(payload, headers)
            except WebhookVerificationError as e:
                logger.error("Invalid webhook signature", error=str(e))
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")
        else:
            try:
                req = json.loads(payload.decode("utf-8"))
            except Exception as e:
                logger.warning("Failed to decode webhook JSON", error=str(e))
                req = {}

        event = req.get("type") or req.get("event")
        data = req.get("data", {})

        logger.info("Received Resend webhook", event=event)

        pool = await get_arq_pool()

        if event == "email.received":
            email_id = data.get("email_id") or data.get("id")
            if not email_id:
                logger.warning("Webhook email.received missing email_id")
                return {"success": False, "reason": "No email_id"}

            await pool.enqueue_job("process_inbound_resend_email", email_id)
            return {"success": True}

        elif event in ["email.sent", "email.delivered", "email.bounced", "email.clicked", "email.opened", "email.failed"]:
            await pool.enqueue_job("process_resend_event", event, data)
            return {"success": True}

        return {"success": True, "ignored": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing webhook", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing webhook")


@router.post("")
async def receive_webhook_root(request: Request):
    return await handle_webhook_payload(request)


@router.post("/resend")
async def receive_webhook_resend(request: Request):
    return await handle_webhook_payload(request)
