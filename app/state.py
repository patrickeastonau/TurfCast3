import reflex as rx
import datetime
import httpx
import logging
from typing import TypedDict, Optional, Any
import json
from pathlib import Path


class WeatherData(TypedDict):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    daily_units: dict[str, str]
    daily: dict[str, list[str | float | None]]


class Location(TypedDict):
    lat: float
    lon: float
    display_name: str


class CalculationResult(TypedDict):
    week_ending: str
    season: str
    target_mm: float
    observed_mm: float
    deficit_mm: float
    forecast_48h_mm: float
    watering_minutes: int
    emoji: str
    status_text: str
    recommendation: str


GRASS_INFO = [
    {
        "id": "buffalo",
        "display_name": "Buffalo (Soft-leaf)",
        "scientific_name": "Stenotaphrum secundatum",
        "image": "/placeholder.svg",
    },
    {
        "id": "kikuyu",
        "display_name": "Kikuyu",
        "scientific_name": "Cenchrus clandestinus",
        "image": "/placeholder.svg",
    },
    {
        "id": "couch_bermuda",
        "display_name": "Couch / Bermuda",
        "scientific_name": "Cynodon dactylon",
        "image": "/placeholder.svg",
    },
    {
        "id": "zoysia",
        "display_name": "Zoysia",
        "scientific_name": "Zoysia spp.",
        "image": "/placeholder.svg",
    },
    {
        "id": "qld_blue_couch",
        "display_name": "QLD Blue Couch",
        "scientific_name": "Digitaria didactyla",
        "image": "/placeholder.svg",
    },
    {
        "id": "tall_fescue",
        "display_name": "Tall Fescue",
        "scientific_name": "Festuca arundinacea",
        "image": "/placeholder.svg",
    },
    {
        "id": "fine_fescue",
        "display_name": "Fine Fescue",
        "scientific_name": "Festuca spp.",
        "image": "/placeholder.svg",
    },
    {
        "id": "seashore_paspalum",
        "display_name": "Seashore Paspalum",
        "scientific_name": "Paspalum vaginatum",
        "image": "/placeholder.svg",
    },
]
GRASS_TYPES = [g["id"] for g in GRASS_INFO]
SPRINKLER_TYPES = [
    "Oscillating",
    "Fixed/Dome",
    "Rotary/Gear-drive",
    "Impact",
    "Dripline",
]
DAYS_OF_WEEK = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]
GRASS_TARGETS = {
    "buffalo": {"spring": 20, "summer": 25, "autumn": 15, "winter": 0},
    "kikuyu": {"spring": 20, "summer": 30, "autumn": 15, "winter": 0},
    "couch_bermuda": {"spring": 15, "summer": 25, "autumn": 10, "winter": 0},
    "zoysia": {"spring": 20, "summer": 25, "autumn": 15, "winter": 0},
    "qld_blue_couch": {"spring": 15, "summer": 25, "autumn": 15, "winter": 0},
    "tall_fescue": {"spring": 25, "summer": 30, "autumn": 25, "winter": 10},
    "fine_fescue": {"spring": 20, "summer": 30, "autumn": 20, "winter": 10},
    "seashore_paspalum": {"spring": 20, "summer": 30, "autumn": 15, "winter": 0},
}
SPRINKLER_RATES = {
    "Oscillating": 20,
    "Fixed/Dome": 20,
    "Rotary/Gear-drive": 30,
    "Impact": 25,
    "Dripline": 40,
}
POSTCODE_DATA_PATH = Path("assets/postcodes.json")


