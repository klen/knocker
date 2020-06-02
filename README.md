# Knocker 0.5.0

The Knocker Service is a simple ready-to-deploy service to make HTTP calls.

[![tests](https://github.com/klen/knocker/workflows/tests/badge.svg)](https://github.com/klen/knocker/actions)

Let's imagine that your service is doing HTTP webhook calls when something
happens. And you need to be sure that the webhooks reach their destination. In
that case you may setup some kind of queue to retry the requests or use the
Knocker.

The features:

- Working as a web-service
- Usable Interface to make HTTP calls
- Configurable (timeouts, retry-policies)


## Getting started

```shell

    docker run -p 0.0.0.0:8000:8000 --name knocker horneds/knocker knocker

```

## Global Configuration

Knocker supports the ENVIRONMENT variables:

- **SCHEMA**: Default schema to make HTTP calls (`https`)

- **MAX_REDIRECTS**: Max number of allowed redirects per a call (`10`)

- **STATUS_URL**: A path to return Knocker Status (`/knocker/status`)

- **TIMEOUT**: Default timeout in seconds (`10.0`)

- **TIMEOUT_MAX**: Maximum allowed timeout in seconds (`60.0`)

- **RETRIES**: Default number of attempts to make HTTP call (`2`)

- **RETRIES_MAX**: Maximum allowed number of retries (`10`)

- **RETRIES_BACKOFF_FACTOR**: A backoff factor in seconds to apply between
  attempts after the second try (`0.5`)

- **RETRIES_BACKOFF_FACTOR_MAX**: Maximum backoff time (`60`)

## Configuration per a request

Requests parameters are passed through HTTP headers:

- **KNOCKER-HOST**: HTTP Host to make a call (required)

- **KNOCKER-SCHEMA**: HTTP Schema to make a call (optional)

- **KNOCKER-CALLBACK**: An URL to make a callback call if all attemps are failed (optional)

- **KNOCKER-TIMEOUT**: Timeout in seconds (float, optional)

- **KNOCKER-RETRIES**: Number of attempts to make HTTP call if previous one was failed (optional)

- **KNOCKER-BACKOF-FACTOR**: A backoff factor in seconds to apply between attempts after the second try


## Making a requests

Let's imagine you have a Knockout Service is running behind the URL: https://knock.myserver.com

```http
POST /webhook/?some-params=12 HTTP/1.1
Host: knock.myserver.com
Content-Type: application/json
Knocker-Host: target-server.com
Knocker-Timeout: 15.0
Knocker-Retries: 5

SOME REQUEST BODY
```

Knocker will attempt to make a `POST` request to
`https://target-server.com/webhook/?some-params=12` with the given request's
body. It will retry the request 5 times after fails (response status 4**, 5**)


## Bug tracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at https://github.com/klen/knocker/issues


## Contributing

Development of The Knocker happens at: https://github.com/klen/knocker


## Contributors

* [Kirill Klenov](https://github.com/klen)


##  License

Licensed under a MIT license (See [LICENSE](https://github.com/klen/knocker/blob/develop/LICENSE))
