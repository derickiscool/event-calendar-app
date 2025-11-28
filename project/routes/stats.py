from flask import Blueprint, render_template, jsonify
from project.db import get_mongo_client

stats_bp = Blueprint('stats', __name__)

# 2. The Data API (Complex Query)
@stats_bp.route("/stats", methods=["GET"])
def get_stats():
    """
    Fetches stats from MongoDB using an Aggregation Pipeline.
    Calculates total funding and activity count per year.
    """
    client = get_mongo_client()
    if not client: 
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        db = client.get_database("event_calendar")
        
        # Aggregation Pipeline:
        pipeline = [
            {"$sort": {"year": 1}},
            {"$project": {
                "_id": 0,
                "year": 1,
                "total_funding": {"$sum": "$gov_contributions.amount_mil"},
                "total_activities": {"$sum": "$activities.number"}
            }}
        ]
        
        stats = list(db.statistics.aggregate(pipeline))
        
        response_data = {
            "years": [s['year'] for s in stats],
            "funding": [round(s['total_funding'], 2) for s in stats],
            "activities": [s['total_activities'] for s in stats]
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        client.close()