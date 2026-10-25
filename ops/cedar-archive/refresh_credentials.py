"""Use a fresh GitHub OIDC token when Google refreshes a long archive job.

The runtime token is kept only in the action's temporary, ignored credential file.
It is never written to the archive, job outputs, command arguments or logs.
"""
import json
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PROVIDER = "projects/293109622606/locations/global/workloadIdentityPools/cedar-github/providers/github"


def configure(environ):
    path = Path(environ["GOOGLE_GHA_CREDS_PATH"]).resolve()
    workspace = Path(environ["GITHUB_WORKSPACE"]).resolve()
    if path.parent != workspace or not path.name.startswith("gha-creds-"):
        raise ValueError("Expected the action's temporary credential file")
    endpoint = urlsplit(environ["ACTIONS_ID_TOKEN_REQUEST_URL"])
    if endpoint.scheme != "https" or not endpoint.hostname.endswith(".actions.githubusercontent.com"):
        raise ValueError("Expected a GitHub Actions OIDC endpoint")
    query = dict(parse_qsl(endpoint.query))
    query["audience"] = PROVIDER
    url = urlunsplit(endpoint._replace(query=urlencode(query)))
    config = {
        "type": "external_account", "audience": "//iam.googleapis.com/" + PROVIDER,
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "credential_source": {
            "url": url, "headers": {"Authorization": "Bearer " + environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]},
            "format": {"type": "json", "subject_token_field_name": "value"},
        },
    }
    path.chmod(0o600)
    path.write_text(json.dumps(config))


if __name__ == "__main__":
    configure(os.environ)
    print("Configured refreshable, job-scoped GitHub authentication.")
