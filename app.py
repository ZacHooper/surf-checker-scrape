from scraper.surfline import get_swell_data
import pandas as pd
import json


def lambda_handler(event: dict, context: dict):
    # Allow specific spot ids to be provided in the event
    # Eg to get the swell data for Torquay Surf Beach: {"spot_id": "607776017a3e100333600795"}
    spot_id = event.get("spot_id", "607776017a3e100333600795")

    url = f"https://services.surfline.com/kbyg/spots/forecasts/wave?spotId={spot_id}&units[swellHeight]=M&units[waveHeight]=M"
    report = get_swell_data(url)
    report["timestamp"] = pd.to_datetime(report["timestamp"], unit="s")
    report["timestamp"] = report["timestamp"].dt.tz_localize("Australia/Sydney")
    return {"statusCode": 200, "body": json.dumps(report.to_json(orient="records"))}


if __name__ == "__main__":
    print(lambda_handler({}, {}))
