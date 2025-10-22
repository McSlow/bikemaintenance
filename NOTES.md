# Strava Bike Maintenance – Follow-up Notes

## Outstanding setup items
- Configure Home Assistant’s **External URL** (`Settings → System → Network`) to a publicly reachable HTTPS address so Strava’s OAuth redirect succeeds.
- Ensure the same host (e.g. `https://example.duckdns.org`) is registered as the callback URL in the Strava developer portal (`<host>/auth/external/callback`).
- Redeploy or sync the updated integration to Home Assistant after setting the external URL, then retry the config flow.

## Integration state
- Custom component files live under `custom_components/strava_bike_maintenance/`.
- OAuth flow now enforces an external callback and surfaces an error if none is configured.
- Sensors, wear counters, and reset service are in place; only onboarding is blocked by OAuth redirect requirements.

## Next session reminders
- After configuring the external URL, run through the HACS install/reload and config flow again.
- Verify that Strava redirects to the public domain and the integration completes setup.
- Consider adding tests or mock flows once OAuth is working, if further validation is needed.***
