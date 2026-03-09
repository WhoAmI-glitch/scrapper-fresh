# Command: /wire-telegram-digest

## Description
Set up or update a Telegram bot integration that sends daily/weekly digest notifications about NUAMAKA platform activity, metrics, or content.

## Usage
```
/wire-telegram-digest [--frequency daily|weekly] [--content metrics|alerts|content|all] [--channel <channel_id>]
```

## Workflow

### Phase 1: Configuration
1. Check for existing Telegram bot configuration.
2. Verify required environment variables:
   - `TELEGRAM_BOT_TOKEN` — bot API token
   - `TELEGRAM_CHAT_ID` — target chat/channel ID
   - `TELEGRAM_DIGEST_SCHEDULE` — cron expression
3. If not configured, create `.env.example` entries and document setup.

### Phase 2: Data Collection
1. Define data sources for the digest:
   - **Metrics**: user signups, active users, feature usage
   - **Alerts**: error rates, downtime, security events
   - **Content**: new blog posts, community highlights
   - **Dev**: recent deployments, PRs merged, tests status
2. Create collector functions for each data source.
3. Implement data formatting for Telegram markdown.

### Phase 3: Bot Implementation
1. Create or update the Telegram bot service:
   - Message formatting with Telegram MarkdownV2
   - Rate limiting compliance (Telegram API limits)
   - Error handling with retry logic
   - Message splitting for long digests
2. Implement the digest scheduler (cron job or queue-based).
3. Add health check for the bot service.

### Phase 4: Templates
1. Create digest message templates:
   ```
   NUAMAKA Daily Digest
   {date}

   METRICS
   - New users: {count}
   - Active users: {count}
   - Top feature: {feature}

   ALERTS
   - {alert summaries}

   DEPLOYMENTS
   - {recent deployments}
   ```
2. Support both daily and weekly formats.
3. Include deep links back to dashboards.

### Phase 5: Testing & Deployment
1. Test message formatting with Telegram API.
2. Verify scheduled execution.
3. Add monitoring for failed digest sends.
4. Document the setup in `docs/integrations/telegram-digest.md`.

## Acceptance Criteria
- [ ] Bot sends formatted digest to configured channel
- [ ] Schedule is configurable via environment variable
- [ ] Content sources are modular and extensible
- [ ] Error handling with retries implemented
- [ ] Rate limiting respected
- [ ] Setup documented with all required env vars
- [ ] Tests cover message formatting and scheduling logic
