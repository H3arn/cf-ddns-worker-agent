# cf-ddns-worker Agent

A minimal python re-implementation of the powershell agent in [cqjjjzr/cf-ddns-worker](https://github.com/cqjjjzr/cf-ddns-worker).

## Structure

```bash
.
├── agnet.py            # core agent logic
├── config.py           # config: token, urls, toggles
├── LICENSE
├── pyproject.toml      # uv package info
├── README.md
├── requirements.txt    # pip-style dependency
└── uv.lock             # uv package version lock
```

## Requirements

- python 3.8+
- packages: `requests psutil`

## Usage

Prepare dependencies:

```bash
git clone https://github.com/H3arn/cf-ddns-worker-agent
cd cf-ddns-worker-agent

# or simply use `uv sync`
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

copy exmaple config to production.

```bash
cp config.py.example config.py
```

edit `config.py`:

```python
CF_TOKEN_ID = "<AUTH.id in cf-ddns-worker>"
CF_TOKEN    = "<AUTH.token in cf-ddns-worker>"
CF_DOMAIN   = "<within AUTH.allowed in cf-ddns-worker>"

CF_WORKER_URL = "<URL of deployed cf-ddns-worker>"
```

Optionally tweak ipv4/ipv6 settings and update URLs.

run the agent:

```bash
# or `uv run python3 agent.py`
python3 agent.py
```

logs will print to stdout:

```text
retrieving public IPv4 address...
got IPv4 address: 203.0.113.42
success!
```

## How it works

The agent retrieves the machine’s current public ipv4/ipv6 address -- either by querying a remote ip service or inspecting local interfaces, and posts it to a configured worker endpoint, signed with an hmac token.

1. fetches public ip:

   - if `CF_IPVx_UPDATE_URL` is set → queries that api.
   - else → scans local nics with `psutil` and filters global addresses.

2. builds json payload:

   ```json
   {
      "id": "...", 
      "domain": "...", 
      "type": "ipv4", 
      "addr": "...", 
      "timestamp": 1731234567
   }
   ```

3. signs payload using hmac-sha256 with `CF_TOKEN` and base64-encodes it.
4. posts to `CF_WORKER_URL` with the signature in the `Authorization` header.

## Notes

- The script mirrors the original powershell logic but drops windows-specific bits like `Get-NetIPAddress`.
- Tested on linux and macOS.
- Intended for automation and cron jobs.
