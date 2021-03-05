#!/usr/bin/env python3

from datetime import date
from json import dumps, loads
from subprocess import run
from sys import argv


def curl(*args):
    command = run(
        ("curl", "--unix-socket", "/opt/unit/control.unit.sock", *args),
        capture_output=True,
    )
    if "error" in loads(command.stdout.decode()):
        raise RuntimeError(f"curl command failed with: {command.stdout.decode()}")
    return command


def get(path):
    return curl(path).stdout.decode()


def put(data, path):
    curl("-X", "PUT", "--data-binary", data, path)


def delete(path):
    curl("-X", "DELETE", path)


def certs(domain):
    return sorted(
        cert
        for cert in loads(get("localhost/certificates"))
        if cert.startswith(f"{domain}-")
    )


# Entrypoints


def suspend_listener(listener):
    contents = get(f"localhost/config/listeners/{listener}")
    with open(f"/opt/unit/backup-listener-{listener}", "w") as backup:
        backup.write(contents)
    delete(f"localhost/config/listeners/{listener}")


def restore_listener(listener):
    with open(f"/opt/unit/backup-listener-{listener}", "r") as backup:
        contents = backup.read()
    put(contents, f"localhost/config/listeners/{listener}")


def use_latest_cert(domain, listener):
    latest = certs(domain)[-1]
    put(dumps({"certificate": latest}), f"localhost/config/listeners/{listener}/tls")


def load_cert(domain):
    cert_name = f"{domain}-{date.today().isoformat()}"

    with open(f"/etc/letsencrypt/live/{domain}/fullchain.pem", "r") as pem:
        cert_data = pem.read()
    with open(f"/etc/letsencrypt/live/{domain}/privkey.pem", "r") as pem:
        cert_data += pem.read()

    put(cert_data, f"localhost/certificates/{cert_name}")


def delete_old_certs(domain):
    for cert in certs(domain)[:-2]:  # keep the last 2
        delete(f"localhost/certificates/{cert}")


if __name__ == "__main__":
    entrypoints = {
        "suspend-listener": suspend_listener,
        "restore-listener": restore_listener,
        "use-latest-cert": use_latest_cert,
        "load-cert": load_cert,
        "delete-old-certs": delete_old_certs,
    }

    _this, entrypoint, *args = argv
    entrypoints[entrypoint](*args)
