# Future Features

Planned features for upcoming releases. When a feature is implemented, remove it from this list and note it in the relevant commit or PR description.

---

## Planned

### Admin: Force sync all sources button
Add a button to the Django admin (on the `Source` changelist or a dedicated admin view) that immediately triggers `catchup_scrapers` for all sources without waiting for the next Celery Beat interval. This gives admins a one-click way to refresh all news on demand instead of navigating to Periodic Tasks.
