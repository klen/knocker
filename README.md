# Knocker 0.12.1

The Knocker Service is a simple ready-to-deploy service to make HTTP calls.

[![tests](https://github.com/klen/knocker/workflows/tests/badge.svg)](https://github.com/klen/knocker/actions)
[![dockerhub](https://images.microbadger.com/badges/image/horneds/knocker.svg)](https://hub.docker.com/r/horneds/knocker)

Let's imagine that your service is doing HTTP webhook calls when something
happens. And you need to be sure that the webhooks reach their destination. In
that case you may setup some kind of queue to retry the failed requests or
allow Knocker do everything for you.

The features:

- Working as a web-service
- Usable Interface to make HTTP calls
- Configurable (timeouts, retry-policies)

Public version is available here: https://knock.horneds.com


## Getting started

```shell

    docker run -p 0.0.0.0:8000:8000 --name knocker horneds/knocker knocker

```

## Making a requests

Basically, all you need to make requests with Knocker is to change URL HOST to
your Knocker Instance and put the original one into `Knocker-Host` header.

Let's imagine you have a Knockout Service is running behind the URL:
https://knock.horneds.com and you want to make a request to
https://target-server.com/webhook/?some-params=12

Request:
```http
POST /webhook/?some-params=12 HTTP/1.1
Host: knock.horneds.com
Content-Type: application/json
Knocker-Host: target-server.com
Knocker-Timeout: 15.0
Knocker-Retries: 5

"SOME REQUEST BODY"
```

Response:
```http
HTTP/1.1 200 OK
Connection: keep-alive
Content-Encoding: gzip
Content-Type: application/json
Date: Tue, 02 Jun 2020 15:10:37 GMT
Transfer-Encoding: chunked

{
    "config": {
        "backoff_factor": 0.5,
        "callback": null,
        "retries": 5,
        "timeout": 15.0,
        "id": "4498279872/4494502784",
    },
    "status": true
}
```

Knocker will attempt to make a `POST` request to
`https://target-server.com/webhook/?some-params=12` with the given request's
body. It will retry the request 5 times after fails (response status 4**, 5**)


## Global Configuration

Knocker supports the ENVIRONMENT variables:

- **SCHEME**: Default scheme to make HTTP calls (`https`)

- **MAX_REDIRECTS**: Max number of allowed redirects per a call (`10`)

- **STATUS_URL**: A path to return Knocker Status (`/knocker/status`)

- **TIMEOUT**: Default timeout in seconds (`10.0`)

- **TIMEOUT_MAX**: Maximum allowed timeout in seconds (`60.0`)

- **RETRIES**: Default number of attempts to make HTTP call (`2`)

- **RETRIES_MAX**: Maximum allowed number of retries (`10`)

- **RETRIES_BACKOFF_FACTOR**: A backoff factor in seconds to apply between
  attempts after the second try (`0.5`)

- **RETRIES_BACKOFF_FACTOR_MAX**: Maximum backoff time (`600`)

- **LOG_FILE**: `-`

- **LOG_LEVEL**: `INFO`

- **LOG_FORMAT**: `%(asctime)s %(levelname)-8s %(message)s`

## Configuration per a request

Requests parameters are passed through HTTP headers:

- **KNOCKER-HOST**: HTTP Host to make a call (required)

- **KNOCKER-SCHEME**: HTTP Scheme to make a call (optional)

- **KNOCKER-TIMEOUT**: Timeout in seconds (float, optional)

- **KNOCKER-RETRIES**: Number of attempts to make HTTP call if previous one was failed (optional)

- **KNOCKER-BACKOFF-FACTOR**: A backoff factor in seconds to apply between attempts after the second try

- **KNOCKER-CALLBACK**: An URL to make a callback call if all attemps are failed (optional)

- **KNOCKER-ID**: Custom ID for the request (optional, by default Knocker creates one by itself)


All other headers which begin from `knocker-` prefix won't be sent to a target
host but will be sent to a callback.


## Callbacks

If all Knocker's attempts to make a given request were failed and callback url
was given then Knocker will make a request to the given callback URL with
params:

```http
POST /your-callback-url
Host: origin-server.com
Content-Type: application/json

{
    "config": {
        "id": "ID", // Request ID
        // ... Request Config
    },
    "method": "GET", // Request Method
    "url": "https://target-server.com/webhook/?some-params=12 HTTP/1.1", // The URL is failed
    "status_code": 403, // Latest failed status code
}
```

## Bug tracker

If you have any suggestions, bug reports or annoyances please report them to
the issue tracker at https://github.com/klen/knocker/issues


## Contributing

Development of The Knocker happens at: https://github.com/klen/knocker


## Contributors

* [Kirill Klenov](https://github.com/klen)


##  License

Licensed under a MIT license (See [LICENSE](https://github.com/klen/knocker/blob/develop/LICENSE))
