from pydantic import BaseModel, EmailStr
from schemas.admin.user import AdminRole, AdminPermission, AdminStatus
from datetime import datetime
import uuid


class AdminLoginRequest(BaseModel):
    identifier: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminProfileResponse(BaseModel):
    id: int
    admin_id: uuid.UUID
    fullname: str
    company_email: str
    personal_email: str
    phone: str | None = None
    role: AdminRole
    permission: list[AdminPermission] = []
    status: AdminStatus
    last_login: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminInviteRequest(BaseModel):
    fullname: str
    personal_email: EmailStr
    phone: str | None = None
    role: AdminRole = AdminRole.MODERATOR
    permission: list[AdminPermission] = []


class AdminUpdateRequest(BaseModel):
    fullname: str | None = None
    personal_email: EmailStr | None = None
    phone: str | None = None
    role: AdminRole | None = None
    permission: list[AdminPermission] | None = None
    status: AdminStatus | None = None


class AdminForgotPasswordRequest(BaseModel):
    email: str


class AdminVerifyOTPRequest(BaseModel):
    email: str
    otp: str


class AdminResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str
