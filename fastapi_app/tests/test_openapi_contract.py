def _resolve_schema(payload, schema):
    while "$ref" in schema or "allOf" in schema:
        if "$ref" in schema:
            schema = payload["components"]["schemas"][schema["$ref"].split("/")[-1]]
            continue
        schema = schema["allOf"][0]
    return schema


def _response_schema(payload, path, method="get", status="200"):
    return payload["paths"][path][method]["responses"][status]["content"]["application/json"]["schema"]


def _resolved_array_items(payload, schema):
    schema = _resolve_schema(payload, schema)
    assert schema["type"] == "array"
    return _resolve_schema(payload, schema["items"])


def test_openapi_exposes_identifier_account_and_explore_shapes(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    payload = response.json()
    schemas = payload["components"]["schemas"]

    login_request = schemas["LoginRequest"]["properties"]
    assert "identifier" in login_request
    assert "username" not in login_request

    token_response = schemas["TokenResponse"]["properties"]
    assert "account_confirmed" in token_response
    assert "confirmed" not in token_response

    user_create = schemas["UserCreate"]["properties"]
    assert "identifier" in user_create
    assert "username" not in user_create

    user_summary = schemas["UserSummary"]["properties"]
    assert "identifier" in user_summary
    assert "username" not in user_summary

    artifact_manifest = schemas["ArtifactManifestItem"]["properties"]
    assert _resolve_schema(payload, artifact_manifest["role"])["enum"] == [
        "preview_thumbnail",
        "event_preview",
        "trajectory_map",
        "height_profile",
        "speed_acceleration",
        "position_vs_time",
        "heliocentric_orbit",
        "kml",
        "dynamic_analysis_report",
        "station_analysis",
        "analysis_tables",
        "observation_preview",
        "raw_image",
        "raw_video",
        "processed_image",
        "processed_video",
        "brightness_graph",
        "frame_brightness_graph",
        "size_graph",
        "observation_text",
    ]
    assert _resolve_schema(payload, artifact_manifest["type"])["enum"] == [
        "image",
        "video",
        "text",
        "interactive",
    ]
    assert _resolve_schema(payload, artifact_manifest["visibility"])["enum"] == [
        "public"
    ]
    assert _resolve_schema(payload, artifact_manifest["primary_action"])["enum"] == [
        "open",
        "download",
    ]

    explore_response = schemas["ExploreResponse"]["properties"]
    assert explore_response["filters"]["allOf"][0]["$ref"].endswith("/ExploreFilters")
    assert explore_response["kpi"]["allOf"][0]["$ref"].endswith("/ExploreKpi")

    ground = schemas["ExploreGround"]["properties"]
    assert set(ground.keys()) == {"lat", "lng", "slat", "slng"}

    atmospheric_path = schemas["AtmosphericPath"]["properties"]
    assert atmospheric_path["speed_source"]["type"] == "string"
    geometry_points = _resolve_schema(payload, atmospheric_path["geometry_points"])
    assert geometry_points["type"] == "array"
    geometry_point_item = _resolve_schema(payload, geometry_points["items"])
    assert set(geometry_point_item["properties"]) == {
        "step_index",
        "fraction",
        "lat",
        "lng",
        "height_km",
    }

    radiant = schemas["RadiantPayload"]["properties"]
    assert radiant["zenith_attractor"]["type"] == "string"

    orbit = schemas["OrbitPayload"]["properties"]
    assert "0..360" in orbit["mean_anomaly_deg"]["description"]
    assert "fallback" in orbit["mean_anomaly_deg"]["description"].lower()
    assert "fallback" in orbit["epoch"]["description"].lower()

    observation = schemas["MeteorObservation"]["properties"]
    assert "has_ams_coords" in observation

    trail_response = schemas["MeteorObservationTrailResponse"]["properties"]
    assert "has_ams_coords" in trail_response
    assert "has_centroid" in trail_response
    assert "has_centroid2" in trail_response
    trail_points = _resolve_schema(payload, trail_response["trailPoints"])
    trail_item = _resolve_schema(payload, trail_points["items"])
    assert "ams_coord_long" in trail_item["properties"]
    assert "ams_coord_lat" in trail_item["properties"]
    assert "centroid_coord_long" in trail_item["properties"]
    assert "centroid_coord_lat" in trail_item["properties"]
    assert "centroid2_coord_long" in trail_item["properties"]
    assert "centroid2_coord_lat" in trail_item["properties"]


def test_openapi_exposes_filters_station_logs_and_path_lookup(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    payload = response.json()
    schemas = payload["components"]["schemas"]
    paths = payload["paths"]

    assert "/api/events/filters" in paths
    filter_response = (
        paths["/api/events/filters"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert filter_response["$ref"].endswith("/EventFilterOptionsResponse")

    assert "/api/station-logs" in paths
    station_log_get = (
        paths["/api/station-logs"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert station_log_get["type"] == "array"
    assert station_log_get["items"]["$ref"].endswith("/StationLogEntry")

    station_log_post = (
        paths["/api/station-logs"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert station_log_post["$ref"].endswith("/StationLogWriteResponse")

    assert "/api/events/by-path/{date_tag}/{time_tag}" in paths
    parameters = paths["/api/events/by-path/{date_tag}/{time_tag}"]["get"]["parameters"]
    descriptions = {
        item["name"]: item.get("description") or item.get("schema", {}).get("description")
        for item in parameters
    }
    assert descriptions["date_tag"] == "Event date folder in `YYYYMMDD` format."
    assert descriptions["time_tag"] == "Event time folder in `HHMMSS` format."

    assert "/api/insights/{report_name}" not in paths

    for report_name, expected_keys in {
        "/api/insights/cam": {
            "Stasjonsnavn",
            "Kameranavn",
            "ForsteObservasjonsTidspunkt",
            "SisteObervasjonsTidspunkt",
            "DagerMedObservasjoner",
            "DagerSidenSisteObservasjon",
            "Kameraopptak",
            "Hendelser",
            "Krysspeilede",
            "Meteorittkandidater",
        },
        "/api/insights/station": {
            "Stasjonsnavn",
            "ForsteObservasjonsTidspunkt",
            "SisteObervasjonsTidspunkt",
            "DagerMedObservasjoner",
            "DagerSidenSisteObservasjon",
            "Kameraopptak",
            "Hendelser",
            "Krysspeilede",
            "Meteorittkandidater",
        },
        "/api/insights/total": {
            "ForsteObservasjonsTidspunkt",
            "SisteObervasjonsTidspunkt",
            "DagerMedObservasjoner",
            "DagerSidenSisteObservasjon",
            "Kameraopptak",
            "Hendelser",
            "Krysspeilede",
            "Meteorittkandidater",
        },
    }.items():
        report_response = _response_schema(payload, report_name)
        report_item = _resolved_array_items(payload, report_response)
        assert set(report_item["properties"]) == expected_keys

    coordinates_response = _response_schema(payload, "/api/insights/coordinates")
    coordinates_item = _resolved_array_items(payload, coordinates_response)
    assert "properties" in coordinates_item
    assert {
        "id",
        "datetimetag",
        "station_cam",
        "number_of_stations",
        "lat",
        "lng",
        "slat",
        "slng",
        "triangulation",
        "proper_triangulation",
        "ai_score",
    }.issubset(coordinates_item["properties"])

    coordinates_parameters = {item["name"] for item in paths["/api/insights/coordinates"]["get"]["parameters"]}
    assert {
        "from_date",
        "to_date",
        "stations",
        "cross_station_confirmed",
        "candidate",
        "includeDeleted",
    }.issubset(coordinates_parameters)

    user_response = _resolve_schema(
        payload,
        _response_schema(payload, "/api/users/{user_id}"),
    )
    assert "properties" in user_response
    assert {
        "id",
        "identifier",
        "role",
        "user_role",
        "roles",
        "user_level",
        "tutorial_completed",
        "account_confirmed",
    }.issubset(user_response["properties"])
    assert "username" not in user_response["properties"]
    assert "confirmed" not in user_response["properties"]

    admin_response = (
        paths["/api/admin/events"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert admin_response["$ref"].endswith("/AdminMeteorEventListResponse")

    admin_event = schemas["AdminMeteorEvent"]
    assert {
        "datetimetag",
        "date",
        "camera_confirmed",
        "user_confirmed",
        "ratings",
        "positive_ratings",
        "negative_ratings",
    }.issubset(admin_event["properties"])

    public_event = schemas["MeteorEvent"]
    for field in ["camera_confirmed", "user_confirmed", "ratings"]:
        assert field not in public_event["properties"]


def test_openapi_exposes_verification_tutorial_reviews_and_station_network(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    payload = response.json()
    paths = payload["paths"]

    assert "/api/auth/verification/confirm" in paths
    assert "/api/auth/verification/resend" in paths
    assert "/api/tutorial" in paths
    assert "/api/users/{user_id}/reviews" in paths
    assert "/api/station-network" in paths

    schemas = payload["components"]["schemas"]
    assert "StationNetworkResponse" in schemas
    assert "TutorialMetadataResponse" in schemas
    assert "UserReviewHistoryResponse" in schemas
    station_network_station = schemas["StationNetworkStation"]["properties"]
    assert "latitude" in station_network_station
    assert "longitude" in station_network_station

    classification = schemas["MeteorEventClassification"]["properties"]
    assert "user_confirmed" in classification
