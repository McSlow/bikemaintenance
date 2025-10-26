# Strava Bike Maintenance – Follow-up Notes

## Outstanding setup items
- Update the Strava developer portal so the **Authorization Callback Domain** is `my.home-assistant.io` (or your own public HTTPS domain if you already expose Home Assistant).
- Redeploy/sync the latest integration version, then run through the config flow again.

## Integration state
- Custom component files live under `custom_components/strava_bike_maintenance/`.
- OAuth flow now uses Home Assistant’s built-in redirect helper (my.home-assistant.io), so Strava auth works even when Home Assistant is only reachable on the local network.
- Sensors, wear counters, and reset service are in place; only onboarding is blocked by OAuth redirect requirements.

## Next session reminders
- After updating the callback domain in Strava, reload the custom component (HACS > reinstall or copy files) and re-run the config flow.
- Confirm Strava opens the My Home Assistant redirect (`https://my.home-assistant.io/redirect/oauth`) and that Home Assistant immediately advances once the popup closes.
- Consider adding tests or mock flows once OAuth is working, if further validation is needed.***
