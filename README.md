## Setting up nginx-unit and https on a raspberry pi

I started with just about a fresh install of Raspberry Pi OS (Debian 10).

### Dependencies
I installed the following dependencies:
```bash
  sudo apt update
  sudo apt upgrade
  sudo apt install certbot ddclient python3-venv python3-dev build-essential libssl-dev libssl-doc libpcre2-dev
```

From there, you can run the `installer` script to download, compile, and install nginx-unit to `/opt/unit`.


### HTTPS
Certbot is as easy as:
```bash
  sudo certbot certonly --standalone
```
Which requires port 80 to be free. You can renew with
```bash
  sudo certbot renew
```
This checks to see if there are any certificates that might expire soon and renews them if so (also requires
port 80 to be free). There are hooks you can set up to temporarily stop your port 80 traffic while your renew,
as described in https://certbot.eff.org/docs/using.html?#renewing-certificates

I'll put in some details there when I get to it.

