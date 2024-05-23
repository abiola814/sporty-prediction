import os
import sys
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
import json

# Required to access database module in parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Database  # noqa: E402

season = 2023

app = Flask(__name__)
CORS(app)

database = Database(season)
cache = {
    "team": {"time": None, "data": None},
    "fantasy": {"time": None, "data": None},
    "predictions": {"time": None, "data": None},
}


def recent_cache(date: datetime) -> bool:
    return (datetime.now() - date).total_seconds() < 30


@app.route("/api/teams", methods=["GET"])
def team():
    if cache["team"]["data"] is not None and recent_cache(cache["team"]["time"]):
        teams_data = cache["team"]["data"]
    else:
        teams_data = database.get_teams_data()
        cache["team"]["data"] = teams_data
        cache["team"]["time"] = datetime.now()

    return jsonify(teams_data)


@app.route("/api/fantasy", methods=["GET"])
def fantasy():
    if cache["fantasy"]["data"] is not None and recent_cache(cache["fantasy"]["time"]):
        fantasy_data = cache["fantasy"]["data"]
    else:
        try:
            fantasy_data = database.get_fantasy_data()
            cache["fantasy"]["data"] = fantasy_data
            cache["fantasy"]["time"] = datetime.now()
        except Exception as e:
            # Handle database fetch errors gracefully
            return jsonify({"error": str(e)})
    return jsonify({"fantasy_data": fantasy_data})


@app.route("/api/predictions", methods=["GET"])
def predictions():
    if cache["predictions"]["data"] is not None and recent_cache(
        cache["predictions"]["time"]
    ):
        predictions_data = cache["predictions"]["data"]
    else:
        try:
            predictions_data = database.get_predictions()
            cache["predictions"]["data"] = predictions_data
            cache["predictions"]["time"] = datetime.now()
        except Exception as e:
            # Handle database fetch errors gracefully
            return jsonify({"error": str(e)})
    return jsonify({"predictions_data": predictions_data})


@app.route("/api/scorepredictions", methods=["GET"])
def scorepredictions():
    data = database.get_predictions()
    restructured_data = []

    for item in data:
        new_predictions = []
        for prediction in item["predictions"]:
            home_goals = prediction["prediction"]["homeGoals"]
            away_goals = prediction["prediction"]["awayGoals"]
            total_goals = home_goals + away_goals
            if total_goals >= 3:
                outcome = "Over 2.5 goals"
            elif total_goals == 1:
                if home_goals == 1:
                    outcome = f"{prediction['home']} over 0.5"
                else:
                    outcome = f"{prediction['away']} over 0.5"
            if total_goals >= 2:
                outcome = "Over 1.5 goals"
            else:
                outcome = "Under 1.5 goals"
            new_prediction = {
                "_id": prediction["_id"],
                "datetime": prediction["datetime"].isoformat(),
                "home": prediction["home"],
                "away": prediction["away"],
                "totalGoals": total_goals,
                "outcome": outcome,
                "actual": prediction["actual"],
            }
            new_predictions.append(new_prediction)
        restructured_data.append({"predictions": new_predictions})

    return jsonify(restructured_data)


@app.route("/api/riskpredictions", methods=["GET"])
def riskpredictions():
    data = database.get_predictions()
    restructured_data = []

    for item in data:
        new_predictions = []
        for prediction in item["predictions"]:
            home_goals = prediction["prediction"]["homeGoals"]
            away_goals = prediction["prediction"]["awayGoals"]
            total_goals = home_goals + away_goals
            if total_goals >= 3:
                if home_goals == 1 and away_goals == 1:
                    outcome = "over 2.5 goal and GG"
                else:
                    outcome = "Over 2.5 goals"
            elif total_goals == 1:
                if home_goals == 1:
                    outcome = f"first half {prediction['home']} over 0.5"
                else:
                    outcome = f"first half {prediction['away']} over 0.5"
            if total_goals >= 2:
                if home_goals == 1 and away_goals == 1:
                    outcome = "Over 1.5 goals and GG"
                else:
                    outcome = "Under 1.5 goals"
            else:
                outcome = "Under 4.5 goals"
            new_prediction = {
                "_id": prediction["_id"],
                "datetime": prediction["datetime"].isoformat(),
                "home": prediction["home"],
                "away": prediction["away"],
                "totalGoals": total_goals,
                "outcome": outcome,
                "actual": prediction["actual"],
            }
            new_predictions.append(new_prediction)
        restructured_data.append({"predictions": new_predictions})

    return jsonify(restructured_data)


if __name__ == "__main__":
    app.run(debug=True)
