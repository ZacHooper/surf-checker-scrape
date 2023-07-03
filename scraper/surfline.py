# Currently scraping infomation from the website. There does look to be an API service that is accessible:
# eg - https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=607776017a3e100333600795 for torquay wave data.
# This data appears to have been generated for the next 16 days so not sure how useful it is for current data

from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import requests
from urllib.parse import urlparse, parse_qs

base_url = "https://services.surfline.com/kbyg/spots/forecasts"


def get_surf_conditions_card(soup: BeautifulSoup) -> BeautifulSoup:
    conditions_card = soup.find(
        "div", {"class": re.compile("CurrentSurfConditionsCard_cardWithForecaster")}
    )

    return conditions_card


def get_surf_height(soup: BeautifulSoup) -> tuple[str, str]:
    """
    Get the surf height and unit from the soup.

    Args:
        soup (BeautifulSoup): Surf report soup.

    Returns:
        tuple[str, str]: The surf height and it's unit
    """
    surf_height_div = soup.find(
        "div", {"class": re.compile("CurrentSurfConditionsCard_waveHeight")}
    )
    surf_height_h2 = surf_height_div.find_all("h2")
    surf_height = surf_height_h2[0].text
    surf_height_unit = surf_height_h2[1].text
    return surf_height, surf_height_unit


def get_surf_rating(soup: BeautifulSoup) -> str:
    """
    Get the surf rating from the soup.

    Args:
        soup (BeautifulSoup): Surf report soup.

    Returns:
        str: The surf rating
    """
    surf_rating_span = soup.find(
        attrs={"class": re.compile("CurrentSurfConditionsCard_conditionsText")}
    )
    surf_rating = surf_rating_span.text
    return surf_rating


def get_surf_description(soup: BeautifulSoup) -> str:
    """
    Get the surf description from the soup.

    Args:
        soup (BeautifulSoup): Surf report soup.

    Returns:
        str: The surf description
    """
    surf_description_div = soup.find(
        "div", attrs={"class": re.compile("CurrentSurfConditionsCard_title")}
    )

    surf_description = surf_description_div.h1.text
    return surf_description


def get_swells(soup: BeautifulSoup) -> list[dict[str, str]]:
    """
    Get the swells from the soup.

    Args:
        soup (BeautifulSoup): Surf report soup.

    Returns:
        list[dict[str, str]]: The swells
    """
    swells_div = soup.find(
        "div", attrs={"class": re.compile("CurrentSurfConditionsCard_swells")}
    )
    swells = swells_div.find_all("div", attrs={"class": "swell"})
    swell_list = []
    for swell in swells:
        swell_dict = {}
        swell_dict["swell_height"] = swell.find("h2").text
        swell_dict["swell_height_unit"] = swell.find("h3").text
        swell_dict["swell_period"] = swell.find("h4").text
        swell_dict["swell_direction"] = swell.find("h5").text
        swell_list.append(swell_dict)
    return swell_list


def get_surf_location_from_id(spot_id: str) -> str:
    spots = {
        "607776017a3e100333600795": "Torquay Surf Beach",
        "640b9160e920306430def151": "Torquay Main Beach",
        "584204204e65fad6a77099c7": "Bells Beach",
        "5842041f4e65fad6a7708c12": "Winkipop",
        "5842041f4e65fad6a7708c0b": "Jan Juc",
        "5842041f4e65fad6a7708c0c": "13th Beach",
    }
    spot = spots.get(spot_id, "Unknown")
    if spot == "Unknown":
        print(f"ERROR: Unknown spot id provided - {spot_id}")
    return spot


def query(url: str, params: dict) -> requests.Response:
    """
    Query the surfline API.

    Args:
        url (str): The url to query.
        params (dict): The query parameters.

    Returns:
        requests.Response: The response from the API.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    response = requests.get(url, headers=headers, params=params)
    return response


def get_wind_data(spot_id: str, wind_speed_unit: str = "KTS") -> pd.DataFrame:
    response = query(
        f"{base_url}/wind", {"spotId": spot_id, "units[windSpeed]": wind_speed_unit}
    )
    wind_data = json.loads(response.text)
    wind_df = pd.DataFrame(wind_data["data"]["wind"])
    wind_df["surf_location"] = spot_id
    return wind_df


def get_wave_data(spot_id: str, wave_height_unit: str = "FEET") -> pd.DataFrame:
    response = query(
        f"{base_url}/wave",
        {"spotId": spot_id, "units[swellHeight]": "M", "units[waveHeight]": "M"},
    )
    wave_data = json.loads(response.text)
    wave_df = pd.DataFrame(wave_data["data"]["wave"])
    wave_df["surf_location"] = spot_id

    # Get general surf information
    wave_df["min_height"] = wave_df.surf.apply(lambda x: x.get("min"))
    wave_df["max_height"] = wave_df.surf.apply(lambda x: x.get("max"))
    wave_df["human_relation"] = wave_df.surf.apply(lambda x: x.get("humanRelation"))

    # Get swell information
    wave_df["swell_run_1"] = wave_df.swells.apply(lambda x: x[0].get("run"))
    wave_df["swell_height_1"] = wave_df.swells.apply(lambda x: x[0].get("height"))
    wave_df["swell_period_1"] = wave_df.swells.apply(lambda x: x[0].get("period"))
    wave_df["swell_direction_1"] = wave_df.swells.apply(lambda x: x[0].get("direction"))

    wave_df["swell_run_2"] = wave_df.swells.apply(lambda x: x[1].get("run"))
    wave_df["swell_height_2"] = wave_df.swells.apply(lambda x: x[1].get("height"))
    wave_df["swell_period_2"] = wave_df.swells.apply(lambda x: x[1].get("period"))
    wave_df["swell_direction_2"] = wave_df.swells.apply(lambda x: x[1].get("direction"))

    wave_df["swell_run_3"] = wave_df.swells.apply(lambda x: x[2].get("run"))
    wave_df["swell_height_3"] = wave_df.swells.apply(lambda x: x[2].get("height"))
    wave_df["swell_period_3"] = wave_df.swells.apply(lambda x: x[2].get("period"))
    wave_df["swell_direction_3"] = wave_df.swells.apply(lambda x: x[2].get("direction"))

    return wave_df


def get_tide_data(spot_id: str) -> pd.DataFrame:
    response = query(f"{base_url}/tides", {"spotId": spot_id})
    tide_data = json.loads(response.text)
    tide_df = pd.DataFrame(tide_data["data"]["tides"])
    tide_df["surf_location"] = spot_id
    return tide_df


def get_weather_data(spot_id: str) -> pd.DataFrame:
    response = query(f"{base_url}/weather", {"spotId": spot_id})
    weather_data = json.loads(response.text)
    weather_df = pd.DataFrame(weather_data["data"]["weather"])
    weather_df["surf_location"] = spot_id
    return weather_df


def get_conditions_data(spot_id: str) -> pd.DataFrame:
    response = query(f"{base_url}/conditions", {"spotId": spot_id})
    conditions_data = json.loads(response.text)
    conditions_df = pd.DataFrame(conditions_data["data"]["conditions"])
    conditions_df["am_observation"] = conditions_df["am"].apply(
        lambda x: x.get("observation")
    )
    conditions_df["pm_observation"] = conditions_df["pm"].apply(
        lambda x: x.get("observation")
    )
    conditions_df["forecaster"] = conditions_df["forecaster"].apply(
        lambda x: x.get("name")
    )
    conditions_df[
        [
            "timestamp",
            "utcOffset",
            "forecaster",
            "human",
            "observation",
            "am_observation",
            "pm_observation",
        ]
    ]
    return conditions_df
