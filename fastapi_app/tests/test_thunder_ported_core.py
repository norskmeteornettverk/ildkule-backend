from datetime import datetime

import numpy as np

from fastapi_app.app.models import Cam, Event, ObservationCamData, Station, User
from fastapi_app.app.security import create_access_token
from fastapi_app.app.services import user_service
from fastapi_app.app.utils import orbit_solver
from fastapi_app.app.utils.serialization import _orbit_payload


def _observation_kwargs(key: str) -> dict:
    return {
        "observation_key": key,
        "source_hash": f"hash-{key}",
    }


def _auth_header(user: User) -> dict:
    token = create_access_token(
        {
            "username": user.username,
            "user_id": user.id,
            "role": user.role,
            "user_level": user.user_level,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_login_and_user_reads(client, db_session, monkeypatch):
    monkeypatch.setattr(user_service, "verify_password", lambda plain, stored: plain == stored)
    user = User(
        username="test@example.com",
        password="test",
        role="ROLE_USER",
        user_level="1",
        tutorial_completed=False,
        confirmed=True,
    )
    db_session.add(user)
    db_session.commit()

    login = client.post(
        "/api/auth/login",
        json={"identifier": "test@example.com", "password": "test"},
    )
    assert login.status_code == 200
    payload = login.json()
    assert "accessToken" in payload
    assert payload["id"] == user.id
    assert payload["identifier"] == "test@example.com"
    assert payload["account_confirmed"] is True

    headers = {"Authorization": f"Bearer {payload['accessToken']}"}

    get_user = client.get(f"/api/users/{user.id}", headers=headers)
    assert get_user.status_code == 200
    user_payload = get_user.json()
    assert user_payload["id"] == user.id
    assert user_payload["identifier"] == "test@example.com"
    assert user_payload["user_role"] == "ROLE_USER"
    assert user_payload["roles"] == ["ROLE_USER"]
    assert user_payload["user_level"] == "1"
    assert user_payload["tutorial_completed"] is False
    assert user_payload["account_confirmed"] is True
    assert "username" not in user_payload
    assert "confirmed" not in user_payload

    get_users = client.get("/api/users", headers=headers)
    assert get_users.status_code == 200
    assert isinstance(get_users.json().get("users"), list)


def test_password_reset_request_shape(client, db_session, monkeypatch):
    monkeypatch.setattr(user_service, "send_mail", lambda *args, **kwargs: None)
    db_session.add(
        User(
            username="reset@example.com",
            password="irrelevant",
            role="ROLE_USER",
            user_level="1",
            confirmed=True,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/auth/password-reset/request",
        json={"email": "reset@example.com"},
    )
    assert response.status_code == 200
    assert "message" in response.json()


def test_tutorialcomplete_authorization_and_update(client, db_session):
    owner = User(
        username="owner@example.com",
        password="na",
        role="ROLE_USER",
        user_level="0",
        tutorial_completed=False,
        confirmed=True,
    )
    other = User(
        username="other@example.com",
        password="na",
        role="ROLE_USER",
        user_level="0",
        tutorial_completed=False,
        confirmed=True,
    )
    db_session.add_all([owner, other])
    db_session.commit()

    forbidden = client.put(
        f"/api/users/{owner.id}/tutorial-completion",
        headers=_auth_header(other),
        json={"completed": True},
    )
    assert forbidden.status_code == 403

    ok = client.put(
        f"/api/users/{owner.id}/tutorial-completion",
        headers=_auth_header(owner),
        json={"completed": True},
    )
    assert ok.status_code == 200
    assert ok.json()["tutorial_completed"] is True
    assert ok.json()["user_level"] == "1"


def test_event_list_search_filter_and_get(client, db_session):
    station = Station(station_name="larvik")
    cam = Cam(station=station, cam_name="cam1")
    event_a = Event(
        datetimetag="20211101010101",
        location="Viken",
        date=datetime(2021, 11, 1, 1, 1, 1),
        user_confirmed=1,
        camera_confirmed=1,
        track_endheight=45.0,
    )
    event_b = Event(
        datetimetag="20230101010101",
        location="Oslo",
        date=datetime(2023, 1, 1, 1, 1, 1),
        user_confirmed=1,
        track_endheight=15.0,
    )
    db_session.add_all([station, cam, event_a, event_b])
    db_session.commit()

    db_session.add(
        ObservationCamData(
            event_id=event_a.id,
            cam_id=cam.id,
            trail_frames=12,
            **_observation_kwargs("larvik:cam1:2021-11-01T01:01:01.000"),
        )
    )
    db_session.commit()

    listed = client.get("/api/events?page=1&limit=1&orderby=date&order=asc")
    assert listed.status_code == 200
    assert listed.json()["currentPage"] == 1
    assert len(listed.json()["events"]) == 1
    first_event = listed.json()["events"][0]
    assert "times" in first_event
    assert "candidate" in first_event
    assert "final_classification" in first_event
    assert "station_summary" in first_event
    assert "camera_confirmed" not in first_event
    assert "user_confirmed" not in first_event

    page2 = client.get("/api/events?page=2&limit=1")
    assert page2.status_code == 200
    assert page2.json()["currentPage"] == 2

    searched = client.get("/api/events?searchTerm=Viken")
    assert searched.status_code == 200
    assert isinstance(searched.json().get("events"), list)

    filtered = client.get(
        "/api/events?stationName=larvik&year=2021&eventType=Krysspeilet"
    )
    assert filtered.status_code == 200
    assert isinstance(filtered.json(), dict)
    assert len(filtered.json()["events"]) >= 1

    get_one = client.get(f"/api/events/{event_a.id}")
    assert get_one.status_code == 200
    assert get_one.json()["id"] == event_a.id
    assert get_one.json()["event_path"] == "20211101/010101"
    assert get_one.json()["event_type"] == "Krysspeilet"
    assert get_one.json()["preview"]["thumbnail_url"].endswith("/data/20211101/010101/thumbnail.jpg")
    assert any(
        artifact["role"] == "event_preview" and artifact["url"].endswith("/data/20211101/010101/image.jpg")
        for artifact in get_one.json()["event_artifacts"]
    )
    assert get_one.json()["header"]["title"].startswith("Krysspeilet")
    assert get_one.json()["classification"]["final_classification"] == "Meteor"
    assert isinstance(get_one.json()["event_artifacts"], list)
    assert isinstance(get_one.json()["observations"], list)
    assert get_one.json()["observations"][0]["observation_ref"]["station_name"] == "larvik"
    assert get_one.json()["analysis"]["atmospheric_path"]["geometry_points"] is None
    assert get_one.json()["analysis"]["orbit"] == {
        "perihelion_distance_au": None,
        "eccentricity": None,
        "inclination_deg": None,
        "ascending_node_deg": None,
        "argument_of_perihelion_deg": None,
        "mean_anomaly_deg": None,
        "epoch": None,
    }
    assert "camera_confirmed" not in get_one.json()
    assert "user_confirmed" not in get_one.json()
    assert "media" not in get_one.json()
    assert "observation_cam_data" not in get_one.json()

    get_by_tag = client.get("/api/events/by-path/20211101/010101")
    assert get_by_tag.status_code == 200
    assert get_by_tag.json()["id"] == event_a.id


def test_event_filter_options_and_coordinate_report(client, db_session):
    station = Station(station_name="larvik")
    cam = Cam(station=station, cam_name="cam1")
    event = Event(
        datetimetag="20240102030405",
        date=datetime(2024, 1, 2, 3, 4, 5),
        user_confirmed=1,
        camera_confirmed=1,
        track_startheight=70.0,
        track_endheight=55.0,
        track_speed=18.5,
        track_speed_source="average",
        track_startlat=61.2,
        track_startlong=11.3,
        track_endlat=59.1,
        track_endlong=10.2,
        radiant_ra=15.5,
        radiant_dec=-2.5,
        radiant_ecl_lat=4.1,
        radiant_ecl_long=200.2,
        radiant_shower="Perseids",
        radiant_zenith_attractor="uncorrected",
    )
    db_session.add_all([station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            trail_frames=10,
            summary_meteor_probability=87.5,
            **_observation_kwargs("larvik:cam1:2024-01-02T03:04:05.000"),
        )
    )
    db_session.commit()

    filter_options = client.get("/api/events/filters")
    assert filter_options.status_code == 200
    payload = filter_options.json()
    assert "2024" in payload["years"]
    assert "larvik" in payload["stations"]
    assert "Krysspeilet" in payload["eventTypes"]

    coordinates = client.get("/api/insights/coordinates")
    assert coordinates.status_code == 200
    coordinate_row = coordinates.json()[0]
    assert coordinate_row["lat"] == 59.1
    assert coordinate_row["lng"] == 10.2
    assert coordinate_row["slat"] == 61.2
    assert coordinate_row["slng"] == 11.3
    assert coordinate_row["track_speed"] == 18.5
    assert coordinate_row["radiant_shower"] == "Perseids"
    assert coordinate_row["proper_triangulation"] is True
    assert coordinate_row["ai_score"] == 87.5
    assert "StationCam" not in coordinate_row
    assert "NumberOfStations" not in coordinate_row

    detail = client.get(f"/api/events/{event.id}")
    assert detail.status_code == 200
    analysis = detail.json()["analysis"]
    assert analysis["atmospheric_path"]["speed_source"] == "average"
    assert analysis["radiant"]["zenith_attractor"] == "uncorrected"
    orbit = analysis["orbit"]
    assert set(orbit) == {
        "perihelion_distance_au",
        "eccentricity",
        "inclination_deg",
        "ascending_node_deg",
        "argument_of_perihelion_deg",
        "mean_anomaly_deg",
        "epoch",
    }
    assert orbit["epoch"] == "2024-01-02T03:04:05+00:00"
    assert orbit["perihelion_distance_au"] is not None
    assert orbit["eccentricity"] is not None
    assert orbit["inclination_deg"] is not None
    assert orbit["ascending_node_deg"] is not None
    assert orbit["argument_of_perihelion_deg"] is not None
    assert orbit["mean_anomaly_deg"] is not None
    assert 0 <= orbit["mean_anomaly_deg"] < 360


def test_orbit_payload_wraps_elliptic_mean_anomaly_to_0_360():
    orbit = _orbit_payload(
        Event(
            track_speed=29.6,
            track_speed_source="average",
            radiant_ra=120.86,
            radiant_dec=26.66,
            radiant_ecl_long=117.45,
            radiant_ecl_lat=6.12,
            radiant_zenith_attractor="uncorrected",
            date=datetime(2022, 1, 5, 23, 42, 19),
        )
    )

    assert orbit["eccentricity"] < 1
    assert 0 <= orbit["mean_anomaly_deg"] < 360


def test_build_orbit_payload_falls_back_when_observation_solve_is_far_off(monkeypatch):
    event = Event(
        track_speed=41.3,
        radiant_ra=230.92,
        radiant_dec=50.30,
        radiant_ecl_long=200.28,
        radiant_ecl_lat=64.57,
        date=datetime(2022, 1, 3, 18, 18, 52),
    )

    monkeypatch.setattr(
        orbit_solver,
        "_solve_observation_candidate",
        lambda *_args, **_kwargs: orbit_solver._ObservationOrbitCandidate(
            payload={
                "perihelion_distance_au": 0.982316,
                "eccentricity": 3.024395,
                "inclination_deg": 37.435,
                "ascending_node_deg": 70.872,
                "argument_of_perihelion_deg": 42.642,
                "mean_anomaly_deg": -393.115,
                "epoch": "2022-01-03T18:18:52+00:00",
            },
            diagnostics=orbit_solver._PathFitDiagnostics(
                track_count=2,
                fit_point_count=8,
                median_residual_km=0.12,
                max_residual_km=0.31,
            ),
        ),
    )

    orbit = orbit_solver.build_orbit_payload(
        event,
        [ObservationCamData(**_observation_kwargs("guard:far"))],
        fallback_factory=orbit_solver._legacy_stat_orbit,
    )

    assert orbit == orbit_solver._legacy_stat_orbit(event)


def test_build_orbit_payload_keeps_observation_solve_when_it_is_close(monkeypatch):
    event = Event(
        track_speed=41.3,
        radiant_ra=230.92,
        radiant_dec=50.30,
        radiant_ecl_long=200.28,
        radiant_ecl_lat=64.57,
        date=datetime(2022, 1, 3, 18, 18, 52),
    )
    fallback = orbit_solver._legacy_stat_orbit(event)
    observed = {
        **fallback,
        "perihelion_distance_au": round(fallback["perihelion_distance_au"] + 0.001, 6),
        "eccentricity": round(fallback["eccentricity"] + 0.02, 6),
        "inclination_deg": round(fallback["inclination_deg"] + 0.4, 3),
        "ascending_node_deg": round(fallback["ascending_node_deg"] + 0.5, 3),
        "argument_of_perihelion_deg": round(fallback["argument_of_perihelion_deg"] + 0.6, 3),
        "mean_anomaly_deg": round(fallback["mean_anomaly_deg"] + 6.0, 3),
    }
    monkeypatch.setattr(
        orbit_solver,
        "_solve_observation_candidate",
        lambda *_args, **_kwargs: orbit_solver._ObservationOrbitCandidate(
            payload=observed,
            diagnostics=orbit_solver._PathFitDiagnostics(
                track_count=2,
                fit_point_count=12,
                median_residual_km=0.22,
                max_residual_km=0.55,
            ),
        ),
    )

    orbit = orbit_solver.build_orbit_payload(
        event,
        [ObservationCamData(**_observation_kwargs("guard:close"))],
        fallback_factory=orbit_solver._legacy_stat_orbit,
    )

    assert orbit == observed


def test_build_orbit_payload_falls_back_when_validation_metrics_are_weak(monkeypatch):
    event = Event(
        track_speed=41.3,
        radiant_ra=230.92,
        radiant_dec=50.30,
        radiant_ecl_long=200.28,
        radiant_ecl_lat=64.57,
        date=datetime(2022, 1, 3, 18, 18, 52),
    )
    fallback = orbit_solver._legacy_stat_orbit(event)
    observed = {
        **fallback,
        "perihelion_distance_au": round(fallback["perihelion_distance_au"] + 0.002, 6),
        "eccentricity": round(fallback["eccentricity"] + 0.04, 6),
        "inclination_deg": round(fallback["inclination_deg"] + 0.8, 3),
        "ascending_node_deg": round(fallback["ascending_node_deg"] + 0.4, 3),
        "argument_of_perihelion_deg": round(fallback["argument_of_perihelion_deg"] + 1.0, 3),
        "mean_anomaly_deg": round(fallback["mean_anomaly_deg"] + 8.0, 3),
    }
    monkeypatch.setattr(
        orbit_solver,
        "_solve_observation_candidate",
        lambda *_args, **_kwargs: orbit_solver._ObservationOrbitCandidate(
            payload=observed,
            diagnostics=orbit_solver._PathFitDiagnostics(
                track_count=2,
                fit_point_count=10,
                median_residual_km=0.41,
                max_residual_km=0.92,
            ),
        ),
    )

    orbit = orbit_solver.build_orbit_payload(
        event,
        [ObservationCamData(**_observation_kwargs("guard:diagnostics"))],
        fallback_factory=orbit_solver._legacy_stat_orbit,
    )

    assert orbit == fallback


def test_build_orbit_payload_reuses_fallback_mean_anomaly_when_only_epoch_cluster_is_unstable(
    monkeypatch,
):
    event = Event(
        track_speed=41.3,
        radiant_ra=230.92,
        radiant_dec=50.30,
        radiant_ecl_long=200.28,
        radiant_ecl_lat=64.57,
        date=datetime(2022, 1, 3, 18, 18, 52),
    )
    fallback = orbit_solver._legacy_stat_orbit(event)
    observed = {
        **fallback,
        "perihelion_distance_au": round(fallback["perihelion_distance_au"] + 0.003, 6),
        "eccentricity": round(fallback["eccentricity"] + 0.03, 6),
        "inclination_deg": round(fallback["inclination_deg"] + 0.9, 3),
        "ascending_node_deg": round(fallback["ascending_node_deg"] + 0.7, 3),
        "argument_of_perihelion_deg": round(fallback["argument_of_perihelion_deg"] + 1.4, 3),
        "mean_anomaly_deg": round(fallback["mean_anomaly_deg"] + 28.0, 3),
        "epoch": "2022-01-03T18:18:52.500000+00:00",
    }
    monkeypatch.setattr(
        orbit_solver,
        "_solve_observation_candidate",
        lambda *_args, **_kwargs: orbit_solver._ObservationOrbitCandidate(
            payload=observed,
            diagnostics=orbit_solver._PathFitDiagnostics(
                track_count=2,
                fit_point_count=14,
                median_residual_km=0.18,
                max_residual_km=0.44,
            ),
        ),
    )

    orbit = orbit_solver.build_orbit_payload(
        event,
        [ObservationCamData(**_observation_kwargs("guard:mean-anomaly"))],
        fallback_factory=orbit_solver._legacy_stat_orbit,
    )

    assert orbit["perihelion_distance_au"] == observed["perihelion_distance_au"]
    assert orbit["eccentricity"] == observed["eccentricity"]
    assert orbit["inclination_deg"] == observed["inclination_deg"]
    assert orbit["ascending_node_deg"] == observed["ascending_node_deg"]
    assert orbit["argument_of_perihelion_deg"] == observed["argument_of_perihelion_deg"]
    assert orbit["mean_anomaly_deg"] == fallback["mean_anomaly_deg"]
    assert orbit["epoch"] == fallback["epoch"]


def test_build_orbit_payload_forwards_explicit_path_policy(monkeypatch):
    event = Event(
        track_speed=41.3,
        radiant_ra=230.92,
        radiant_dec=50.30,
        radiant_ecl_long=200.28,
        radiant_ecl_lat=64.57,
        date=datetime(2022, 1, 3, 18, 18, 52),
    )
    fallback = orbit_solver._legacy_stat_orbit(event)
    observed_path_policy = {}

    def fake_solve_observation_candidate(_event, _observations, path_policy=orbit_solver._RUNTIME_PATH_POLICY):
        observed_path_policy["value"] = path_policy
        return orbit_solver._ObservationOrbitCandidate(
            payload=fallback,
            diagnostics=orbit_solver._PathFitDiagnostics(
                track_count=2,
                fit_point_count=8,
                median_residual_km=0.18,
                max_residual_km=0.42,
            ),
        )

    monkeypatch.setattr(orbit_solver, "_solve_observation_candidate", fake_solve_observation_candidate)

    orbit = orbit_solver.build_orbit_payload(
        event,
        [ObservationCamData(**_observation_kwargs("policy:explicit"))],
        fallback_factory=orbit_solver._legacy_stat_orbit,
        path_policy="policy_b",
    )

    assert observed_path_policy["value"] == "policy_b"
    assert orbit == fallback


def test_select_best_path_model_honors_preferred_policy_name(monkeypatch):
    samples = [
        orbit_solver._ProjectedPathSample(0, 0.0, 0.0, 0.10, 3),
        orbit_solver._ProjectedPathSample(1, 1.0, 10.0, 0.10, 3),
        orbit_solver._ProjectedPathSample(0, 2.0, 20.0, 0.10, 2),
        orbit_solver._ProjectedPathSample(1, 3.0, 30.0, 0.10, 2),
    ]

    monkeypatch.setattr(orbit_solver, "_filter_samples_for_policy", lambda _samples, _policy: list(_samples))
    monkeypatch.setattr(orbit_solver, "_estimate_track_weight_scales", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(orbit_solver, "_trim_temporal_outliers", lambda _samples, _model: list(_samples))

    def fake_solve_linear_path_model(_samples, _track_count, policy_name, track_weight_scales=None):
        residuals = {
            "policy_a": (0.02, 0.04),
            "policy_b": (0.50, 0.75),
        }[policy_name]
        return orbit_solver._PathModelSolution(
            policy_name=policy_name,
            speed_kms=42.0,
            intercepts=np.array([0.0, 0.0]),
            time_center=0.0,
            scalar_residual_median_km=residuals[0],
            scalar_residual_max_km=residuals[1],
            timing_spread_seconds=0.0,
        )

    def fake_solve_quadratic_path_model(_samples, _track_count, track_weight_scales=None):
        return orbit_solver._PathModelSolution(
            policy_name="policy_c",
            speed_kms=42.0,
            intercepts=np.array([0.0, 0.0]),
            time_center=0.0,
            scalar_residual_median_km=0.25,
            scalar_residual_max_km=0.35,
            acceleration_kms2=0.12,
            timing_spread_seconds=0.0,
        )

    monkeypatch.setattr(orbit_solver, "_solve_linear_path_model", fake_solve_linear_path_model)
    monkeypatch.setattr(orbit_solver, "_solve_quadratic_path_model", fake_solve_quadratic_path_model)

    selected = orbit_solver._select_best_path_model(samples, 2, preferred_policy_name="policy_b")

    assert selected is not None
    solved_model, selected_samples = selected
    assert solved_model.policy_name == "policy_b"
    assert selected_samples == samples


def test_sample_weight_penalizes_edge_points_more_than_center_points():
    edge = orbit_solver._ProjectedPathSample(
        track_index=0,
        timestamp=0.0,
        scalar_km=10.0,
        residual_km=0.2,
        edge_distance=0,
    )
    near_edge = orbit_solver._ProjectedPathSample(
        track_index=0,
        timestamp=0.0,
        scalar_km=10.0,
        residual_km=0.2,
        edge_distance=1,
    )
    center = orbit_solver._ProjectedPathSample(
        track_index=0,
        timestamp=0.0,
        scalar_km=10.0,
        residual_km=0.2,
        edge_distance=3,
    )

    assert orbit_solver._sample_weight(edge) < orbit_solver._sample_weight(near_edge) < orbit_solver._sample_weight(center)


def test_trim_endpoint_outliers_drops_obvious_tail_spike():
    samples = [
        orbit_solver._ProjectedPathSample(0, 0.0, 0.0, 0.10, 3),
        orbit_solver._ProjectedPathSample(0, 1.0, 1.0, 0.12, 2),
        orbit_solver._ProjectedPathSample(0, 2.0, 2.0, 0.11, 1),
        orbit_solver._ProjectedPathSample(0, 3.0, 3.0, 0.13, 1),
        orbit_solver._ProjectedPathSample(0, 4.0, 4.0, 0.14, 2),
        orbit_solver._ProjectedPathSample(0, 5.0, 5.0, 0.95, 3),
    ]

    trimmed = orbit_solver._trim_endpoint_outliers(samples)

    assert len(trimmed) == 5
    assert [item.residual_km for item in trimmed] == [0.10, 0.12, 0.11, 0.13, 0.14]


def test_trim_temporal_outliers_removes_scalar_spike_when_tracks_survive():
    samples = [
        orbit_solver._ProjectedPathSample(0, 0.0, 0.0, 0.10, 3),
        orbit_solver._ProjectedPathSample(1, 1.0, 10.0, 0.10, 3),
        orbit_solver._ProjectedPathSample(0, 2.0, 20.0, 0.10, 2),
        orbit_solver._ProjectedPathSample(1, 3.0, 30.0, 0.10, 2),
        orbit_solver._ProjectedPathSample(0, 4.0, 50.0, 0.10, 1),
    ]

    trimmed = orbit_solver._trim_temporal_outliers(
        samples,
        speed_kms=10.0,
        intercepts=np.array([0.0, 0.0]),
        time_center=0.0,
    )

    assert len(trimmed) == 4
    assert [item.scalar_km for item in trimmed] == [0.0, 10.0, 20.0, 30.0]


def test_solve_linear_path_model_accepts_speed_just_under_150_kms():
    samples = [
        orbit_solver._ProjectedPathSample(0, 0.0, 0.0, 0.10, 3),
        orbit_solver._ProjectedPathSample(1, 0.2, 29.8, 0.10, 3),
        orbit_solver._ProjectedPathSample(0, 0.4, 59.6, 0.10, 2),
        orbit_solver._ProjectedPathSample(1, 0.6, 89.4, 0.10, 2),
    ]

    solved = orbit_solver._solve_linear_path_model(samples, 2, "policy_a")

    assert solved is not None
    assert abs(solved.speed_kms - 149.0) < 1e-6


def test_solve_linear_path_model_still_rejects_speed_over_150_kms():
    samples = [
        orbit_solver._ProjectedPathSample(0, 0.0, 0.0, 0.10, 3),
        orbit_solver._ProjectedPathSample(1, 0.2, 30.2, 0.10, 3),
        orbit_solver._ProjectedPathSample(0, 0.4, 60.4, 0.10, 2),
        orbit_solver._ProjectedPathSample(1, 0.6, 90.6, 0.10, 2),
    ]

    solved = orbit_solver._solve_linear_path_model(samples, 2, "policy_a")

    assert solved is None


def test_event_detail_exposes_sampled_geometry_points_when_solved_path_exists(client, db_session):
    station = Station(station_name="alta")
    cam = Cam(station=station, cam_name="cam7")
    event = Event(
        datetimetag="20240203040506",
        location="Finnmark",
        date=datetime(2024, 2, 3, 4, 5, 6),
        user_confirmed=1,
        camera_confirmed=1,
        track_startheight=86.0,
        track_endheight=24.0,
        track_startlat=70.1,
        track_startlong=24.9,
        track_endlat=69.2,
        track_endlong=23.4,
    )
    db_session.add_all([station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            **_observation_kwargs("alta:cam7:2024-02-03T04:05:06.000"),
        )
    )
    db_session.commit()

    response = client.get(f"/api/events/{event.id}")

    assert response.status_code == 200
    geometry_points = response.json()["analysis"]["atmospheric_path"]["geometry_points"]
    assert len(geometry_points) == 17
    assert geometry_points[0] == {
        "step_index": 0,
        "fraction": 0.0,
        "lat": 70.1,
        "lng": 24.9,
        "height_km": 86.0,
    }
    assert geometry_points[-1] == {
        "step_index": 16,
        "fraction": 1.0,
        "lat": 69.2,
        "lng": 23.4,
        "height_km": 24.0,
    }


def test_insight_cam_and_station(client, db_session):
    station = Station(station_name="sorreisa")
    cam = Cam(station=station, cam_name="cam2")
    event = Event(
        datetimetag="20211102010101",
        date=datetime(2021, 11, 2, 1, 1, 1),
        user_confirmed=1,
        track_startheight=60.0,
        track_endheight=50.0,
    )
    db_session.add_all([station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            trail_frames=10,
            **_observation_kwargs("sorreisa:cam2:2021-11-02T01:01:01.000"),
        )
    )
    db_session.commit()

    cam_report = client.get("/api/insights/cam")
    assert cam_report.status_code == 200
    cam_row = cam_report.json()[0]
    assert set(cam_row) == {
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
    }
    assert cam_row["Stasjonsnavn"] == "Sorreisa"
    assert cam_row["Kameranavn"] == "cam2"

    station_report = client.get("/api/insights/station")
    assert station_report.status_code == 200
    station_row = station_report.json()[0]
    assert set(station_row) == {
        "Stasjonsnavn",
        "ForsteObservasjonsTidspunkt",
        "SisteObervasjonsTidspunkt",
        "DagerMedObservasjoner",
        "DagerSidenSisteObservasjon",
        "Kameraopptak",
        "Hendelser",
        "Krysspeilede",
        "Meteorittkandidater",
    }
    assert station_row["Stasjonsnavn"] == "Sorreisa"

    total_report = client.get("/api/insights/total")
    assert total_report.status_code == 200
    total_row = total_report.json()[0]
    assert set(total_row) == {
        "ForsteObservasjonsTidspunkt",
        "SisteObervasjonsTidspunkt",
        "DagerMedObservasjoner",
        "DagerSidenSisteObservasjon",
        "Kameraopptak",
        "Hendelser",
        "Krysspeilede",
        "Meteorittkandidater",
    }


def test_explore_and_csv_export(client, db_session):
    station = Station(station_name="alta")
    cam = Cam(station=station, cam_name="cam9")
    event = Event(
        datetimetag="20260203040506",
        location="Finnmark",
        date=datetime(2026, 2, 3, 4, 5, 6),
        user_confirmed=1,
        camera_confirmed=1,
        track_startlat=70.4,
        track_startlong=24.2,
        track_startheight=90.0,
        track_endheight=22.0,
        track_speed=20.0,
        radiant_ra=12.3,
        radiant_dec=-1.2,
        track_endlat=69.9,
        track_endlong=23.3,
    )
    db_session.add_all([station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            summary_latitude=69.6,
            summary_longitude=23.1,
            summary_elevation=20,
            summary_meteor_probability=73.2,
            **_observation_kwargs("alta:cam9:2026-02-03T04:05:06.000"),
        )
    )
    db_session.commit()

    response = client.get(
        "/api/explore?from_date=2026-02-01&to_date=2026-02-05&stations=alta&cross_station_confirmed=true&candidate=true"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["kpi"]["total_events"] == 1
    assert payload["events"][0]["candidate"]["is_candidate"] is True
    assert payload["events"][0]["ground"]["lat"] == 69.9
    assert payload["events"][0]["ground"]["slat"] == 70.4
    assert payload["events"][0]["ground"]["slng"] == 24.2
    assert payload["events"][0]["ai_score"] == 73.2

    csv_response = client.get("/api/explore/export?format=csv&candidate=true")
    assert csv_response.status_code == 200
    assert "event_path,title,utc_time,local_time" in csv_response.text
    assert "20260203/040506" in csv_response.text