class LawnState(rx.State):
    grass_type: str = GRASS_INFO[0]["id"]
    postcode: str = ""
    sprinkler_type: str = SPRINKLER_TYPES[0]
    notification_day: str = DAYS_OF_WEEK[0]
    notification_time: str = "18:00"

    @rx.var
    def sprinkler_rates_display(self) -> dict[str, float]:
        return {k: round(10 / v, 2) for k, v in SPRINKLER_RATES.items()}

    is_loading: bool = False
    error_message: str = ""
    location: Optional[Location] = None
    weather_station_info: str = ""
    calculation_result: Optional[CalculationResult] = None
    show_results: bool = False
    postcode_data: dict[str, dict[str, float | str]] = {}

    @rx.var
    def is_form_valid(self) -> bool:
        return len(self.postcode) == 4 and self.postcode.isdigit()

    @rx.event
    async def on_load(self):
        """Load postcode data on initial app load."""
        if not self.postcode_data:
            if not POSTCODE_DATA_PATH.exists():
                try:
                    async with httpx.AsyncClient() as client:
                        res = await client.get(
                            "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.json"
                        )
                        res.raise_for_status()
                        all_postcodes_list = res.json()
                        processed_postcodes = {}
                        for item in all_postcodes_list:
                            pc = item.get("postcode")
                            if pc and pc not in processed_postcodes:
                                if (
                                    item.get("state") == "VIC"
                                    or (
                                        item.get("state") == "WA"
                                        and float(item.get("lat", 0)) < -20
                                    )
                                    or item.get("state") == "NT"
                                ):
                                    processed_postcodes[pc] = {
                                        "latitude": item.get(
                                            "Lat_precise", item.get("lat")
                                        ),
                                        "longitude": item.get(
                                            "Long_precise", item.get("long")
                                        ),
                                        "locality": item["locality"],
                                        "state": item["state"],
                                    }
                        POSTCODE_DATA_PATH.write_text(json.dumps(processed_postcodes))
                        self.postcode_data = processed_postcodes
                except Exception as e:
                    logging.exception(
                        f"Failed to download or process postcode data: {e}"
                    )
                    self.error_message = (
                        "Could not load location data. Please try again later."
                    )
                    return
            try:
                with POSTCODE_DATA_PATH.open("r") as f:
                    self.postcode_data = json.load(f)
            except FileNotFoundError as e:
                logging.exception(
                    f"Postcode data file not found at: {POSTCODE_DATA_PATH}: {e}"
                )
                self.error_message = (
                    "Location data is missing. App may not function correctly."
                )
            except json.JSONDecodeError as e:
                logging.exception(f"Error decoding JSON from {POSTCODE_DATA_PATH}: {e}")
                self.error_message = (
                    "Location data is corrupted. Please contact support."
                )
            except Exception as e:
                logging.exception(f"Error loading postcode data: {e}")
                self.error_message = "Failed to load location data. Please refresh."

    @rx.event(background=True)
    async def calculate_watering(self):
        """Main event to trigger the watering calculation process."""
        async with self:
            if not self.is_form_valid:
                self.error_message = "Please enter a valid 4-digit postcode."
                return
            self.is_loading = True
            self.error_message = ""
            self.show_results = False
        try:
            await self._resolve_location()
            async with self:
                if not self.location:
                    self.is_loading = False
                    return
            weather_data = await self._fetch_weather_data()
            if not weather_data:
                async with self:
                    self.is_loading = False
                return
            await self._perform_calculations(weather_data)
        except Exception as e:
            logging.exception(f"Error in calculation process: {e}")
            async with self:
                self.error_message = f"An unexpected error occurred: {e}"
        finally:
            async with self:
                self.is_loading = False
                if not self.error_message and self.calculation_result:
                    self.show_results = True

    async def _resolve_location(self):
        """Resolve postcode to latitude and longitude."""
        async with self:
            if not self.postcode_data:
                await self.on_load()
            if not self.postcode_data:
                self.error_message = "Location data not loaded. Cannot find postcode."
                self.location = None
                return
            if self.postcode in self.postcode_data:
                pc_data = self.postcode_data[self.postcode]
                self.location = {
                    "lat": float(pc_data["latitude"]),
                    "lon": float(pc_data["longitude"]),
                    "display_name": f"{pc_data['locality']}, {pc_data['state']}",
                }
                self.weather_station_info = "Nearest weather station data"
            else:
                self.error_message = (
                    "Postcode not found. Please enter a valid Australian postcode."
                )
                self.location = None

    async def _fetch_weather_data(self) -> Optional[WeatherData]:
        """Fetch weather data from the Open-Meteo API."""
        async with self:
            if not self.location:
                return None
            lat, lon = (self.location["lat"], self.location["lon"])
        API_URL = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum",
            "past_days": 7,
            "forecast_days": 2,
            "timezone": "Australia/Melbourne",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(API_URL, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logging.exception(f"HTTP error fetching weather data: {e}")
            async with self:
                self.error_message = f"Weather service error: {e.response.status_code}. Please try again later."
            return None
        except Exception as e:
            logging.exception(f"Error fetching weather data: {e}")
            async with self:
                self.error_message = "Could not connect to the weather service. Check your internet connection."
            return None

    def _get_season(self, today: datetime.date) -> str:
        """Determine the current season in the Southern Hemisphere."""
        month = today.month
        if month in [12, 1, 2]:
            return "summer"
        if month in [3, 4, 5]:
            return "autumn"
        if month in [6, 7, 8]:
            return "winter"
        return "spring"

    async def _perform_calculations(self, weather_data: WeatherData):
        """Perform all calculations based on weather data and user settings."""
        async with self:
            today = datetime.date.today()
            season = self._get_season(today)
            target_mm = GRASS_TARGETS.get(self.grass_type, {}).get(season, 0)
            daily_precip = weather_data.get("daily", {}).get("precipitation_sum", [])
            if not daily_precip or len(daily_precip) < 9:
                self.error_message = (
                    "Incomplete weather data received. Cannot perform calculation."
                )
                return
            observed_mm = sum((p for p in daily_precip[:7] if p is not None))
            winter_exception_grasses = [
                "buffalo",
                "kikuyu",
                "zoysia",
                "seashore_paspalum",
            ]
            if self.grass_type in winter_exception_grasses and season == "winter":
                if len(daily_precip) >= 14:
                    last_14_days_precip = sum(
                        (p for p in daily_precip[:14] if p is not None)
                    )
                    deficit_mm = 5.0 if last_14_days_precip < 10 else 0.0
                else:
                    deficit_mm = 5.0 if observed_mm < 5 else 0.0
            elif self.grass_type == "fine_fescue" and season == "winter":
                deficit_mm = max(0.0, target_mm - observed_mm)
            else:
                deficit_mm = max(0.0, target_mm - observed_mm)
            forecast_48h_mm = sum((p for p in daily_precip[7:9] if p is not None))
            minutes_per_10mm = SPRINKLER_RATES.get(self.sprinkler_type, 20)
            raw_watering_minutes = deficit_mm * (minutes_per_10mm / 10.0)
            watering_minutes = int(5 * round(raw_watering_minutes / 5))
            if forecast_48h_mm >= 25 or (target_mm > 0 and observed_mm >= target_mm):
                emoji = "🌧️"
                status_text = "Heavy Rain - Skip"
                recommendation = (
                    "Nature's got it covered. No watering needed this week."
                )
                watering_minutes = 0
            elif 5 <= forecast_48h_mm < 25 or (
                target_mm > 0 and abs(target_mm - observed_mm) <= 3
            ):
                emoji = "🌦️"
                status_text = "Light Rain - Monitor"
                recommendation = "Monitor your lawn. Watering may not be necessary."
                watering_minutes = int(5 * round(watering_minutes / 2 / 5))
            elif deficit_mm > 15 and forecast_48h_mm < 5:
                emoji = "🔥"
                status_text = "Very Dry - Deep Water"
                recommendation = (
                    f"A deep watering is needed. Water for {watering_minutes} minutes."
                )
            elif deficit_mm > 0:
                emoji = "☀️"
                status_text = "Dry - Water Needed"
                recommendation = (
                    f"Your lawn is thirsty. Water for {watering_minutes} minutes."
                )
            else:
                emoji = "✅"
                status_text = "All Good"
                recommendation = "Your lawn has received enough water recently."
                watering_minutes = 0
            if watering_minutes > 45 and (not "split" in recommendation):
                recommendation += " Consider splitting this into two shorter sessions to improve absorption."
            self.calculation_result = {
                "week_ending": today.strftime("%d %b %Y"),
                "season": season.title(),
                "target_mm": round(target_mm, 1),
                "observed_mm": round(observed_mm, 1),
                "deficit_mm": round(deficit_mm, 1),
                "forecast_48h_mm": round(forecast_48h_mm, 1),
                "watering_minutes": watering_minutes,
                "emoji": emoji,
                "status_text": status_text,
                "recommendation": recommendation,
            }