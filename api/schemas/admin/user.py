from enum import Enum as TypeEnum

class AdminStatus(str, TypeEnum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class AdminRole(str, TypeEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"


class AdminPermission(str, TypeEnum):
    MANAGE_ALL = "manage:all"
    MANAGE_ADMINS = "manage:admins"
    MANAGE_SETTINGS = "manage:settings"
    VIEW_AUDIT_LOGS = "view:audit_logs"
    MANAGE_STORES = "manage:stores"
    MANAGE_USERS = "manage:users"
    MANAGE_EMAILS = "manage:emails"
    MANAGE_SUPPORT = "manage:support"
    VIEW_ANALYTICS = "view:analytics"


