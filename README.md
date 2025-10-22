# Strava Bike Maintenance for Home Assistant

This repository hosts a Home Assistant custom integration that reads bike usage data from Strava and tracks distance-based maintenance counters. Each bike listed in your Strava account becomes a device in Home Assistant with sensors for total distance and resettable wear indicators for common service tasks.

## Features
- Secure OAuth2 login with Strava using a Client ID and Client Secret.
- Periodic polling of Strava’s `/athlete` endpoint to capture per-bike distance.
- Home Assistant sensors exposing lifetime distance per bike (kilometres).
- Automatic wear counters for chain wear, chain waxing, and tire wear, incremented by distance travelled since the last reset.
- `strava_bike_maintenance.reset_wear_counter` service for resetting individual wear counters after maintenance.

## Requirements
- Home Assistant 2023.8 or newer.
- An active Strava account with bikes configured under *My Gear*.
- A Strava API application registered at <https://www.strava.com/settings/api> to obtain your Client ID and Client Secret.
- Access to the Home Assistant `config` directory to install custom components.

## Installation
1. Copy the entire `custom_components/strava_bike_maintenance` folder from this repository into your Home Assistant configuration directory (typically `/config/custom_components/`).
2. Restart Home Assistant to load the new integration.
3. Open **Settings → Devices & Services → Add Integration**, search for **Strava Bike Maintenance**, and select it.
4. Enter the Strava Client ID and Client Secret when prompted. Home Assistant will redirect you to Strava to grant access; approve the request to finish linking.
5. Once connected, the integration will create devices and sensors for each bike returned by Strava.

## Entities
For every Strava bike the integration provides:
- `sensor.strava_<bike_name>_total_distance` – total distance logged by Strava (km, total increasing).
- `sensor.strava_<bike_name>_chain` – distance since the chain wear counter was last reset.
- `sensor.strava_<bike_name>_chain_waxing` – distance since the chain was waxed.
- `sensor.strava_<bike_name>_tires` – distance since the tire wear counter was last reset.

Entity names derive from the Strava bike name. Attributes include the underlying Strava gear ID (`bike_id`) and the wear part identifier where applicable.

## Resetting Wear Counters
The `strava_bike_maintenance.reset_wear_counter` service is provided to reset a wear counter after maintenance. Example call:

```yaml
service: strava_bike_maintenance.reset_wear_counter
data:
  bike_id: b123456789
  part: chain
```

Valid parts: `chain`, `chain_waxing`, `tires`. The `bike_id` can be found in the sensor attributes or in Strava’s gear URL. After resetting, the updated value will be reflected on the next Strava data poll (default every 15 minutes) or immediately if you manually refresh the entity.

## Troubleshooting
- **No bikes discovered**: Confirm the authorised Strava account has bikes set up and that the Strava app includes the `read` scope.
- **Authentication expired**: Use **Reconfigure** on the integration card to redo the OAuth flow. Verify the Client Secret matches your Strava application.
- **Wear counters not persisting**: Ensure Home Assistant can write to its configuration directory; the integration stores counters via Home Assistant’s storage helper.

## Development Notes
- Polling interval defaults to 15 minutes; adjust `UPDATE_INTERVAL_SECONDS` in `custom_components/strava_bike_maintenance/const.py` if needed.
- Additional wear counters can be introduced by extending `WEAR_PARTS` in `const.py` and updating `services.yaml` selectors and strings.

## License
A license has not yet been specified. Add an appropriate license file before distributing modified versions.
