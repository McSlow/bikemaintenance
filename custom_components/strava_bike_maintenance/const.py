"""Constants for the Strava Bike Maintenance integration."""

DOMAIN = "strava_bike_maintenance"

CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

API_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
API_TOKEN_URL = "https://www.strava.com/oauth/token"
API_BASE_URL = "https://www.strava.com/api/v3"

UPDATE_INTERVAL_SECONDS = 900  # 15 minutes

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_wear_counters"

WEAR_PARTS = {
    "chain": "Chain",
    "chain_waxing": "Chain Waxing",
    "tires": "Tires",
}
