from __future__ import annotations

import logging

import boto3
from botocore.exceptions import ClientError

from src.adapters.email.base import EmailSender
from src.modules.common.pii import mask_email

logger = logging.getLogger(__name__)


class SesEmailSender(EmailSender):
    """AWS SES adapter for staging/production transactional e-mail."""

    def __init__(self, sender: str, region: str | None = None) -> None:
        self._sender = sender
        self._region = region
        self._client = boto3.client(
            "ses",
            region_name=region,
        )

    async def send(
        self,
        *,
        recipient: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        body: dict = {"Text": {"Data": text_body}}
        if html_body:
            body["Html"] = {"Data": html_body}

        try:
            response = self._client.send_email(
                Source=self._sender,
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": body,
                },
            )
            logger.info(
                "[EMAIL-SES] MessageId=%s to=%s subject=%s",
                response.get("MessageId", "unknown"),
                mask_email(recipient),
                subject,
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "Unknown")
            logger.warning(
                "[EMAIL-SES] Failed to send to %s: %s",
                mask_email(recipient),
                error_code,
            )
            raise
