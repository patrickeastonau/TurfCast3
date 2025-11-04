import reflex as rx
from typing import Any
from app.state import LawnState, GRASS_INFO, SPRINKLER_TYPES, DAYS_OF_WEEK

SPRINKLER_IMAGES = {
    "Oscillating": "/placeholder.svg",
    "Fixed/Dome": "/placeholder.svg",
    "Rotary/Gear-drive": "/placeholder.svg",
    "Impact": "/placeholder.svg",
    "Dripline": "/placeholder.svg",
}


def icon_text(icon_name: str, text: str | rx.Var[str | float | int]) -> rx.Component:
    """A helper component for an icon followed by text."""
    return rx.el.div(
        rx.icon(icon_name, class_name="h-5 w-5 text-gray-500"),
        rx.el.span(text, class_name="text-gray-700 font-medium"),
        class_name="flex items-center gap-3",
    )


def sprinkler_option(sprinkler_type: str) -> rx.Component:
    rate = LawnState.sprinkler_rates_display[sprinkler_type]
    return rx.el.div(
        rx.el.div(
            rx.image(
                src=SPRINKLER_IMAGES.get(sprinkler_type, "/placeholder.svg"),
                class_name="h-24 w-full object-cover rounded-t-lg",
            ),
            rx.el.div(
                rx.el.span(sprinkler_type, class_name="font-semibold text-gray-800"),
                rx.el.span(
                    f"(~{rate} mm/min)", class_name="text-xs text-gray-500 mt-1 block"
                ),
                class_name="p-3 text-center",
            ),
            class_name=rx.cond(
                LawnState.sprinkler_type == sprinkler_type,
                "rounded-lg border-2 border-orange-500 shadow-lg scale-105 bg-white",
                "rounded-lg border border-gray-200 bg-white hover:shadow-md transition-all",
            ),
        ),
        on_click=lambda: LawnState.set_sprinkler_type(sprinkler_type),
        class_name="cursor-pointer transform transition-transform duration-200",
    )


def grass_option(grass: dict) -> rx.Component:
    """A component to display a grass type option with an image."""
    return rx.el.div(
        rx.el.div(
            rx.image(
                src=grass["image"], class_name="h-24 w-full object-cover rounded-t-lg"
            ),
            rx.el.div(
                rx.el.span(
                    grass["display_name"],
                    class_name="font-semibold text-gray-800 leading-tight",
                ),
                rx.el.span(
                    f"({grass['scientific_name']})",
                    class_name="text-xs italic text-gray-500 mt-1",
                ),
                class_name="p-3 text-center flex flex-col",
            ),
            class_name=rx.cond(
                LawnState.grass_type == grass["id"],
                "rounded-lg border-2 border-orange-500 shadow-lg scale-105 bg-white",
                "rounded-lg border border-gray-200 bg-white hover:shadow-md transition-all",
            ),
        ),
        on_click=lambda: LawnState.set_grass_type(grass["id"]),
        class_name="cursor-pointer transform transition-transform duration-200",
    )


def settings_card() -> rx.Component:
    """The main card for user settings."""
    return rx.el.div(
        rx.el.h2("Your Lawn Setup", class_name="text-2xl font-bold text-gray-800 mb-6"),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Grass Type",
                    htmlFor="grass-type",
                    class_name="font-semibold text-gray-700 mb-3 block",
                ),
                rx.el.div(
                    rx.foreach(GRASS_INFO, grass_option),
                    class_name="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8",
                ),
                class_name="w-full",
            )
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Postcode (AU)",
                    htmlFor="postcode",
                    class_name="font-semibold text-gray-700 mb-2 block",
                ),
                rx.el.input(
                    id="postcode",
                    placeholder="e.g., 3000",
                    on_change=LawnState.set_postcode,
                    maxLength=4,
                    class_name="w-full p-3 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition",
                    default_value=LawnState.postcode,
                ),
                class_name="w-full",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6",
        ),
        rx.el.div(
            rx.el.label(
                "Sprinkler Type", class_name="font-semibold text-gray-700 mb-3 block"
            ),
            rx.el.div(
                rx.foreach(SPRINKLER_TYPES, sprinkler_option),
                class_name="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8",
            ),
        ),
        rx.el.div(
            rx.el.h3(
                "Weekly Notification",
                class_name="text-lg font-semibold text-gray-800 mb-4 border-t pt-6",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Day",
                        htmlFor="notification-day",
                        class_name="font-medium text-gray-600 mb-2 block",
                    ),
                    rx.el.select(
                        rx.foreach(DAYS_OF_WEEK, lambda d: rx.el.option(d, value=d)),
                        id="notification-day",
                        value=LawnState.notification_day,
                        on_change=LawnState.set_notification_day,
                        class_name="w-full p-3 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition",
                    ),
                ),
                rx.el.div(
                    rx.el.label(
                        "Time",
                        htmlFor="notification-time",
                        class_name="font-medium text-gray-600 mb-2 block",
                    ),
                    rx.el.input(
                        type="time",
                        id="notification-time",
                        on_change=LawnState.set_notification_time,
                        class_name="w-full p-3 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition",
                        default_value=LawnState.notification_time,
                    ),
                ),
                class_name="grid grid-cols-2 gap-4",
            ),
            class_name="mb-8",
        ),
        rx.el.button(
            rx.icon("calculator", class_name="mr-2"),
            "Calculate Watering Needs",
            on_click=LawnState.calculate_watering,
            is_loading=LawnState.is_loading,
            disabled=~LawnState.is_form_valid | LawnState.is_loading,
            class_name="w-full flex justify-center items-center bg-orange-500 text-white font-bold py-4 px-4 rounded-lg hover:bg-orange-600 transition-all duration-300 disabled:bg-gray-300 disabled:cursor-not-allowed text-lg shadow-md hover:shadow-lg",
        ),
        rx.cond(
            LawnState.error_message != "",
            rx.el.div(
                rx.icon("flag_triangle_right", class_name="h-5 w-5 mr-2 text-red-700"),
                rx.el.span(LawnState.error_message),
                class_name="mt-4 p-3 bg-red-100 text-red-700 rounded-lg flex items-center",
            ),
            None,
        ),
        class_name="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 w-full max-w-4xl mx-auto",
    )


