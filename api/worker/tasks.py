import asyncio
import json
import time
import uuid
import email
import email.utils
from email.policy import default
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select, delete, func
from pywebpush import webpush, WebPushException
import structlog
from setting import settings
from models.config import LocalSession
from models.user import UserNotificationSubscription, User, UserSession, StoreMember
from models.business import Store
from models.stock import Sale
from libs.resend import fetch_resend_email_details, download_raw_email

logger = structlog.get_logger()


def _execute_webpush(sub_info: dict, payload: dict) -> bool:
    if not webpush:
        return False
    try:
        webpush(
            subscription_info=sub_info,
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL},
            timeout=5
        )
        return True
    except WebPushException as ex:
        response_code = getattr(ex.response, "status_code", None) if hasattr(ex, "response") else None
        if response_code in (404, 410):
            return False
        return False
    except Exception:
        return False


async def send_push_notification(ctx: dict, sub_info: dict, payload: dict) -> bool:
    return await asyncio.to_thread(_execute_webpush, sub_info, payload)


async def notify_staff_store(
    ctx: dict,
    store_id: str,
    title: str,
    body: str,
    data: dict | None = None
):
    payload = {"title": title, "body": body, "data": data or {}}
    async with LocalSession() as db:
        target_store_id = uuid.UUID(str(store_id))
        store_res = await db.execute(select(Store).where(Store.store_id == target_store_id))
        store = store_res.scalar_one_or_none()

        user_ids = set()
        if store and store.user_id:
            user_ids.add(store.user_id)

        member_res = await db.execute(select(StoreMember.user_id).where(StoreMember.store_id == target_store_id))
        for m_uid in member_res.scalars().all():
            user_ids.add(m_uid)

        for uid in user_ids:
            await notify_user_personal(ctx, str(uid), title, body, data)


async def notify_user_personal(
    ctx: dict,
    user_id: str,
    title: str,
    body: str,
    data: dict | None = None
):
    payload = {"title": title, "body": body, "data": data or {}}
    async with LocalSession() as db:
        uid = uuid.UUID(str(user_id))
        stmt = select(UserNotificationSubscription).where(
            UserNotificationSubscription.user_id == uid
        )
        res = await db.execute(stmt)
        subs = res.scalars().all()

        dead_subs = []
        for sub in subs:
            success = await send_push_notification(ctx, sub.sub_info, payload)
            if not success:
                dead_subs.append(sub.id)

        if dead_subs:
            await db.execute(
                delete(UserNotificationSubscription).where(
                    UserNotificationSubscription.id.in_(dead_subs)
                )
            )
            await db.commit()


async def notify_low_stock(
    ctx: dict,
    store_id: str,
    product_name: str,
    current_stock: int,
    min_stock: int
):
    title = "Low Stock Alert"
    body = f"{product_name} is running low ({current_stock} remaining, minimum: {min_stock})."
    data = {
        "type": "low_stock",
        "store_id": str(store_id),
        "product_name": product_name,
        "current_stock": current_stock,
        "min_stock": min_stock,
    }
    await notify_staff_store(ctx, store_id, title, body, data)


async def send_customer_sms_receipt(
    ctx: dict,
    customer_phone: str,
    sale_id: str,
    receipt_data: dict
):
    await asyncio.sleep(0.01)


async def generate_eod_report(ctx: dict, store_id: str, date_str: str):
    await asyncio.sleep(0.01)


async def log_security_audit_event(
    ctx: dict,
    user_id: str | None,
    action: str,
    ip_address: str,
    user_agent: str,
    metadata: dict | None = None
):
    await asyncio.sleep(0.01)


async def cron_cleanup_expired_sessions(ctx: dict):
    now = datetime.now(timezone.utc)
    async with LocalSession() as db:
        await db.execute(
            delete(UserSession).where(UserSession.expired_at < now)
        )
        await db.commit()


