"""Parse knocker request settings."""

from __future__ import annotations

import re
import uuid

from marshmallow import INCLUDE, Schema, ValidationError, fields, post_load, validate

from . import config

SCHEMA_RE = re.compile("^https?://")


class RequestConfigSchema(Schema):
    """Serialize/deserialize knocker requests."""

    host = fields.String(required=True, data_key="knocker-host")
    scheme = fields.String(
        load_default=config.SCHEME,
        validate=validate.OneOf(["https", "http"]),
        data_key="knocker-scheme",
    )

    callback = fields.URL(
        allow_none=True,
        load_default=None,
        data_key="knocker-callback",
    )

    id = fields.String(data_key="knocker-id", load_default=lambda: uuid.uuid4().hex)

    timeout = fields.Float(
        load_default=config.TIMEOUT,
        validate=validate.Range(0, config.TIMEOUT_MAX),
        data_key="knocker-timeout",
    )

    retries = fields.Int(
        load_default=config.RETRIES,
        validate=validate.Range(0, config.RETRIES_MAX),
        data_key="knocker-retries",
    )

    backoff_factor = fields.Float(
        load_default=config.RETRIES_BACKOFF_FACTOR,
        validate=validate.Range(0, config.RETRIES_BACKOFF_FACTOR_MAX),
        data_key="knocker-backoff-factor",
    )

    @post_load
    def fix_host(self, data: dict, **_: dict) -> dict:
        """Clean a host and ensure that it is allowed."""
        data["host"] = SCHEMA_RE.sub("", data["host"])
        if config.HOSTS_ONLY and data["host"] not in config.HOSTS_ONLY:
            msg = "Host '%s' is not in allowed hosts: %s"
            raise ValidationError(msg, field_name="knocker-host")

        return data


request_config_schema = RequestConfigSchema(unknown=INCLUDE)
