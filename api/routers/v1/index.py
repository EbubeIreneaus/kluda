from fastapi import APIRouter
from .auth import router as AuthRouter
from .stores import router as StoresRouter
from .members import router as MembersRouter
from .products import router as ProductsRouter
from .customers import router as CustomersRouter, router_debt as DebtorsRouter
from .sales import router as SalesRouter
from .notifications import router as NotificationsRouter
from .subscriptions import router as SubscriptionsRouter
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
from .admin.plans import router as AdminPlanRouter
from .admin.subscriptions import router as AdminSubscriptionRouter
from .admin.webhook import router as InboundWebhookRouter
from .admin.faqs import router as AdminFaqRouter
from .faqs import router as FaqRouter
from .audit import router as StoreAuditRouter


router = APIRouter(prefix="/v1")

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(AdminAuthRouter)
admin_router.include_router(AdminTeamRouter)
admin_router.include_router(AdminPlanRouter)
admin_router.include_router(AdminSubscriptionRouter)
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
admin_router.include_router(AdminFaqRouter)
admin_router.include_router(InboundWebhookRouter)
router.include_router(admin_router)

router.include_router(AuthRouter, tags=["Authentication"])
router.include_router(StoresRouter, tags=["Store Management"])
router.include_router(MembersRouter, tags=["Store Members & Staff"])
router.include_router(ProductsRouter, tags=["Products & Inventory"])
router.include_router(CustomersRouter, tags=["Customers"])
router.include_router(DebtorsRouter, tags=["Debt Management"])
router.include_router(SalesRouter, tags=["Sales & POS"])
router.include_router(NotificationsRouter, tags=["Notifications"])
router.include_router(SubscriptionsRouter, tags=["Subscriptions & Billing"])
router.include_router(SSORouter, tags=["SSO"])
router.include_router(FaqRouter, tags=["FAQs"])
router.include_router(StoreAuditRouter, tags=["Store Audit Logs"])
router.include_router(InboundWebhookRouter)