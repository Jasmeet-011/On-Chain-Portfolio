# Alert System - Quick Reference Guide

## 📋 Table of Contents
- [Creating Alerts](#creating-alerts)
- [Alert Types](#alert-types)
- [API Examples](#api-examples)
- [Common Issues](#common-issues)

---

## Creating Alerts

### Token Price Alert
```python
# Create a token price alert
POST /alerts/
{
  "token_symbol": "SOL",
  "target_price": 150.0,
  "condition": "above",  // "above" or "below"
  "wallet_address": null  // null = all wallets, or specific address
}
```

### Portfolio Value Alert
```python
# Create a portfolio value alert
POST /alerts/
{
  "alert_type": "portfolio",
  "portfolio_metric": "value",  // "value", "change_percent", "risk_level", "concentration"
  "condition": "below",
  "target_value": 10000.0
}
```

### Wallet Value Alert
```python
# Create a wallet-specific alert
POST /alerts/
{
  "alert_type": "wallet",
  "wallet_address": "0x123...",
  "condition": "above",
  "target_value": 5000.0
}
```

---

## Alert Types

### Tier 1: Portfolio Alerts
| Metric | Description | Example |
|--------|-------------|---------|
| `value` | Total portfolio value | Alert when portfolio > $10,000 |
| `change_percent` | 24h percentage change | Alert when change > 5% |
| `risk_level` | Portfolio risk | Alert when risk is "high" |
| `concentration` | Max token concentration | Alert when 1 token > 50% |

### Tier 2: Token Alerts
| Type | Description | Example |
|------|-------------|---------|
| Global | Track across all wallets | Alert when SOL > $150 |
| Specific | Track in one wallet | Alert when SOL > $150 in wallet X |

### Tier 3: Wallet Alerts
| Type | Description | Example |
|------|-------------|---------|
| Value | Total wallet value | Alert when wallet > $5,000 |

---

## API Examples

### List All Alerts
```bash
GET /alerts/
Authorization: Bearer <token>

Response:
[
  {
    "id": "alert_123",
    "alert_type": "token",
    "token_symbol": "SOL",
    "condition": "above",
    "target_price": 150.0,
    "current_price": 145.23,
    "is_active": true,
    "status": "active",
    "created_at": "2025-01-08T00:00:00Z"
  }
]
```

### Get Alert Statistics
```bash
GET /alerts/stats
Authorization: Bearer <token>

Response:
{
  "total_alerts": 8,
  "active_alerts": 5,
  "triggered_today": 1,
  "triggered_this_week": 3,
  "triggered_total": 10
}
```

### Update Alert
```bash
PATCH /alerts/{alert_id}
Authorization: Bearer <token>

Body:
{
  "target_price": 160.0,
  "is_active": true
}
```

### Delete Alert
```bash
DELETE /alerts/{alert_id}
Authorization: Bearer <token>

Response: 204 No Content
```

### Test Alert Email
```bash
POST /alerts/{alert_id}/test
Authorization: Bearer <token>

Response:
{
  "message": "Test email sent successfully",
  "email": "user@example.com",
  "alert_id": "alert_123"
}
```

---

## Email Preferences

### Get Preferences
```bash
GET /alerts/preferences/email
Authorization: Bearer <token>

Response:
{
  "user_id": "user_123",
  "price_alerts_enabled": true,
  "daily_digest_enabled": true,
  "weekly_summary_enabled": false
}
```

### Update Preferences
```bash
PUT /alerts/preferences/email
Authorization: Bearer <token>

Body:
{
  "price_alerts_enabled": true,
  "daily_digest_enabled": false,
  "weekly_summary_enabled": true
}
```

---

## Common Issues

### Issue: Alert not triggering
**Possible causes:**
1. Alert is not active (`is_active: false`)
2. Cooldown period (recurring alerts wait 1 hour)
3. Price not reaching target
4. Scheduler not running

**Solution:**
```python
# Check alert status
GET /alerts/{alert_id}

# Reactivate if needed
PATCH /alerts/{alert_id}
{
  "is_active": true
}
```

### Issue: Not receiving emails
**Possible causes:**
1. Email preferences disabled
2. SMTP not configured
3. Invalid email address

**Solution:**
```python
# Check preferences
GET /alerts/preferences/email

# Enable if needed
PUT /alerts/preferences/email
{
  "price_alerts_enabled": true
}

# Test email
POST /alerts/{alert_id}/test
```

### Issue: Validation error
**Possible causes:**
1. Invalid token symbol
2. Negative price
3. Missing required fields

**Solution:**
```python
# Ensure valid data
{
  "token_symbol": "SOL",  // Must be non-empty
  "target_price": 150.0,  // Must be > 0
  "condition": "above"    // Must be "above" or "below"
}
```

---

## Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Check authentication token |
| 404 | Not Found | Alert ID doesn't exist |
| 422 | Validation Error | Check required fields |
| 500 | Server Error | Check logs, contact support |

---

## Scheduler Jobs

### Check Alerts
```python
# Runs every 5 minutes
# Checks all active alerts and triggers notifications
```

### Daily Digest
```python
# Runs daily at 8:00 AM
# Sends portfolio summary to users with digest enabled
```

### Weekly Summary
```python
# Runs Sunday at 8:00 AM
# Sends weekly performance summary
```

---

## Best Practices

1. **Set Realistic Targets**: Don't set alerts too close to current price
2. **Use Recurring Alerts**: For continuous monitoring
3. **Test First**: Use the test endpoint before relying on alerts
4. **Check Stats**: Monitor trigger counts to avoid spam
5. **Manage Preferences**: Disable digests if not needed

---

## Support

For issues or questions:
1. Check logs: `backend/logs/`
2. Review documentation: `ALERT_SYSTEM_IMPROVEMENTS.md`
3. Test endpoints: Use `/test` endpoints
4. Check database: Verify alert documents

---

## Quick Tips

💡 **Tip 1**: Use portfolio alerts for overall monitoring
💡 **Tip 2**: Use token alerts for specific price points
💡 **Tip 3**: Use wallet alerts for account balance tracking
💡 **Tip 4**: Test emails before important price movements
💡 **Tip 5**: Disable inactive alerts to reduce noise
