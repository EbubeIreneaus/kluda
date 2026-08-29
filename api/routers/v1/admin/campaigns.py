import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.email import EmailCampaign
from models.admin.user import Admin
from schemas.admin.email import EmailCampaignCreate, EmailCampaignResponse, EmailCampaignStatus
from schemas.admin.user import AdminPermission
from libs.deps import require_admin_permission
from libs.audit import record_audit_log
from libs.cloudinary import cloudinary_uploader
from setting import settings
from worker.config import get_arq_pool


router = APIRouter(prefix="/campaigns", tags=["Admin Email Campaigns"])


@router.get("", response_model=list[EmailCampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    result = await db.scalars(select(EmailCampaign).order_by(EmailCampaign.created_at.desc()))
    return result.all()


@router.post("", response_model=EmailCampaignResponse)
async def create_campaign(
    payload: EmailCampaignCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    new_campaign = EmailCampaign(
        title=payload.title,
        subject=payload.subject,
        sender=payload.sender,
        body=payload.body,
        status=EmailCampaignStatus.DRAFT,
        target_audience=payload.target_audience,
        scheduled_at=payload.scheduled_at,
    )
    db.add(new_campaign)
    await db.flush()
    await db.refresh(new_campaign)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="CAMPAIGN_CREATED",
        target_type="campaign",
        target_id=new_campaign.campaign_id,
        details={"title": new_campaign.title},
    )
    return new_campaign


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    campaign = await db.scalar(select(EmailCampaign).where(EmailCampaign.campaign_id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    campaign.status = EmailCampaignStatus.SENDING
    await db.flush()

    arq_pool = await get_arq_pool()
    if arq_pool:
        await arq_pool.enqueue_job("send_admin_email_campaign", str(campaign.campaign_id))

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="CAMPAIGN_SENT",
        target_type="campaign",
        target_id=campaign.campaign_id,
    )
    return {"status": "ok", "message": "Campaign enqueued for delivery"}


@router.post("/media/upload")
async def upload_campaign_image(
    file: UploadFile = File(...),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    contents = await file.read()
    folder_name = getattr(settings, "IMAGE_FOLDER", "kluda")
    upload_res = cloudinary_uploader.upload(
        contents,
        folder=f"{folder_name}/campaigns",
        resource_type="auto",
    )
    secure_url = upload_res.get("secure_url") or upload_res.get("url")
    return {"status": "ok", "url": secure_url}
