from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.setting import SystemSetting
from models.admin.user import Admin
from schemas.admin.setting import SettingItem, SettingUpdate
from schemas.admin.user import AdminPermission
from libs.deps import require_admin_permission, get_admin
from libs.audit import record_audit_log


from libs.cache import delete_cache

router = APIRouter(prefix="/settings", tags=["Admin System Settings"])


@router.get("", response_model=list[SettingItem])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    result = await db.scalars(select(SystemSetting).order_by(SystemSetting.key.asc()))
    return result.all()


@router.get("/{key}", response_model=SettingItem)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    setting = await db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return setting


@router.put("/{key}", response_model=SettingItem)
async def update_setting(
    key: str,
    payload: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SETTINGS)),
):
    setting = await db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    old_value = None

    if not setting:
        setting = SystemSetting(key=key, value=payload.value, description=payload.description)
        db.add(setting)
    else:
        old_value = setting.value
        setting.value = payload.value
        if payload.description is not None:
            setting.description = payload.description

    await db.flush()
    await db.refresh(setting)

    # Invalidate public caches when corresponding setting is updated
    if key == "platform_contact_info":
        await delete_cache("kluda:cache:public_contact_info")

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="SETTING_UPDATED",
        target_type="setting",
        details={"key": key, "old_value": old_value, "new_value": payload.value},
    )
    return setting
