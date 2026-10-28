"""Pure geographical helpers used by route analysis."""

from math import asin, cos, radians, sin, sqrt


class InvalidRouteGeometryError(ValueError):
    """The routing provider returned geometry that cannot be sampled."""


def distance_km(a: dict, b: dict) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    haversine = sin((lat2 - lat1) / 2) ** 2
    haversine += cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(haversine))


def sample_corridor_points(route: dict, count: int = 5) -> list[tuple[str, float, float, float]]:
    """Sample a route by travelled distance, including both endpoints."""
    coords = route.get("coordinates", [])
    if len(coords) < 2:
        raise InvalidRouteGeometryError("Route contains fewer than two coordinates")
    lengths = [distance_km(coords[index - 1], coords[index]) for index in range(1, len(coords))]
    total = sum(lengths)
    if total <= 0:
        raise InvalidRouteGeometryError("Route contains no usable geometry")

    targets = [total * index / (count - 1) for index in range(count)]
    samples = []
    segment, travelled = 0, 0.0
    for index, target in enumerate(targets):
        while segment < len(lengths) - 1 and travelled + lengths[segment] < target:
            travelled += lengths[segment]
            segment += 1
        fraction = (target - travelled) / lengths[segment]
        start, end = coords[segment], coords[segment + 1]
        lat = start["lat"] + fraction * (end["lat"] - start["lat"])
        lon = start["lon"] + fraction * (end["lon"] - start["lon"])
        label = (
            "origin" if index == 0 else "destination" if index == count - 1 else f"corridor_{index}"
        )
        samples.append((label, lat, lon, target / total))
    return samples
