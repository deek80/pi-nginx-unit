#!/usr/bin/env python3

from datetime import datetime
from json import dumps, loads
from subprocess import run
from sys import argv


def curl(*args):
    output = loads(
        run(
            ("curl", "--unix-socket", "/opt/unit/control.unit.sock", *args),
            text=True,
            capture_output=True,
        ).stdout
    )
    if "error" in output:
        raise RuntimeError(f"curl command failed with: {output['error']}")
    return output


def get(path):
    return curl(path)


def put(data, path):
    return curl("-X", "PUT", "--data-binary", data, path)


def delete(path):
    return curl("-X", "DELETE", path)


def certs(domain):
    return sorted(
        cert for cert in get("localhost/certificates") if cert.startswith(f"{domain}-")
    )


def timestamp():
    return datetime.now().strftime("%s")


def today():
    return datetime.now().date().isoformat()


# Entrypoints


def suspend_listener(listener):
    contents = get(f"localhost/config/listeners/{listener}")
    with open(f"/opt/unit/backup-listener-{listener}", "w") as backup:
        backup.write(dumps(contents))
    delete(f"localhost/config/listeners/{listener}")


def restore_listener(listener):
    with open(f"/opt/unit/backup-listener-{listener}", "r") as backup:
        contents = backup.read()
    put(contents, f"localhost/config/listeners/{listener}")


def use_latest_cert(domain, listener):
    latest = certs(domain)[-1]
    put(dumps({"certificate": latest}), f"localhost/config/listeners/{listener}/tls")


def load_cert(domain):
    with open(f"/etc/letsencrypt/live/{domain}/fullchain.pem", "r") as pem:
        cert_data = pem.read()
    with open(f"/etc/letsencrypt/live/{domain}/privkey.pem", "r") as pem:
        cert_data += pem.read()

    put(cert_data, f"localhost/certificates/{domain}-{today()}")


def delete_old_certs(domain):
    for cert in certs(domain)[:-2]:  # keep the last 2
        delete(f"localhost/certificates/{cert}")


def create_python_app(name, path, module, processes=1, app="app"):
    config = {
        "type": "python",
        "home": f"{path}/.venv",
        "path": path,
        "module": module,
        "callable": app,
        "processes": int(processes),
        "environment": {"published": timestamp()},
    }
    put(dumps(config), f"localhost/config/applications/{name}")


def refresh_app(name):
    """ workaround to restart an app when you update the source """
    put(
        dumps(timestamp()),
        f"localhost/config/applications/{name}/environment/published",
    )


if __name__ == "__main__":
    entrypoints = {
        "suspend-listener": suspend_listener,
        "restore-listener": restore_listener,
        "use-latest-cert": use_latest_cert,
        "load-cert": load_cert,
        "delete-old-certs": delete_old_certs,
        "create-python-app": create_python_app,
        "refresh-app": refresh_app,
    }

    _this, entrypoint, *args = argv
    entrypoints[entrypoint](*args)
