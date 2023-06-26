import base64
import json
from datetime import datetime

import pandas as pd
import boto3

from scraper.surfline import get_swell_data

s3 = boto3.client("s3")


def lambda_handler(event: dict, context: dict):
    body = json.loads(event["body"])
    # Allow specific spot ids to be provided in the event
    # Eg to get the swell data for Torquay Surf Beach: {"spot_id": "607776017a3e100333600795"}
    spot_id = body.get("spot_id", "607776017a3e100333600795")
    longitude = body.get("longitude", None)
    latitude = body.get("latitude", None)

    image_encoded = body.get("image", None)
    if image_encoded is None:
        return {"statusCode": 400, "body": "No image provided"}

    image = base64.b64decode(image_encoded)

    now = datetime.utcnow()
    now_str = now.strftime("%Y%m%d_%H%M%S")

    # Save the image to S3
    s3.put_object(
        Bucket="surf-pics", Key=f"{now_str}_{longitude}_{latitude}.jpeg", Body=image
    )

    url = f"https://services.surfline.com/kbyg/spots/forecasts/wave?spotId={spot_id}&units[swellHeight]=M&units[waveHeight]=M"
    report = get_swell_data(url)
    report["timestamp"] = pd.to_datetime(report["timestamp"], unit="s")
    report["timestamp"] = report["timestamp"].dt.tz_localize("Australia/Sydney")
    return {"statusCode": 200, "body": json.dumps(report.to_json(orient="records"))}


if __name__ == "__main__":
    with open("encoded-20230626223217.txt", "r") as f:
        image_encoded = f.read()
    print(
        lambda_handler(
            {
                "surf_id": "5842041f4e65fad6a7708c0b",
                "image": image_encoded,
                "longitude": 151.209900,
                "latitude": -33.865143,
            },
            {},
        )
    )
