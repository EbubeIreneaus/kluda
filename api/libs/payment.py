import hashlib
import hmac
from typing import Any
import httpx
from setting import settings


class PaymentException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class PaymentManager:
    def __init__(
        self,
        secret_key: str | None = None,
        public_key: str | None = None,
        base_url: str = "https://api.paystack.co",
    ):
        self.secret_key = secret_key or getattr(settings, "PAYSTACK_SECRET", "")
        self.public_key = public_key or getattr(settings, "PAYSTACK_PUBLIC", "")
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    json=json_data,
                    params=params,
                )
                data = response.json()
            except httpx.RequestError as exc:
                raise PaymentException(
                    message=f"Payment gateway connection error: {str(exc)}",
                    status_code=502,
                ) from exc
            except ValueError as exc:
                raise PaymentException(
                    message="Invalid response received from payment gateway",
                    status_code=502,
                ) from exc

            if not response.is_success or not data.get("status", False):
                error_msg = data.get("message", "Payment gateway operation failed")
                raise PaymentException(
                    message=error_msg,
                    status_code=response.status_code if not response.is_success else 400,
                    details=data,
                )

            return data

 
    async def paystack_create_user(
        self,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
    
        payload: dict[str, Any] = {"email": email}
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if phone:
            payload["phone"] = phone
        if metadata:
            payload["metadata"] = metadata

        return await self._request("POST", "/customer", json_data=payload)

    async def paystack_update_user(
        self,
        customer_code: str,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        payload: dict[str, Any] = {}
        if first_name is not None:
            payload["first_name"] = first_name
        if last_name is not None:
            payload["last_name"] = last_name
        if phone is not None:
            payload["phone"] = phone
        if metadata is not None:
            payload["metadata"] = metadata

        return await self._request("PUT", f"/customer/{customer_code}", json_data=payload)

    async def paystack_fetch_user(self, customer_code_or_email: str) -> dict[str, Any]:
        return await self._request("GET", f"/customer/{customer_code_or_email}")

    # Aliases
    paystack_create_customer = paystack_create_user
    paystack_update_customer = paystack_update_user
    paystack_fetch_customer = paystack_fetch_user

    async def paystack_create_plan(
        self,
        name: str,
        amount: int,
        interval: str = "monthly",
        description: str | None = None,
        currency: str = "NGN",
        send_invoices: bool = True,
    ) -> dict[str, Any]:
        """
        Create a subscription plan on Paystack.
        Note: amount should be in subunit (kobo for NGN).
        """
        payload: dict[str, Any] = {
            "name": name,
            "amount": amount,
            "interval": interval,
            "currency": currency,
            "send_invoices": send_invoices,
        }
        if description:
            payload["description"] = description

        return await self._request("POST", "/plan", json_data=payload)

    async def paystack_update_plan(
        self,
        plan_code_or_id: str,
        name: str | None = None,
        amount: int | None = None,
        interval: str | None = None,
        description: str | None = None,
        currency: str | None = None,
        send_invoices: bool | None = None,
    ) -> dict[str, Any]:

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if amount is not None:
            payload["amount"] = amount
        if interval is not None:
            payload["interval"] = interval
        if description is not None:
            payload["description"] = description
        if currency is not None:
            payload["currency"] = currency
        if send_invoices is not None:
            payload["send_invoices"] = send_invoices

        return await self._request("PUT", f"/plan/{plan_code_or_id}", json_data=payload)

    async def paystack_fetch_plan(self, plan_code_or_id: str) -> dict[str, Any]:
        """Fetch plan details from Paystack."""
        return await self._request("GET", f"/plan/{plan_code_or_id}")

    async def paystack_charge(
        self,
        authorization_code: str,
        email: str,
        amount: int,
        reference: str | None = None,
        currency: str = "NGN",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Charge a card using a stored reusable authorization code.
        amount should be in subunit (kobo for NGN).
        """
        payload: dict[str, Any] = {
            "authorization_code": authorization_code,
            "email": email,
            "amount": amount,
            "currency": currency,
        }
        if reference:
            payload["reference"] = reference
        if metadata:
            payload["metadata"] = metadata

        return await self._request(
            "POST", "/transaction/charge_authorization", json_data=payload
        )

    paystack_charge_authorization = paystack_charge

    async def paystack_initialize_transaction(
        self,
        email: str,
        amount: int,
        plan: str | None = None,
        reference: str | None = None,
        callback_url: str | None = None,
        channels: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Initialize a transaction for payment or subscription checkout."""
        payload: dict[str, Any] = {
            "email": email,
            "amount": amount,
        }
        if plan:
            payload["plan"] = plan
        if reference:
            payload["reference"] = reference
        if callback_url:
            payload["callback_url"] = callback_url
        if channels:
            payload["channels"] = channels
        if metadata:
            payload["metadata"] = metadata

        return await self._request("POST", "/transaction/initialize", json_data=payload)

    async def paystack_verify_transaction(self, reference: str) -> dict[str, Any]:
        return await self._request("GET", f"/transaction/verify/{reference}")

    async def paystack_create_subscription(
        self,
        customer_code: str,
        plan_code: str,
        authorization_code: str | None = None,
        start_date: str | None = None,
    ) -> dict[str, Any]:

        payload: dict[str, Any] = {
            "customer": customer_code,
            "plan": plan_code,
        }
        if authorization_code:
            payload["authorization"] = authorization_code
        if start_date:
            payload["start_date"] = start_date

        return await self._request("POST", "/subscription", json_data=payload)

    async def paystack_fetch_subscription(self, subscription_code_or_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/subscription/{subscription_code_or_id}")

    async def paystack_disable_subscription(
        self, subscription_code: str, email_token: str
    ) -> dict[str, Any]:
        payload = {
            "code": subscription_code,
            "token": email_token,
        }
        return await self._request("POST", "/subscription/disable", json_data=payload)

    async def paystack_enable_subscription(
        self, subscription_code: str, email_token: str
    ) -> dict[str, Any]:
        payload = {
            "code": subscription_code,
            "token": email_token,
        }
        return await self._request("POST", "/subscription/enable", json_data=payload)

    async def paystack_generate_subscription_link(
        self, subscription_code: str
    ) -> dict[str, Any]:
        return await self._request(
            "GET", f"/subscription/{subscription_code}/manage/link"
        )

    def verify_webhook_signature(
        self, payload_body: bytes, signature_header: str | None
    ) -> bool:
        if not signature_header or not self.secret_key:
            return False

        computed = hmac.new(
            self.secret_key.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha512,
        ).hexdigest()

        return hmac.compare_digest(computed, signature_header)


payment_manager = PaymentManager()
