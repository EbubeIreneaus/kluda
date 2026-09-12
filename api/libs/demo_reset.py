import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.business import Store
from models.user import User, Customer, Debt
from models.stock import Stock, StockHistory, Sale, SaleItem
from models.store_audit import StoreAuditLog
from models.notification import Notification
from setting import settings


async def execute_demo_reset(
    db: AsyncSession,
    store_id: uuid.UUID,
    wipe_mode: str = "sales_only",
) -> dict:
    store = await db.scalar(select(Store).where(Store.store_id == store_id))
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    owner = await db.scalar(select(User).where(User.user_id == store.user_id))
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store owner not found")

    allowed_emails = settings.demo_emails_list
    if owner.email.lower() not in allowed_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Reset is only permitted on authorized demo/pitch accounts ({', '.join(allowed_emails)}) "
                f"to protect merchant data. Account '{owner.email}' is not in the demo allowlist."
            ),
        )

    # 1. Fetch sales belonging to this store
    sale_ids = (
        await db.scalars(select(Sale.sale_id).where(Sale.store_id == store.store_id))
    ).all()

    # 2. Delete SaleItems
    if sale_ids:
        await db.execute(delete(SaleItem).where(SaleItem.sale_id.in_(sale_ids)))

    # 3. Delete Sales
    res_sales = await db.execute(delete(Sale).where(Sale.store_id == store.store_id))
    sales_deleted = res_sales.rowcount or len(sale_ids)

    # 4. Delete StockHistories
    res_history = await db.execute(
        delete(StockHistory).where(StockHistory.store_id == store.store_id)
    )
    histories_deleted = res_history.rowcount or 0

    # 5. Delete Debts for customers of this store
    customer_ids = (
        await db.scalars(select(Customer.customer_id).where(Customer.store_id == store.store_id))
    ).all()
    debts_deleted = 0
    if customer_ids:
        res_debt = await db.execute(
            delete(Debt).where(Debt.customer_id.in_([str(cid) for cid in customer_ids]))
        )
        debts_deleted = res_debt.rowcount or 0

    # 6. Delete StoreAudits
    res_audit = await db.execute(
        delete(StoreAuditLog).where(StoreAuditLog.store_id == store.store_id)
    )
    audits_deleted = res_audit.rowcount or 0

    # 7. Delete Notifications for this store
    res_notif = await db.execute(
        delete(Notification).where(Notification.target_id == store.store_id)
    )
    notifications_deleted = res_notif.rowcount or 0

    products_deleted = 0
    customers_deleted = 0

    # 8. If full_wipe, also delete products and customers
    if wipe_mode == "full_wipe":
        res_products = await db.execute(
            delete(Stock).where(Stock.store_id == store.store_id)
        )
        products_deleted = res_products.rowcount or 0

        res_customers = await db.execute(
            delete(Customer).where(Customer.store_id == store.store_id)
        )
        customers_deleted = res_customers.rowcount or len(customer_ids)

    await db.commit()

    return {
        "success": True,
        "store_id": str(store.store_id),
        "store_name": store.name,
        "owner_email": owner.email,
        "wipe_mode": wipe_mode,
        "deleted_counts": {
            "sales": sales_deleted,
            "stock_histories": histories_deleted,
            "debts": debts_deleted,
            "audits": audits_deleted,
            "notifications": notifications_deleted,
            "products": products_deleted,
            "customers": customers_deleted,
        },
        "message": (
            f"Demo store data wiped successfully ({wipe_mode}). "
            "Store is fresh and ready for merchant demonstration."
        ),
    }
