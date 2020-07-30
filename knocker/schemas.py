import uuid
import re

import marshmallow as ma

from . import config


SCHEMA = re.compile('^https?://')


class RequestConfigSchema(ma.Schema):

    host = ma.fields.String(required=True, data_key='knocker-host')
    scheme = ma.fields.String(missing=config.SCHEME, validate=ma.validate.OneOf([
        'https', 'http'
    ]), data_key='knocker-scheme')

    callback = ma.fields.URL(allow_none=True, missing=None, data_key='knocker-callback')

    id = ma.fields.String(data_key='knocker-id', missing=lambda: uuid.uuid4().hex)

    timeout = ma.fields.Float(
        missing=config.TIMEOUT, validate=ma.validate.Range(0, config.TIMEOUT_MAX),
        data_key='knocker-timeout'
    )

    retries = ma.fields.Int(
        missing=config.RETRIES, validate=ma.validate.Range(0, config.RETRIES_MAX),
        data_key='knocker-retries'
    )

    backoff_factor = ma.fields.Float(
        missing=config.RETRIES_BACKOFF_FACTOR,
        validate=ma.validate.Range(0, config.RETRIES_BACKOFF_FACTOR_MAX),
        data_key='knocker-backoff-factor'
    )

    @ma.post_load
    def fix_host(self, data, **kwargs):
        data['host'] = SCHEMA.sub('', data['host'])
        return data


request_config_schema = RequestConfigSchema(unknown=ma.INCLUDE)
