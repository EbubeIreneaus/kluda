import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.email import EmailCampaign
from models.admin.user import Admin
from schemas.admin.email import (
    EmailCampaignCreate,
    EmailCampaignUpdate,
    EmailCampaignResponse,
    EmailCampaignStatus,
)
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
    send_now: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    initial_status = EmailCampaignStatus.SENDING if send_now else EmailCampaignStatus.DRAFT

    new_campaign = EmailCampaign(
        title=payload.title,
        subject=payload.subject,
        sender=payload.sender,
        body=payload.body,
        status=initial_status,
        target_audience=payload.target_audience,
        scheduled_at=payload.scheduled_at,
    )
    db.add(new_campaign)
    await db.flush()
    await db.refresh(new_campaign)

    if send_now:
        arq_pool = await get_arq_pool()
        if arq_pool:
            await arq_pool.enqueue_job("send_admin_email_campaign", str(new_campaign.campaign_id))

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="CAMPAIGN_SENT" if send_now else "CAMPAIGN_CREATED",
        target_type="campaign",
        target_id=new_campaign.campaign_id,
        details={"title": new_campaign.title, "send_now": send_now},
    )
    return new_campaign


@router.put("/{campaign_id}", response_model=EmailCampaignResponse)
async def update_campaign(
    campaign_id: uuid.UUID,
    payload: EmailCampaignUpdate,
    send_now: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    campaign = await db.scalar(select(EmailCampaign).where(EmailCampaign.campaign_id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign.status in [EmailCampaignStatus.SENDING, EmailCampaignStatus.SENT]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a campaign that has already been dispatched")

    if payload.title is not None:
        campaign.title = payload.title
    if payload.subject is not None:
        campaign.subject = payload.subject
    if payload.sender is not None:
        campaign.sender = payload.sender
    if payload.body is not None:
        campaign.body = payload.body
    if payload.target_audience is not None:
        campaign.target_audience = payload.target_audience
    if payload.scheduled_at is not None:
        campaign.scheduled_at = payload.scheduled_at

    if send_now:
        campaign.status = EmailCampaignStatus.SENDING
        await db.flush()
        arq_pool = await get_arq_pool()
        if arq_pool:
            await arq_pool.enqueue_job("send_admin_email_campaign", str(campaign.campaign_id))
    else:
        await db.flush()

    await db.refresh(campaign)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="CAMPAIGN_SENT" if send_now else "CAMPAIGN_UPDATED",
        target_type="campaign",
        target_id=campaign.campaign_id,
        details={"title": campaign.title, "send_now": send_now},
    )
    return campaign


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    campaign = await db.scalar(select(EmailCampaign).where(EmailCampaign.campaign_id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign.status == EmailCampaignStatus.SENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete an active campaign currently sending")

    await db.delete(campaign)
    await db.flush()

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="CAMPAIGN_DELETED",
        target_type="campaign",
        target_id=campaign_id,
    )
    return {"status": "ok", "message": "Campaign deleted successfully"}


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    campaign = await db.scalar(select(EmailCampaign).where(EmailCampaign.campaign_id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign.status in [EmailCampaignStatus.SENDING, EmailCampaignStatus.SENT]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign has already been sent or is currently sending")

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