async def send_admin_email_campaign(ctx: dict, campaign_id_str: str):
    from models.admin.email import EmailCampaign, EmailCampaignStatus
    from libs.resend import resend_client
    async with LocalSession() as db:
        cid = uuid.UUID(campaign_id_str)
        campaign = await db.scalar(select(EmailCampaign).where(EmailCampaign.campaign_id == cid))
        if not campaign:
            return

        target = campaign.target_audience or "all_merchants"
        recipients_set = set()

        if target in ["all_merchants", "all", "all_users"]:
            users = (await db.scalars(select(User.email).where(User.status == "ACTIVE"))).all()
            for u in users:
                if u:
                    recipients_set.add(u)
        elif target == "all_staff":
            staff_emails = (
                await db.scalars(
                    select(User.email)
                    .join(StoreMember, StoreMember.user_id == User.user_id)
                    .where(StoreMember.status == "ACTIVE")
                )
            ).all()
            for s in staff_emails:
                if s:
                    recipients_set.add(s)
        elif target.startswith("specific_store:"):
            store_id_str = target.split(":", 1)[1]
            try:
                sid = uuid.UUID(store_id_str)
                st = await db.scalar(select(Store).where(Store.store_id == sid))
                if st and st.user_id:
                    owner = await db.scalar(select(User).where(User.user_id == st.user_id))
                    if owner and owner.email:
                        recipients_set.add(owner.email)
                m_emails = (
                    await db.scalars(
                        select(User.email)
                        .join(StoreMember, StoreMember.user_id == User.user_id)
                        .where(StoreMember.store_id == sid, StoreMember.status == "ACTIVE")
                    )
                ).all()
                for me in m_emails:
                    if me:
                        recipients_set.add(me)
            except Exception:
                pass
        elif "@" in target:
            for item in target.split(","):
                clean = item.strip()
                if clean and "@" in clean:
                    recipients_set.add(clean)

        recipients = list(recipients_set)
        campaign.total_recipients = len(recipients)

        from libs.email_template import render_branded_email
        final_html = campaign.body if "<!DOCTYPE html>" in campaign.body else render_branded_email(campaign.subject, campaign.body)

        for r_email in recipients:
            try:
                resend_client.Emails.send({
                    "from": campaign.sender,
                    "to": [r_email],
                    "subject": campaign.subject,
                    "html": final_html,
                })
                delivered += 1
            except Exception:
                failed += 1

        campaign.total_delivered = delivered
        campaign.total_failed = failed
        campaign.status = EmailCampaignStatus.SENT if delivered > 0 else EmailCampaignStatus.FAILED
        campaign.sent_at = datetime.now(timezone.utc)
        await db.commit()


