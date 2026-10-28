import pytest

from services.geo import InvalidRouteGeometryError, sample_corridor_points


def test_samples_corridor_by_distance_with_endpoints():
    route = {
        "coordinates": [
            {"lat": 0.0, "lon": 0.0},
            {"lat": 0.0, "lon": 1.0},
            {"lat": 0.0, "lon": 3.0},
        ]
    }

    points = sample_corridor_points(route, count=3)

    assert [point[0] for point in points] == ["origin", "corridor_1", "destination"]
    assert points[0][1:3] == (0.0, 0.0)
    assert points[-1][1:3] == (0.0, 3.0)
    assert points[1][2] == pytest.approx(1.5)


@pytest.mark.parametrize(
    "coordinates",
    [[], [{"lat": 0.0, "lon": 0.0}], [{"lat": 0.0, "lon": 0.0}] * 2],
)
def test_rejects_unsampleable_route_geometry(coordinates):
    with pytest.raises(InvalidRouteGeometryError):
        sample_corridor_points({"coordinates": coordinates})
