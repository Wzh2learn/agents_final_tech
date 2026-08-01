# Deployment Process Guards

## Option 1: systemd (recommended for production)

```bash
# Copy unit file
sudo cp deploy/m1-harness.service /etc/systemd/system/

# Edit tokens (M1_API_TOKEN, M1_ADMIN_TOKEN) before enabling
sudo systemctl daemon-reload
sudo systemctl enable m1-harness
sudo systemctl start m1-harness

# Check status
sudo systemctl status m1-harness
journalctl -u m1-harness -f
```

## Option 2: supervisord

```bash
# Install supervisord if not present
pip install supervisor

# Add to supervisord config (e.g. /etc/supervisor/conf.d/)
sudo cp deploy/supervisord.conf /etc/supervisor/conf.d/m1-harness.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start m1-harness

# Check status
sudo supervisorctl status m1-harness
```

## Important Notes

- **DO NOT** enable these services without first setting real tokens in the
  environment variables (`M1_API_TOKEN`, `M1_ADMIN_TOKEN`).
- The service expects PostgreSQL/PGVector on `:15432` and the LLM on `:8004`.
- Logs are written to `logs/app.log` (JSON structured) and `logs/m1_stderr.log`.
- Health check: `curl http://localhost:5050/health`
- Metrics: `curl http://localhost:5050/api/metrics`