async def send_auth_reset_email(ctx: dict, recipient_email: str, otp_code: str, account_type: str = "Admin"):
    from libs.resend import resend_client
    if not hasattr(settings, "RESEND_API_KEY") or not settings.RESEND_API_KEY:
        return

    domain = settings.DOMAIN_NAME
    sender = "Kluda Security <onboarding@resend.dev>" if "localhost" in domain else f"Kluda Security <security@{domain}>"

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 540px; margin: 0 auto; padding: 32px 24px; background: #09090b; color: #f4f4f5; border-radius: 16px; border: 1px solid #27272a;">
        <div style="margin-bottom: 24px; text-align: center;">
            <div style="display: inline-block; width: 44px; height: 44px; line-height: 44px; border-radius: 12px; background: #10b981; color: #09090b; font-size: 22px; font-weight: 900;">K</div>
            <h2 style="color: #ffffff; margin: 16px 0 4px 0; font-size: 20px;">Password Reset Verification</h2>
            <p style="color: #a1a1aa; font-size: 13px; margin: 0;">{account_type} Account Security</p>
        </div>
        <p style="font-size: 14px; color: #d4d4d8; line-height: 1.6;">You recently requested to reset your password. Use the verification code below to complete the reset process:</p>
        <div style="margin: 28px 0; text-align: center;">
            <span style="display: inline-block; padding: 14px 28px; font-size: 28px; font-weight: 800; letter-spacing: 6px; color: #10b981; background: #18181b; border: 1px solid #27272a; border-radius: 12px; font-family: monospace;">{otp_code}</span>
        </div>
        <p style="font-size: 12px; color: #71717a; line-height: 1.5; margin-top: 24px;">This code will expire in 15 minutes. If you did not make this request, please ignore this email or contact support immediately.</p>
    </div>
    """

    try:
        resend_client.Emails.send({
            "from": sender,
            "to": [recipient_email],
            "subject": f"Kluda {account_type} - Password Reset Code",
            "html": html_content,
        })
    except Exception:
        pass


async def process_inbound_resend_email(ctx: dict, email_id: str):
    from models.admin.email import EmailThread, EmailMessages, EmailMailbox, EmailThreadStatus
    from models.admin.user import Admin
    from schemas.admin.email import MailboxType
    email_details = await asyncio.to_thread(fetch_resend_email_details, email_id)
    if not email_details:
        return

    raw = email_details.get("raw") or {}
    raw_url = raw.get("download_url")

    mail_id = None
    in_reply_to = None
    references = None
    from_raw = email_details.get("from")
    to_raw = email_details.get("to")
    if not to_raw and email_details.get("received_for"):
        to_raw = email_details.get("received_for")

    subject = email_details.get("subject") or "(No Subject)"
    html_body = email_details.get("html") or email_details.get("text") or ""

    if raw_url:
        try:
            raw_content = await download_raw_email(raw_url)
            parsed_msg = email.message_from_string(raw_content, policy=default)
            mail_id = parsed_msg.get("Message-ID")
            in_reply_to = parsed_msg.get("In-Reply-To")
            references = parsed_msg.get("References")
            if not from_raw:
                from_raw = parsed_msg.get("From")
            if not to_raw:
                to_raw = parsed_msg.get("To")
            if not subject or subject == "(No Subject)":
                subject = parsed_msg.get("Subject") or "(No Subject)"
        except Exception:
            pass

    if not mail_id:
        mail_id = email_details.get("id") or email_details.get("email_id") or email_id

    if isinstance(from_raw, (list, tuple)) and len(from_raw) > 0:
        from_raw = from_raw[0]

    if isinstance(to_raw, (list, tuple)) and len(to_raw) > 0:
        to_raw = to_raw[0]

    from_parsed = email.utils.parseaddr(str(from_raw))[1] if from_raw else "unknown@example.com"
    to_parsed = email.utils.parseaddr(str(to_raw))[1] if to_raw else f"support@{settings.DOMAIN_NAME}"

    if not to_parsed:
        to_parsed = f"support@{settings.DOMAIN_NAME}"

    from_email = from_parsed.lower()
    to_email = to_parsed.lower()

    now = datetime.now(timezone.utc)

    async with LocalSession() as db:
        thread = None
        if in_reply_to:
            clean_in_reply = in_reply_to.strip().strip("<>").strip()
            existing_msg = await db.scalar(
                select(EmailMessages).where(
                    (EmailMessages.mail_id == clean_in_reply) |
                    (EmailMessages.mail_id == in_reply_to.strip())
                )
            )
            if existing_msg:
                thread = await db.scalar(select(EmailThread).where(EmailThread.thread_id == existing_msg.thread_id))

        mailbox = await db.scalar(select(EmailMailbox).where(EmailMailbox.email == to_email))
        if not mailbox:
            admin_match = await db.scalar(select(Admin).where(Admin.company_email == to_email))
            if admin_match:
                mailbox = EmailMailbox(
                    name=admin_match.fullname,
                    email=admin_match.company_email.lower(),
                    type=MailboxType.PERSONAL,
                    owner_admin_id=admin_match.admin_id,
                    allowed_admin_ids=[str(admin_match.admin_id)],
                )
                db.add(mailbox)
                await db.flush()
                await db.refresh(mailbox)
            else:
                mailbox = await db.scalar(
                    select(EmailMailbox)
                    .where(EmailMailbox.type == MailboxType.SHARED)
                    .order_by(EmailMailbox.id.asc())
                )

        if not thread:
            clean_subject = subject.replace("Re: ", "").replace("RE: ", "").replace("Fwd: ", "").strip()
            thread = await db.scalar(
                select(EmailThread).where(
                    EmailThread.customer_email == from_email,
                    EmailThread.subject.ilike(f"%{clean_subject}%"),
                )
            )

        if not thread:
            thread = EmailThread(
                mailbox_id=mailbox.mailbox_id if mailbox else None,
                customer_email=from_email,
                to=to_email,
                subject=subject,
                snippet=(html_body[:150] + "...") if len(html_body) > 150 else html_body,
                status=EmailThreadStatus.UNREAD,
                last_message_at=now,
            )
            db.add(thread)
            await db.flush()
            await db.refresh(thread)
        else:
            thread.snippet = (html_body[:150] + "...") if len(html_body) > 150 else html_body
            thread.status = EmailThreadStatus.UNREAD
            thread.last_message_at = now
            if not thread.mailbox_id and mailbox:
                thread.mailbox_id = mailbox.mailbox_id
            if not thread.to or thread.to == "":
                thread.to = to_email
            await db.flush()

        new_message = EmailMessages(
            thread_id=thread.thread_id,
            mail_id=mail_id.strip() if mail_id else None,
            in_reply_to=in_reply_to.strip() if in_reply_to else None,
            recipients=to_email,
            sender=from_email,
            body=html_body,
            direction="incoming",
            created_at=now,
        )
        db.add(new_message)
        await db.commit()


async def sync_outgoing_email_message_id(ctx: dict, resend_id: str):
    from models.admin.email import EmailMessages
    import resend

    if not resend_id:
        return

    message_id = None
    for _ in range(3):
        try:
            res = await asyncio.to_thread(resend.Emails.get, resend_id)
            if isinstance(res, dict):
                message_id = res.get("message_id")
            elif hasattr(res, "message_id"):
                message_id = getattr(res, "message_id")
            if message_id:
                break
        except Exception:
            pass
        await asyncio.sleep(2)

    if message_id:
        async with LocalSession() as db:
            msg = await db.scalar(
                select(EmailMessages).where(EmailMessages.resend_id == resend_id)
            )
            if msg:
                msg.mail_id = str(message_id).strip()
                await db.commit()


async def process_resend_event(ctx: dict, event_type: str, data: dict):
    from models.admin.email import EmailMessages, EmailThread
    email_id = data.get("email_id") or data.get("id")
    if not email_id:
        logger.warning("Resend event received without email_id", event_type=event_type, data=data)
        return

    logger.info("Processing Resend event", event_type=event_type, email_id=email_id)
    message_id = data.get("message_id")

    async with LocalSession() as db:
        msg = await db.scalar(
            select(EmailMessages).where(EmailMessages.resend_id == email_id)
        )
        if msg:
            if message_id and not msg.mail_id:
                msg.mail_id = str(message_id).strip()

            if event_type in ("email.bounced", "email.failed"):
                thread = await db.scalar(
                    select(EmailThread).where(EmailThread.thread_id == msg.thread_id)
                )
                if thread:
                    bounce_info = data.get("bounce", {})
                    reason = bounce_info.get("message") or "Delivery failed / bounced"
                    thread.snippet = f"[Failed: {reason[:100]}]"
                    logger.warning("Email delivery failure recorded", event_type=event_type, email_id=email_id, thread_id=str(thread.thread_id), reason=reason)

            await db.commit()
            logger.info("Resend event processed successfully", event_type=event_type, email_id=email_id, message_id=msg.mail_id)
        else:
            logger.info("No matching EmailMessages found for Resend event", event_type=event_type, email_id=email_id)


async def cron_generate_daily_metrics(ctx: dict):
    from models.admin.metric import DailyPlatformMetric
    from models.admin.ticket import SupportTicket, TicketStatus
    from models.admin.email import EmailThread, EmailThreadStatus
    from models.stock import Stock
    from schemas.business import StoreStatus
    now = datetime.now(timezone.utc)
    today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    async with LocalSession() as db:
        existing = await db.scalar(select(DailyPlatformMetric).where(DailyPlatformMetric.date == today))
        if existing:
            return

        total_merchants = await db.scalar(select(func.count(User.id))) or 0
        new_merchants = await db.scalar(select(func.count(User.id)).where(User.created_at >= today)) or 0
        total_stores = await db.scalar(select(func.count(Store.id))) or 0
        active_stores = await db.scalar(select(func.count(Store.id)).where(Store.status == StoreStatus.ACTIVE)) or 0
        total_staff = 0 #fix later
        total_products = await db.scalar(select(func.count(Stock.id))) or 0

        sales_stats = await db.execute(
            select(
                func.count(Sale.id).label("total_transactions"),
                func.coalesce(func.sum(Sale.amount_recived), 0).label("total_gmv"),
            )
        )
        s_row = sales_stats.first()
        open_tickets = await db.scalar(select(func.count(SupportTicket.id)).where(SupportTicket.status == TicketStatus.OPEN)) or 0
        unread_threads = await db.scalar(select(func.count(EmailThread.id)).where(EmailThread.status == EmailThreadStatus.UNREAD)) or 0

        metric = DailyPlatformMetric(
            date=today,
            total_merchants=total_merchants,
            new_merchants_today=new_merchants,
            total_stores=total_stores,
            active_stores=active_stores,
            total_staff=total_staff,
            total_products=total_products,
            total_transactions=s_row.total_transactions if s_row else 0,
            total_gmv=int(s_row.total_gmv) if s_row else 0,
            total_tickets_open=open_tickets,
            total_emails_unread=unread_threads,
        )
        db.add(metric)
        await db.commit()


async def send_admin_welcome_email(
    ctx: dict,
    fullname: str,
    personal_email: str,
    company_email: str,
    role_name: str,
    temp_password: str,
):
    from libs.email_template import render_branded_email
    import resend

    if not (hasattr(settings, "RESEND_API_KEY") and settings.RESEND_API_KEY):
        return

    resend.api_key = settings.RESEND_API_KEY
    admin_login_url = f"https://administration.{settings.DOMAIN_NAME}/login"

    body_content = f"""
