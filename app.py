import requests
from bs4 import BeautifulSoup as bs4
from datetime import datetime, timedelta
import pytz
import re
from scraper.surfline import (
    get_surf_height,
    get_surf_rating,
    get_surf_conditions_card,
    get_surf_description,
    get_swell_data,
)
import pandas as pd
import json

tz = pytz.timezone("Australia/Sydney")


def scrape_surfline(url: str) -> dict:
    # user agent header
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = bs4(response.text, "html.parser")

    # get domain from url
    domain = url.split("/")[2]

    # get surf spot from url
    spot = url.split("/")[4]

    # Get surf conditions
    conditions_card = get_surf_conditions_card(soup)

    # get surf height
    surf_height, surf_height_unit = get_surf_height(conditions_card)

    # get surf rating
    surf_rating = get_surf_rating(conditions_card)

    # get surf description
    surf_description = get_surf_description(conditions_card)

    return {
        "website": domain,
        "time_of_day": datetime.now(tz=tz).strftime("%H:%M:%S"),
        "surf_spot": spot,
        "surf_height": surf_height,
        "surf_height_unit": surf_height_unit,
        "surf_rating": surf_rating,
        "surf_description": surf_description,
    }


def lambda_handler(event, context):
    url = "https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=607776017a3e100333600795&units[swellHeight]=M&units[waveHeight]=M"
    report = get_swell_data(url)
    report["timestamp"] = pd.to_datetime(report["timestamp"], unit="s")
    report["timestamp"] = report["timestamp"].dt.tz_localize("Australia/Sydney")
    return {"statusCode": 200, "body": json.dumps(report.to_json(orient="records"))}


if __name__ == "__main__":
    print(lambda_handler(None, None))