def results_card() -> rx.Component:
    """The card to display calculation results."""
    return rx.el.div(
        rx.cond(
            LawnState.calculation_result,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            LawnState.calculation_result["emoji"], class_name="text-6xl"
                        ),
                        rx.el.div(
                            rx.el.h2(
                                LawnState.calculation_result["status_text"],
                                class_name="text-3xl font-bold text-gray-800",
                            ),
                            rx.el.p(
                                f"For week ending {LawnState.calculation_result['week_ending']}",
                                class_name="text-gray-500",
                            ),
                            class_name="ml-4",
                        ),
                        class_name="flex items-center mb-6",
                    ),
                    rx.el.div(
                        rx.el.p(
                            LawnState.calculation_result["recommendation"],
                            class_name="text-xl font-medium text-center text-orange-800",
                        ),
                        class_name="bg-orange-100 p-6 rounded-xl mb-8 border border-orange-200",
                    ),
                    rx.el.div(
                        icon_text(
                            "thermometer-sun",
                            f"{LawnState.calculation_result['season']} Season Target: {LawnState.calculation_result['target_mm']} mm",
                        ),
                        icon_text(
                            "cloud-drizzle",
                            f"Last 7 Days Rainfall: {LawnState.calculation_result['observed_mm']} mm",
                        ),
                        icon_text(
                            "droplets",
                            f"Watering Deficit: {LawnState.calculation_result['deficit_mm']} mm",
                        ),
                        icon_text(
                            "cloud-lightning",
                            f"48hr Forecast: {LawnState.calculation_result['forecast_48h_mm']} mm",
                        ),
                        class_name="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 mb-6",
                    ),
                    rx.el.div(
                        icon_text(
                            "map-pin",
                            f"{LawnState.postcode} ({LawnState.location['display_name']}) - {LawnState.weather_station_info}",
                        ),
                        class_name="text-sm text-gray-400 mt-8 border-t pt-4",
                    ),
                )
            ),
            None,
        ),
        class_name="bg-white p-8 rounded-2xl shadow-lg border border-gray-200 w-full max-w-4xl mx-auto mt-8",
    )


def index() -> rx.Component:
    """The main page of the app."""
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.image(src="placeholder.svg", class_name="h-12 w-12"),
                rx.el.h1(
                    "TurfCast",
                    class_name="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-orange-600 ml-3",
                ),
                class_name="flex items-center justify-center mb-4",
            ),
            rx.el.p(
                "Rain data. Lawn logic.",
                class_name="text-center text-gray-600 mb-8 max-w-md mx-auto",
            ),
            rx.el.div(
                rx.el.p(
                    "Feed in your grass type, postcode, and sprinkler setup — TurfCast’ll tell you if it’s time to water, or if nature’s already shouted you a round.",
                    class_name="text-center text-gray-700",
                ),
                class_name="bg-orange-50 border border-orange-200 p-4 rounded-lg max-w-2xl mx-auto mb-12",
            ),
            settings_card(),
            rx.cond(
                LawnState.is_loading,
                rx.el.div(
                    rx.el.div(
                        class_name="animate-pulse bg-gray-200 h-64 rounded-2xl w-full max-w-4xl mx-auto mt-8"
                    )
                ),
                rx.cond(LawnState.show_results, results_card(), None),
            ),
            rx.el.footer(
                rx.el.p(
                    "Powered by ",
                    rx.el.a(
                        "Open-Meteo",
                        href="https://open-meteo.com/",
                        target="_blank",
                        class_name="text-orange-600 hover:underline font-semibold",
                    ),
                    " and ",
                    rx.el.a(
                        "Reflex",
                        href="https://reflex.dev/",
                        target="_blank",
                        class_name="text-orange-600 hover:underline font-semibold",
                    ),
                    ".",
                ),
                class_name="text-center text-sm text-gray-500 mt-16 pb-8",
            ),
            class_name="container mx-auto px-4 py-8 md:py-12",
        ),
        class_name="font-['Roboto'] bg-gray-50 min-h-screen",
        on_mount=LawnState.on_load,
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, title="TurfCast - Smart Lawn Watering")