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


router = APIRouter(prefix="/v1")

router.include_router(BusinessAuthRouter, tags=["Staff Authentication"])
router.include_router(BusinessStaffRouter, tags=['Staff'])
router.include_router(BusinessProductRouter, tags=['Stock'])
router.include_router(BusinessCustomerRouter, tags=['Customer'])
router.include_router(BusinessDebtorRouter, tags=['Debt'])
router.include_router(BusinessSalesRouter, tags=['Sales'])
router.include_router(BusinessNotificationRouter, tags=['Staff Notifications'])
router.include_router(OwnerAuthRouter, tags=["User Authentication"])
router.include_router(OwnerStaffRouter, tags=["Staff - User"])
router.include_router(OwnerStoreRouter, tags=["Stock - User"])
router.include_router(OwnerNotificationRouter, tags=['Owner Notifications'])
router.include_router(SSORouter, tags=["SSO"])