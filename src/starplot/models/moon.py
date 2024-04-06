import numpy as np
from skyfield.api import Angle

from starplot.data import load
from starplot.models.base import SkyObject, SkyObjectManager


class MoonManager(SkyObjectManager):
    @classmethod
    def all(cls):
        raise NotImplementedError

    @classmethod
    def find(cls):
        raise NotImplementedError

    @classmethod
    def get(cls, dt, ephemeris: str = "de421_2001.bsp"):
        RADIUS_KM = 1_740

        ephemeris = load(ephemeris)
        timescale = load.timescale().from_datetime(dt)
        earth, moon = ephemeris["earth"], ephemeris["moon"]
        astrometric = earth.at(timescale).observe(moon)
        ra, dec, distance = astrometric.radec()

        apparent_diameter_degrees = Angle(
            radians=np.arcsin(RADIUS_KM / distance.km) * 2.0
        ).degrees

        return Moon(
            ra=ra.hours,
            dec=dec.degrees,
            name="Moon",
            apparent_size=apparent_diameter_degrees,
        )


class Moon(SkyObject):
    """Moon model. Only used for Earth's moon right now, but will potentially represent other planets' moons in future versions."""

    _manager = MoonManager

    name: str = "Moon"
    """Name of the moon"""

    apparent_size: float
    """Apparent size (degrees)"""

    def __init__(self, ra: float, dec: float, name: str, apparent_size: float) -> None:
        super().__init__(ra, dec)
        self.name = name
        self.apparent_size = apparent_size

    @classmethod
    def get(dt, ephemeris: str = "de421_2001.bsp"):
        """
        Get the Moon for a specific date/time.

        Args:
            dt: Datetime you want the moon for (must be timezone aware!)
            ephemeris: Ephemeris to use for calculating moon positions (see [Skyfield's documentation](https://rhodesmill.org/skyfield/planets.html) for details)
        """
        pass