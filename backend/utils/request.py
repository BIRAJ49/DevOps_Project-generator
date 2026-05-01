from ipaddress import ip_address, ip_network

from fastapi import Request

from backend.utils.config import get_settings


def _client_host(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _is_trusted_proxy(host: str) -> bool:
    try:
        client_ip = ip_address(host)
    except ValueError:
        return False

    for trusted_proxy in get_settings().trusted_proxy_ips:
        try:
            if "/" in trusted_proxy:
                if client_ip in ip_network(trusted_proxy, strict=False):
                    return True
            elif client_ip == ip_address(trusted_proxy):
                return True
        except ValueError:
            continue

    return False


def _valid_header_ip(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.split(",")[0].strip()
    try:
        ip_address(candidate)
    except ValueError:
        return None
    return candidate


def extract_client_ip(request: Request) -> str:
    client_host = _client_host(request)
    if not _is_trusted_proxy(client_host):
        return client_host

    forwarded_for = _valid_header_ip(request.headers.get("x-forwarded-for"))
    if forwarded_for:
        return forwarded_for

    real_ip = _valid_header_ip(request.headers.get("x-real-ip"))
    if real_ip:
        return real_ip

    return client_host
