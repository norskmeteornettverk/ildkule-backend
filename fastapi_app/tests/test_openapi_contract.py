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

    explore_response = schemas["ExploreResponse"]["properties"]
    assert explore_response["filters"]["allOf"][0]["$ref"].endswith("/ExploreFilters")
    assert explore_response["kpi"]["allOf"][0]["$ref"].endswith("/ExploreKpi")

    ground = schemas["ExploreGround"]["properties"]
    assert set(ground.keys()) == {"lat", "lng", "slat", "slng"}


def test_openapi_exposes_filters_station_logs_and_path_lookup(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    payload = response.json()
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
