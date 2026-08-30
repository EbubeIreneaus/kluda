from fastapi import APIRouter
from .business.auth import router as BusinessAuthRouter
from .business.staff import router as BusinessStaffRouter
from .business.product import router as BusinessProductRouter
from .business.customer import router as BusinessCustomerRouter, router2 as BusinessDebtorRouter
from .business.sales import router as BusinessSalesRouter
from .business.notification import router as BusinessNotificationRouter
from .owners.auth import router as OwnerAuthRouter
from .owners.staff import router as OwnerStaffRouter
from .owners.store import router as OwnerStoreRouter
from .owners.notification import router as OwnerNotificationRouter
from .sso import router as SSORouter
from .admin.auth import router as AdminAuthRouter
from .admin.admins import router as AdminTeamRouter
from .admin.mailboxes import router as AdminMailboxRouter
from .admin.stores import router as AdminStoreRouter
from .admin.merchants import router as AdminMerchantRouter
from .admin.campaigns import router as AdminCampaignRouter
from .admin.inbox import router as AdminInboxRouter
from .admin.tickets import router as AdminTicketRouter
from .admin.settings import router as AdminSettingRouter
from .admin.audit import router as AdminAuditRouter
from .admin.analytics import router as AdminAnalyticsRouter
from .admin.notifications import router as AdminNotificationRouter
from .admin.webhook import router as InboundWebhookRouter


router = APIRouter(prefix="/v1")

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(AdminAuthRouter)
admin_router.include_router(AdminTeamRouter)
admin_router.include_router(AdminMailboxRouter)
admin_router.include_router(AdminStoreRouter)
admin_router.include_router(AdminMerchantRouter)
admin_router.include_router(AdminCampaignRouter)
admin_router.include_router(AdminInboxRouter)
admin_router.include_router(AdminTicketRouter)
admin_router.include_router(AdminSettingRouter)
admin_router.include_router(AdminAuditRouter)
admin_router.include_router(AdminAnalyticsRouter)
admin_router.include_router(AdminNotificationRouter)
admin_router.include_router(InboundWebhookRouter)
router.include_router(admin_router)

router.include_router(OwnerAuthRouter, tags=["User Authentication"])
router.include_router(OwnerStaffRouter, tags=["Staff - User"])
router.include_router(OwnerStoreRouter, tags=["Stock - User"])
router.include_router(OwnerNotificationRouter, tags=['Owner Notifications'])
router.include_router(SSORouter, tags=["SSO"])
router.include_router(InboundWebhookRouter)

router.include_router(BusinessAuthRouter, tags=["Staff Authentication"])
router.include_router(BusinessStaffRouter, tags=['Staff'])
router.include_router(BusinessProductRouter, tags=['Stock'])
router.include_router(BusinessCustomerRouter, tags=['Customer'])
router.include_router(BusinessDebtorRouter, tags=['Debt'])
router.include_router(BusinessSalesRouter, tags=['Sales'])
router.include_router(BusinessNotificationRouter, tags=['Staff Notifications'])