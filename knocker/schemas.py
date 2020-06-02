import marshmallow as ma

from . import config


class RequestConfigSchema(ma.Schema):

    host = ma.fields.String(required=True, data_key='knocker-host')
    schema = ma.fields.String(missing=config.SCHEMA, validate=ma.validate.OneOf([
        'https', 'http'
    ]), data_key='knocker-schema')

    callback = ma.fields.URL(allow_none=True, missing=None, data_key='knocker-callback')

    timeout = ma.fields.Float(
        missing=config.TIMEOUT, validate=ma.validate.Range(0, config.TIMEOUT_MAX),
        data_key='knocker-timeout',
    )

    retries = ma.fields.Int(
        missing=config.RETRIES, validate=ma.validate.Range(0, config.RETRIES_MAX),
        data_key='knocker-retries',
    )

    backof_factor = ma.fields.Float(
        missing=config.RETRIES_BACKOFF_FACTOR,
        validate=ma.validate.Range(0, config.RETRIES_BACKOFF_FACTOR_MAX),
        data_key='knocker-backof-factor',
    )


request_config_schema = RequestConfigSchema(unknown=ma.EXCLUDE)