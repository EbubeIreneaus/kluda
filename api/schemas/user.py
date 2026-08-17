from pydantic import Field
from enum import Enum
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
import uuid


class StaffRole(str, Enum):
    STAFF = "staff"
    ADMIN = "admin"
    MANAGER = "manager"


class StaffStatus(str, Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    TERMINATED = 'terminated'

class UserStatus(str, Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    TERMINATED = 'terminated'
    DELETED = "deleted"


class StaffPermission(str, Enum):
    MANAGE_USER = "manage:user"
    MANAGE_STAFF = "manage:staff"
    VIEW_ANALYTICS = "view:analytics"
    VIEW_PRODUCT="view:product"
    MANAGE_PRODUCT = "manage:product"
    RECORD_SALES = "record:sales"
    MANAGE_ALL = "manage:all"


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

class StaffCreate(BaseModel):
    first_name: str
    last_name: str
    other_name: str | None = None
    role: str = "staff"
    email: EmailStr
    password: str
    phone: str | None = None
    permission: list[StaffPermission] = [StaffPermission.MANAGE_USER]
    status: StaffStatus = StaffStatus.ACTIVE

class StaffUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    other_name: str | None = None
    role: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    permission: list[StaffPermission] | None = None
    status: StaffStatus | None = None

class StaffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    staff_id: str
    store_id: uuid.UUID
    first_name: str
    last_name: str
    other_name: str | None = None
    role: str
    email: EmailStr
    phone: str | None = None
    permission: list[StaffPermission]
    status: StaffStatus
    last_login: datetime | None = None
    created_at: datetime

class StaffLogin(BaseModel):
    staff_id: str
    password: str

class BaseUser(BaseModel):
    fullname: str
    email: EmailStr
    phone: str | None = Field(min_length=11, max_length=15)
    

class UserCreate(BaseUser):
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class UserResponseMini(BaseUser):
    user_id: uuid.UUID
    created_at: datetime
    status: UserStatus = UserStatus.ACTIVE

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class PasswordResetEmailRequest(BaseModel):
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    email: EmailStr
    otp_token: str


class PasswordResetSubmitRequest(BaseModel):
    email: EmailStr
    otp_token: str
    new_password: str



class CustomerCreate(BaseModel):
    fullname: str | None = None
    phone: str | None = None
    address: str | None = None
    email: EmailStr
    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerUpdate(BaseModel):
    fullname: str | None = None
    phone: str | None = None
    address: str | None = None
    email: EmailStr | None = None
    status: CustomerStatus | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: uuid.UUID
    fullname: str | None = None
    phone: str | None = None
    address: str | None = None
    email: EmailStr
    status: CustomerStatus | str
    created_at: datetime


class DebtCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    amount: int
    status: str = "unpaid"
    staff_note: str | None = None


class DebtUpdate(BaseModel):
    amount: int | None = None
    status: str | None = None
    staff_note: str | None = None


class DebtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    debt_id: uuid.UUID
    customer: CustomerResponse
    amount: int
    status: str
    staff_note: str | None = None
    created_at: datetime
    updated_at: datetime