from enum import Enum
from typing import Iterator

import numpy as np

from skyfield.api import Angle

from starplot.data import load
from starplot.models.base import SkyObject, SkyObjectManager


class PlanetName(str, Enum):
    """Planets ... Coming Soon: Pluto :)"""

    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"


PLANET_LABELS_DEFAULT = {p: p.value.upper() for p in PlanetName}

PLANET_SIZE_KM = {
    PlanetName.MERCURY: 2_440,
    PlanetName.VENUS: 6_052,
    PlanetName.MARS: 3_390,
    PlanetName.JUPITER: 69_911,
    PlanetName.SATURN: 58_232,
    PlanetName.URANUS: 25_362,
    PlanetName.NEPTUNE: 24_622,
}
"""
Planet sizes from NASA:

https://science.nasa.gov/resource/solar-system-sizes/

Retrieved on 28-Jan-2024
"""


class PlanetManager(SkyObjectManager):
    @classmethod
    def all(cls, dt, ephemeris: str = "de421_2001.bsp"):
        ephemeris = load(ephemeris)
        timescale = load.timescale().from_datetime(dt)
        earth = ephemeris["earth"]

        for p in PlanetName:
            planet = ephemeris[f"{p.value} barycenter"]
            astrometric = earth.at(timescale).observe(planet)
            ra, dec, distance = astrometric.radec()

            # angular diameter:
            # https://rhodesmill.org/skyfield/examples.html#what-is-the-angular-diameter-of-a-planet-given-its-radius
            radius_km = PLANET_SIZE_KM[p]
            apparent_diameter_degrees = Angle(
                radians=np.arcsin(radius_km / distance.km) * 2.0
            ).degrees

            yield Planet(
                ra=ra.hours,
                dec=dec.degrees,
                name=p,
                apparent_size=apparent_diameter_degrees,
            )

    @classmethod
    def find(cls):
        raise NotImplementedError

    @classmethod
    def get(cls, name: str, dt, ephemeris: str = "de421_2001.bsp"):
        for p in cls.all(dt, ephemeris):
            if p.name == name:
                return p

        return None


class Planet(SkyObject):
    """Planet model."""

    _manager = PlanetManager

    name: str
    """Name of the planet"""

    apparent_size: float
    """Apparent size (degrees)"""

    def __init__(self, ra: float, dec: float, name: str, apparent_size: float) -> None:
        super().__init__(ra, dec)
        self.name = name
        self.apparent_size = apparent_size

    @classmethod
    def all(dt, ephemeris: str = "de421_2001.bsp") -> Iterator["Planet"]:
        """
        Iterator for getting all planets at a specific date/time.

        Args:
            dt: Datetime you want the planets for (must be timezone aware!)
            ephemeris: Ephemeris to use for calculating planet positions (see [Skyfield's documentation](https://rhodesmill.org/skyfield/planets.html) for details)
        """
        pass

    @classmethod
    def get(dt, ephemeris: str = "de421_2001.bsp") -> "Planet":
        """
        Get a planet for a specific date/time.

        Args:
            dt: Datetime you want the planet for (must be timezone aware!)
            ephemeris: Ephemeris to use for calculating planet positions (see [Skyfield's documentation](https://rhodesmill.org/skyfield/planets.html) for details)
        """
        pass
