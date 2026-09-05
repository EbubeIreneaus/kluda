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

    VIEW_STAFF = "view:staff"
    EDIT_STAFF = "edit:staff"
    CREATE_STAFF = "create:staff"
    DELETE_STAFF = "delete:staff"
    STAFF_PERMISSION = "staff:permission"

    VIEW_ANALYTICS = "view:analytics"

    VIEW_PRODUCT = "view:product"
    EDIT_PRODUCT = "edit:product"
    CREATE_PRODUCT = "create:product"
    DELETE_PRODUCT = "delete:product"
    RESTORE_PRODUCT = "restore:product"
    ADJUST_STOCK = "adjust:stock"

    RECORD_SALES = "record:sales"
    VIEW_SALES = "view:sales"
    CANCEL_SALES = "cancel:sales"
    APPLY_DISCOUNT = "apply:discount"

    VIEW_DEBT = "view:debt"
    RECORD_DEBT = "record:debt"
    SETTLE_DEBT = "settle:debt"

    VIEW_AUDIT_LOG = "view:audit-log"

    VIEW_CUSTOMER = "view:customer"
    CREATE_CUSTOMER = "create:customer"
    EDIT_CUSTOMER = "edit:customer"
    DELETE_CUSTOMER = "delete:customer"

    VIEW_APP_SETTINGS = "view:app-settings"
    EDIT_APP_SETTINGS = "edit:app-settings"

    EXPORT_REPORT = "export:report"

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
    password: str | None = None
    phone: str | None = None
    permission: list[StaffPermission] = [StaffPermission.RECORD_SALES, StaffPermission.VIEW_PRODUCT]
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
    store_id: uuid.UUID | None = None
    first_name: str
    last_name: str
    other_name: str | None = None
    role: str
    email: EmailStr
    phone: str | None = None
    permission: list[StaffPermission]
    status: StaffStatus
    has_pin: bool = False
    pin_hash: str | None = None
    pin_salt: str | None = None
    last_login: datetime | None = None
    created_at: datetime | None = None


class StaffSetPin(BaseModel):
    pin: str = Field(min_length=4, max_length=6)


class StaffLogin(BaseModel):
    staff_id: str
    password: str

class BaseUser(BaseModel):
    fullname: str
    email: EmailStr
    phone: str | None = Field(default=None, min_length=11, max_length=15)

class BaseStaffResponse(BaseUser):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    fullname:str

class UserCreate(BaseUser):
    password: str = Field(min_length=6)

class UserRegisterWithStore(BaseModel):
    fullname: str
    email: EmailStr
    password: str = Field(min_length=6)
    phone: str | None = None
    store_name: str | None = None
    store_category: str | None = None
    store_address: str | None = None
    referral_code: str | None = None

class StoreMemberCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    other_name: str | None = None
    phone: str | None = None
    display_name: str | None = None
    role: str = "cashier"
    permission: list[StaffPermission] = [StaffPermission.RECORD_SALES, StaffPermission.VIEW_PRODUCT]
    status: StaffStatus = StaffStatus.ACTIVE

class StoreMemberUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None
    permission: list[StaffPermission] | None = None
    status: StaffStatus | None = None

class StoreMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    display_name: str | None = None
    fullname: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    permission: list[StaffPermission] = []
    status: StaffStatus
    created_at: datetime

class UserLogin(BaseModel):
    email: str | None = None
    staff_id: str | None = None
    password: str = Field(min_length=1)

class UserResponseMini(BaseUser):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    created_at: datetime
    status: UserStatus = UserStatus.ACTIVE
    referral_code: str | None = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class PasswordResetEmailRequest(BaseModel):
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    email: EmailStr
    code: str | None = None
    otp_token: str | None = None


class PasswordResetSubmitRequest(BaseModel):
    email: EmailStr
    code: str | None = None
    otp_token: str | None = None
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