<h2>Welcome to Kluda Operations &amp; Administration</h2>
<p>Hello <strong>{fullname}</strong>,</p>
<p>You have been assigned an administrator account on the <strong>Kluda Retail Platform</strong>.</p>

<blockquote style="margin: 16px 0; padding: 14px 18px; border-left: 4px solid #059669; background-color: #f8fafc; color: #1e293b; border-radius: 0 8px 8px 0;">
  <strong>Assigned Role:</strong> <span style="display: inline-block; background-color: #d1fae5; color: #065f46; font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">{role_name}</span>
</blockquote>

<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px;">
  <tbody>
    <tr style="border-bottom: 1px solid #e2e8f0;">
      <td style="padding: 8px 0; color: #64748b; font-weight: 600; width: 140px;">Company Login:</td>
      <td style="padding: 8px 0; font-family: monospace; font-weight: 700; color: #0f172a;">{company_email}</td>
    </tr>
    <tr style="border-bottom: 1px solid #e2e8f0;">
      <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Recovery Email:</td>
      <td style="padding: 8px 0; color: #0f172a;">{personal_email}</td>
    </tr>
    <tr>
      <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Temporary Password:</td>
      <td style="padding: 8px 0; font-family: monospace; font-weight: 700; color: #059669; font-size: 14px;">{temp_password}</td>
    </tr>
  </tbody>
