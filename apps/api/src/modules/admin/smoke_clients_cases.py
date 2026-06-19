import argparse
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class SmokeResult:
    client_id: str
    case_id: str


def build_client_payload() -> dict[str, Any]:
    return {
        "name": "Cliente Local Exemplo",
        "document": "00000000000",
        "email": "cliente.local@example.test",
        "phone": "+5500000000000",
        "metadata": {"source": "local_smoke"},
    }


def build_case_payload(client_id: str) -> dict[str, Any]:
    return {
        "client_id": client_id,
        "case_type": "contract_analysis",
        "priority": "normal",
        "metadata": {"source": "local_smoke"},
    }


def assert_success(response: Any, expected_status: int) -> dict[str, Any]:
    body = response.json()
    if response.status_code != expected_status or body.get("success") is not True:
        raise RuntimeError(
            f"Unexpected response {response.status_code}: {body}"
        )

    return body


def run_smoke(
    *,
    token: str,
    base_url: str = "http://127.0.0.1:8000",
    http_client: Any | None = None,
) -> SmokeResult:
    headers = {"Authorization": f"Bearer {token}"}
    should_close = http_client is None
    client = http_client or httpx.Client(base_url=base_url, timeout=10)

    try:
        client_response = client.post(
            "/api/v1/clients",
            headers=headers,
            json=build_client_payload(),
        )
        client_body = assert_success(client_response, 201)
        client_id = client_body["data"]["id"]

        assert_success(
            client.get("/api/v1/clients", headers=headers),
            200,
        )

        case_response = client.post(
            "/api/v1/cases",
            headers=headers,
            json=build_case_payload(client_id),
        )
        case_body = assert_success(case_response, 201)
        case_id = case_body["data"]["id"]

        assert_success(
            client.get("/api/v1/cases", headers=headers),
            200,
        )

        return SmokeResult(client_id=client_id, case_id=case_id)
    finally:
        if should_close:
            client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local smoke tests for clients and cases routes."
    )
    parser.add_argument("--token", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_smoke(token=args.token, base_url=args.base_url)
    print(f"client_id={result.client_id}")
    print(f"case_id={result.case_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
