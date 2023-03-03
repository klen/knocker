"""Parse knocker request settings."""

import re
import uuid

import marshmallow as ma

from . import config

SCHEMA_RE = re.compile("^https?://")


# TODO: Check callbacks
class RequestConfigSchema(ma.Schema):
    """Serialize/deserialize knocker requests."""

    host = ma.fields.String(required=True, data_key="knocker-host")
    scheme = ma.fields.String(
        load_default=config.SCHEME,
        validate=ma.validate.OneOf(["https", "http"]),
        data_key="knocker-scheme",
    )

    callback = ma.fields.URL(
        allow_none=True, load_default=None, data_key="knocker-callback"
    )

    id = ma.fields.String(data_key="knocker-id", load_default=lambda: uuid.uuid4().hex)

    timeout = ma.fields.Float(
        load_default=config.TIMEOUT,
        validate=ma.validate.Range(0, config.TIMEOUT_MAX),
        data_key="knocker-timeout",
    )

    retries = ma.fields.Int(
        load_default=config.RETRIES,
        validate=ma.validate.Range(0, config.RETRIES_MAX),
        data_key="knocker-retries",
    )

    backoff_factor = ma.fields.Float(
        load_default=config.RETRIES_BACKOFF_FACTOR,
        validate=ma.validate.Range(0, config.RETRIES_BACKOFF_FACTOR_MAX),
        data_key="knocker-backoff-factor",
    )

    #  limit = ma.fields.Int(
    #      validate=ma.validate.Range(0, 1e5),
    #      data_key='knocker-limit'
    #  )

    #  limit_period = ma.fields.Int(
    #      validate=ma.validate.Range(0, 86400),
    #      data_key='knocker-limit-period'
    #  )

    @ma.post_load
    def fix_host(self, data, **kwargs):
        """Clean a host and ensure that it is allowed."""
        data["host"] = SCHEMA_RE.sub("", data["host"])
        if config.HOSTS_ONLY and data["host"] not in config.HOSTS_ONLY:
            raise ma.ValidationError("Host is not allowed", field_name="knocker-host")

        return data


request_config_schema = RequestConfigSchema(unknown=ma.INCLUDE)
