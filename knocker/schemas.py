import marshmallow as ma

from . import config


class RequestConfigSchema(ma.Schema):

    host = ma.fields.String(required=True)
    scheme = ma.fields.String(missing=config.SCHEME, validate=ma.validate.OneOf([
        'https', 'http'
    ]))

    callback = ma.fields.URL(allow_none=True, missing=None)

    id = ma.fields.String()

    timeout = ma.fields.Float(
        missing=config.TIMEOUT, validate=ma.validate.Range(0, config.TIMEOUT_MAX),
    )

    retries = ma.fields.Int(
        missing=config.RETRIES, validate=ma.validate.Range(0, config.RETRIES_MAX),
    )

    backoff_factor = ma.fields.Float(
        missing=config.RETRIES_BACKOFF_FACTOR,
        validate=ma.validate.Range(0, config.RETRIES_BACKOFF_FACTOR_MAX),
    )


request_config_schema = RequestConfigSchema(unknown=ma.INCLUDE)