</table>

<p style="margin: 24px 0 16px 0;">
  <a href="{admin_login_url}" style="display: inline-block; background-color: #059669; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 14px;">Log Into Admin Portal &rarr;</a>
</p>

<div style="margin: 16px 0; padding: 12px 16px; border-left: 4px solid #f59e0b; background-color: #fffbeb; border-radius: 0 8px 8px 0; font-size: 12px; color: #92400e;">
  <strong>Security Requirement:</strong> For account security, please sign in and set a new permanent password.
</div>
"""

    html = render_branded_email(
        subject="Welcome to Kluda Admin Portal",
        body_html=body_content,
        recipient_email=personal_email,
        recipient_name=fullname,
        action_text="Log Into Admin Portal",
        action_url=admin_login_url,
    )

    try:
        await asyncio.to_thread(
            resend.Emails.send,
            {
                "from": f"Kluda Team <team@{settings.DOMAIN_NAME}>",
                "to": [personal_email],
                "subject": "Welcome to Kluda Admin Portal",
                "html": html,
            }
        )
    except Exception:
        pass


async def send_subscription_notification_email(
    ctx,
    recipient_email: str,
    recipient_name: str,
    event_type: str,
    amount: int,
    plan_name: str,
    reference: str,
    next_renewal: str | None = None,
):
    import resend
    from libs.email_template import render_branded_email

    if not (hasattr(settings, "RESEND_API_KEY") and settings.RESEND_API_KEY):
        return

    resend.api_key = settings.RESEND_API_KEY
    # Paystack amounts are in subunit (kobo for NGN)
    formatted_amount = f"{amount:,} kobo"
    app_url = f"https://pos.{settings.DOMAIN_NAME}" if "localhost" not in settings.DOMAIN_NAME else "http://localhost:3000"

    if event_type == "payment_success":
        subject = f"Kluda - Payment Confirmed ({plan_name})"
        body_content = f"""
        <h2>Subscription Payment Confirmed</h2>
        <p>Hello {recipient_name}, your subscription payment for <strong>{plan_name}</strong> was successful.</p>
        <table class="data-table">
          <tr><th>Plan</th><td>{plan_name}</td></tr>
          <tr><th>Amount Paid</th><td>{formatted_amount}</td></tr>
          <tr><th>Reference</th><td>{reference}</td></tr>
          <tr><th>Next Renewal</th><td>{next_renewal or 'N/A'}</td></tr>
        </table>
        """
        action_text = "View Merchant Hub"
        action_url = f"{app_url}/marchant"
    else:
        subject = f"Kluda - Payment Failed ({plan_name})"
        body_content = f"""
        <h2>Subscription Payment Failed</h2>
        <p>Hello {recipient_name}, we were unable to process your payment for <strong>{plan_name}</strong>.</p>
        <table class="data-table">
          <tr><th>Plan</th><td>{plan_name}</td></tr>
          <tr><th>Attempted Amount</th><td>{formatted_amount}</td></tr>
          <tr><th>Reference</th><td>{reference}</td></tr>
        </table>
        <blockquote>Please update your payment card or ensure sufficient balance to prevent service disruption.</blockquote>
        """
        action_text = "Update Payment Method"
        action_url = f"{app_url}/settings"

    html = render_branded_email(
        subject=subject,
        body_html=body_content,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        action_text=action_text,
        action_url=action_url,
    )

    sender = "Kluda Billing <onboarding@resend.dev>" if "localhost" in settings.DOMAIN_NAME else f"Kluda Billing <billing@{settings.DOMAIN_NAME}>"

    try:
        await asyncio.to_thread(
            resend.Emails.send,
            {
                "from": sender,
                "to": [recipient_email],
                "subject": subject,
                "html": html,
            },
        )
    except Exception as exc:
        logger.error("Failed to send subscription notification email", error=str(exc), recipient=recipient_email)


async def process_paystack_webhook(ctx: dict, event_data: dict):
    from worker.config import get_arq_pool
    from models.subscription import UserSubscription
    from models.admin.plan import Plan
    from schemas.subscription import SubscriptionStatus, PaymentChannel, PlanStatus

    event = event_data.get("event")
    data = event_data.get("data", {})
    if not event or not data:
        return

    customer_data = data.get("customer") or {}
    metadata = data.get("metadata") or {}
    cust_code = customer_data.get("customer_code")
    email = customer_data.get("email")
    user_id_str = metadata.get("user_id")

    async with LocalSession() as db:
        user = None
        if user_id_str:
            try:
                uid = uuid.UUID(str(user_id_str))
                user = (await db.execute(select(User).where(User.user_id == uid))).scalar_one_or_none()
            except Exception:
                user = None

        if not user and cust_code:
            user = (await db.execute(select(User).where(User.paystack_customer_code == cust_code))).scalar_one_or_none()

        if not user and email:
            user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

        if not user:
            logger.warning("Paystack webhook received but no matching user found", paystack_event=event, email=email, customer_code=cust_code)
            return

        if cust_code and not user.paystack_customer_code:
            user.paystack_customer_code = cust_code

        auth_data = data.get("authorization")
        if isinstance(auth_data, dict) and auth_data.get("authorization_code"):
            user.paystack_authorization = auth_data

        idempotency_key = None
        if event == "charge.success":
            idempotency_key = f"charge_{data.get('reference') or data.get('id')}"
        elif event in ("invoice.payment_failed", "invoice.update"):
            idempotency_key = f"invoice_{data.get('invoice_code') or data.get('id')}"
        elif event == "subscription.create":
            idempotency_key = f"sub_create_{data.get('subscription_code') or data.get('id')}"
        elif event in ("subscription.disable", "subscription.not_renew"):
            idempotency_key = f"sub_disable_{data.get('subscription_code') or data.get('id')}"
        else:
            idempotency_key = f"{event}_{data.get('id') or data.get('reference')}"

        if idempotency_key:
            existing = (await db.execute(
                select(UserSubscription).where(UserSubscription.idempotency_key == idempotency_key)
            )).scalar_one_or_none()
            if existing:
                logger.info("Paystack webhook event already processed", idempotency_key=idempotency_key, paystack_event=event)
                return

        plan_code = None
        if isinstance(data.get("plan"), dict):
            plan_code = data.get("plan", {}).get("plan_code")
        elif isinstance(data.get("plan"), str):
            plan_code = data.get("plan")

        plan_slug = metadata.get("plan_slug")
        plan = None
        if plan_slug:
            plan = (await db.execute(select(Plan).where(Plan.slug == plan_slug))).scalar_one_or_none()
        if not plan and plan_code:
            plan = (await db.execute(select(Plan).where(Plan.paystack_planid == plan_code))).scalar_one_or_none()
        if not plan:
            plan = (await db.execute(select(Plan).where(Plan.status == PlanStatus.AVAILABLE))).scalars().first()

        sub_code = data.get("subscription_code")
        if not sub_code and isinstance(data.get("subscription"), dict):
            sub_code = data.get("subscription", {}).get("subscription_code")

        pool = await get_arq_pool()

        if event == "charge.success":
            next_payment_date_str = data.get("next_payment_date")
            next_renewal = None
            if next_payment_date_str:
                try:
                    next_renewal = datetime.fromisoformat(next_payment_date_str.replace("Z", "+00:00"))
                except Exception:
                    next_renewal = None

            if not next_renewal:
                interval_days = 365 if getattr(plan, "interval", "") == "annually" else 30
                next_renewal = datetime.now(timezone.utc) + timedelta(days=interval_days)

            new_sub = UserSubscription(
                user_id=user.user_id,
                plan_id=plan.slug if plan else "starter",
                status=SubscriptionStatus.ACTIVE,
                amount=int(data.get("amount", 0)),
                reference=data.get("reference"),
                idempotency_key=idempotency_key,
                paystack_subscription_code=sub_code,
                payment_channel=PaymentChannel.PAYSTACK,
                next_renewal=next_renewal,
            )
            db.add(new_sub)
            await db.flush()
            user.current_subscription_id = new_sub.subscription_id
            await db.commit()

            await pool.enqueue_job(
                "send_subscription_notification_email",
                recipient_email=user.email,
                recipient_name=user.fullname,
                event_type="payment_success",
                # Paystack amounts are in subunit (kobo for NGN)
                amount=int(data.get("amount", 0)),
                plan_name=plan.name if plan else "Subscription Plan",
                reference=data.get("reference") or "",
                next_renewal=next_renewal.strftime("%B %d, %Y"),
            )

            await pool.enqueue_job(
                "notify_user_personal",
                str(user.user_id),
                "Subscription Confirmed",
                f"Your subscription to {plan.name if plan else 'Kluda'} is active.",
                {
                    "type": "subscription_success",
                    "url": "/marchant",
                    "amount": int(data.get("amount", 0)),
                    "plan_slug": plan.slug if plan else "starter",
                },
            )

        elif event in ("invoice.payment_failed",):
            new_sub = UserSubscription(
                user_id=user.user_id,
                plan_id=plan.slug if plan else (user.current_subscription_id and str(user.current_subscription_id) or "starter"),
                status=SubscriptionStatus.DUE,
                amount=int(data.get("amount", 0)),
                reference=data.get("invoice_code") or data.get("reference"),
                idempotency_key=idempotency_key,
                paystack_subscription_code=sub_code,
                payment_channel=PaymentChannel.PAYSTACK,
                next_renewal=datetime.now(timezone.utc),
            )
            db.add(new_sub)
            await db.commit()

            await pool.enqueue_job(
                "send_subscription_notification_email",
                recipient_email=user.email,
                recipient_name=user.fullname,
                event_type="payment_failed",
                # Paystack amounts are in subunit (kobo for NGN)
                amount=int(data.get("amount", 0)),
                plan_name=plan.name if plan else "Subscription Plan",
                reference=data.get("invoice_code") or data.get("reference") or "",
                next_renewal=None,
            )

            await pool.enqueue_job(
                "notify_user_personal",
                str(user.user_id),
                "Subscription Payment Failed",
                f"Payment for your {plan.name if plan else 'Kluda'} subscription failed. Please update your payment method.",
                {
                    "type": "subscription_failed",
                    "url": "/settings",
                    "amount": int(data.get("amount", 0)),
                    "plan_slug": plan.slug if plan else "starter",
                },
            )

        elif event in ("subscription.disable", "subscription.not_renew"):
            if user.current_subscription_id:
                curr_sub = (await db.execute(
                    select(UserSubscription).where(UserSubscription.subscription_id == user.current_subscription_id)
                )).scalar_one_or_none()
                if curr_sub:
                    curr_sub.status = SubscriptionStatus.EXPIRED
                    await db.commit()

            await pool.enqueue_job(
                "notify_user_personal",
                str(user.user_id),
                "Subscription Deactivated",
                "Your subscription has been cancelled or deactivated.",
                {
                    "type": "subscription_disabled",
                    "url": "/marchant",
                },
            )


