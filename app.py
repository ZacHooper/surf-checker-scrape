import base64
import json
from datetime import datetime

import pandas as pd
import boto3

from sqlalchemy import create_engine, text

from scraper.surfline import (
    get_wind_data,
    get_wave_data,
    get_tide_data,
    get_weather_data,
    get_conditions_data,
    get_surf_location_from_id,
)

s3 = boto3.client("s3")
secrets_client = boto3.client("secretsmanager", region_name="ap-southeast-2")


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
    key = f"{now_str}_{longitude}_{latitude}.jpeg"

    # Save the image to S3
    s3.put_object(
        Bucket="surf-pics", Key=f"{now_str}_{longitude}_{latitude}.jpeg", Body=image
    )

    spots = [
        "607776017a3e100333600795",  # Torquay Surf Beach
        "5842041f4e65fad6a7708c0b",  # Jan Juc
        "5842041f4e65fad6a7708c0c",  # 13th Beach
        "584204204e65fad6a77099c7",  # Bells Beach
    ]
    wind_data = pd.DataFrame()
    wave_data = pd.DataFrame()
    tide_data = pd.DataFrame()
    weather_data = pd.DataFrame()
    conditions_data = pd.DataFrame()
    for spot_id in spots:
        # Get the data from Surfline
        wind_data = pd.concat([wind_data, get_wind_data(spot_id)])
        wave_data = pd.concat([wave_data, get_wave_data(spot_id)])
        tide_data = pd.concat([tide_data, get_tide_data(spot_id)])
        weather_data = pd.concat([weather_data, get_weather_data(spot_id)])
        conditions_data = pd.concat([conditions_data, get_conditions_data(spot_id)])

    # Get secret from AWS Secrets Manager
    secrets_client = boto3.client("secretsmanager", region_name="ap-southeast-2")
    raw_string = secrets_client.get_secret_value(SecretId="prod/surf-checker/conn_str")[
        "SecretString"
    ]
    conn_str = json.loads(raw_string)["connection_str"]

    # Save the data to the database
    engine = create_engine(conn_str)
    with engine.begin() as conn:
        qry = """--sql
        INSERT INTO reports (longitude, latitude, photo_key, waves, wind, tide, weather, report)
        VALUES (:longitude, :latitude, :photo_key, :waves, :wind, :tide, :weather, :report)
        """
        params = (
            {
                "longitude": longitude,
                "latitude": latitude,
                "photo_key": key,
                "waves": wave_data.to_json(orient="records"),
                "wind": wind_data.to_json(orient="records"),
                "tide": tide_data.to_json(orient="records"),
                "weather": weather_data.to_json(orient="records"),
                "report": conditions_data.to_json(orient="records"),
            },
        )
        conn.execute(text(qry), params)
    return {"statusCode": 200, "body": "Surf report saved"}


if __name__ == "__main__":
    # lambda_handler({"body": json.dumps({"image": "test"})}, {})

    spots = [
        "607776017a3e100333600795",  # Torquay Surf Beach
        "5842041f4e65fad6a7708c0b",  # Jan Juc
        "5842041f4e65fad6a7708c0c",  # 13th Beach
        "584204204e65fad6a77099c7",  # Bells Beach
    ]
    wind_data = pd.DataFrame()
    wave_data = pd.DataFrame()
    tide_data = pd.DataFrame()
    weather_data = pd.DataFrame()
    conditions_data = pd.DataFrame()
    for spot_id in spots:
        # Get the data from Surfline
        wind_data = pd.concat([wind_data, get_wind_data(spot_id)])
        wave_data = pd.concat([wave_data, get_wave_data(spot_id)])
        tide_data = pd.concat([tide_data, get_tide_data(spot_id)])
        weather_data = pd.concat([weather_data, get_weather_data(spot_id)])
        conditions_data = pd.concat([conditions_data, get_conditions_data(spot_id)])

    all_data = (
        pd.merge(
            wind_data,
            wave_data,
            on=["timestamp", "surf_location"],
            suffixes=("_wind", "_wave"),
        )
        .merge(tide_data, on=["timestamp", "surf_location"], suffixes=("", "_tide"))
        .merge(
            weather_data, on=["timestamp", "surf_location"], suffixes=("", "_weather")
        )
        .merge(
            conditions_data,
            on=["timestamp", "surf_location"],
            how="left",
            suffixes=("", "_conditions"),
        )
    )
    all_data["surf_location_name"] = all_data["surf_location"].apply(
        lambda x: get_surf_location_from_id(x)
    )
