# 🚴‍♂️ Strava Bike Maintenance for Home Assistant

Keep on top of wear items across your bikes by syncing Strava mileage straight into Home Assistant. This custom integration turns every Strava bike into a device with distance and maintenance sensors so you know exactly when to swap chains, re-wax, or refresh tires.

## ✨ Features
- 🔐 OAuth2 login using your Strava Client ID/Secret.
- 🔁 Polls the Strava `/athlete` endpoint to gather per-bike distance.
- 📏 Auto-created sensors for lifetime distance (km) on each bike.
- 🛠️ Resettable wear counters for chain, chain waxing, and tires that track distance since last service.
- 🧰 `strava_bike_maintenance.reset_wear_counter` service to zero any wear counter after maintenance.

## 📋 Requirements
- Home Assistant 2023.8 or newer.
- Strava account with bikes configured under *My Gear*.
- Strava API application (create at <https://www.strava.com/settings/api>) for Client ID and Client Secret.
- Access to the Home Assistant `config` directory to install custom components.

## ⚙️ Installation
1. Copy `custom_components/strava_bike_maintenance` into your Home Assistant `custom_components` directory (e.g. `/config/custom_components/`).
2. Restart Home Assistant to load the integration.
3. In Home Assistant set **Settings → System → Network → External URL** to the public HTTPS address Strava can reach (e.g. `https://example.duckdns.org`).
4. Go to **Settings → Devices & Services → Add Integration**, search for **Strava Bike Maintenance**, and select it.
   - In the Strava developer portal set the callback URL/domain to the same host followed by `/auth/external/callback` (e.g. `https://example.duckdns.org/auth/external/callback`).
5. Enter your Strava Client ID and Client Secret. Authorise Home Assistant when Strava prompts you.
6. Once linked, the integration creates devices and sensors for every bike returned by Strava.

## 📡 Entities
Each bike exposes:
- `sensor.strava_<bike_name>_total_distance` – total Strava distance (km, total increasing).
- `sensor.strava_<bike_name>_chain` – distance since the chain counter was reset.
- `sensor.strava_<bike_name>_chain_waxing` – distance since the chain was waxed.
- `sensor.strava_<bike_name>_tires` – distance since the tire counter was reset.

Sensor names follow the bike name from Strava. Attributes include the Strava gear ID (`bike_id`) and wear part identifiers.

## 🔄 Resetting Wear Counters
Call the `strava_bike_maintenance.reset_wear_counter` service whenever you service a bike part:

```yaml
service: strava_bike_maintenance.reset_wear_counter
data:
  bike_id: b123456789
  part: chain
```

Valid `part` values: `chain`, `chain_waxing`, `tires`. The `bike_id` appears in sensor attributes or in Strava’s gear URL. Updated totals show up on the next Strava poll (default every 2 hours) or immediately after a manual refresh.

## 🧯 Troubleshooting
- **No bikes discovered**: Check that bikes exist in Strava and the app request includes the `read` scope.
- **Authentication expired**: Use **Reconfigure** on the integration card to repeat the OAuth flow; confirm your Client Secret matches the Strava app.
- **Wear counters not persisting**: Ensure Home Assistant can write to its configuration directory; counters rely on the storage helper.

## 🛠️ Development Notes
- Polling interval defaults to 2 hours (`UPDATE_INTERVAL_SECONDS` in `custom_components/strava_bike_maintenance/const.py`).
- Add more wear parts by extending `WEAR_PARTS` in `const.py` and updating `services.yaml` plus translations.

## 📄 License
A license has not yet been specified. Add one before distributing modified versions.
