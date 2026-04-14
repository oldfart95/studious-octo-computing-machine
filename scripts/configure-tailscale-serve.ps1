$ErrorActionPreference = "Stop"

tailscale serve --bg 443 http://127.0.0.1:5173
tailscale serve status
