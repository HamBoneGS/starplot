from typing import Callable, Mapping

import geopandas as gpd
import numpy as np

from starplot.data import DataFiles
from starplot.data.dsos import (
    DsoType,
    DEFAULT_DSO_TYPES,
    ONGC_TYPE,
    ONGC_TYPE_MAP,
    DSO_LEGEND_LABELS,
    DSO_LABELS_DEFAULT,
    DsoLabelMaker,
)
from starplot.models import DSO
from starplot.styles import MarkerSymbolEnum


class DsoPlotterMixin:
    def _plot_dso_polygon(self, polygon, style):
        coords = list(zip(*polygon.exterior.coords.xy))
        # close the polygon - for some reason matplotlib needs the coord twice
        coords.append(coords[0])
        coords.append(coords[0])
        self._polygon(coords, style.marker.to_polygon_style(), closed=False)

    def open_clusters(self, *args, **kwargs):
        """
        Plots open clusters

        This is just a small wrapper around the `dsos()` function, so any `kwargs` will be passed through.
        """
        self.dsos(types=[DsoType.OPEN_CLUSTER], **kwargs)

    def globular_clusters(self, *args, **kwargs):
        """
        Plots globular clusters

        This is just a small wrapper around the `dsos()` function, so any `kwargs` will be passed through.
        """
        self.dsos(types=[DsoType.GLOBULAR_CLUSTER], **kwargs)

    def galaxies(self, *args, **kwargs):
        """
        Plots galaxy DSO types:

        - Galaxy
        - Galaxy Pair
        - Galaxy Triplet

        This is just a small wrapper around the `dsos()` function, so any `kwargs` will be passed through.
        """
        self.dsos(
            types=[
                DsoType.GALAXY,
                DsoType.GALAXY_PAIR,
                DsoType.GALAXY_TRIPLET,
            ],
            **kwargs,
        )

    def nebula(self, *args, **kwargs):
        """
        Plots nebula DSO types:

        - Nebula
        - Planetary Nebula
        - Emission Nebula
        - Star Cluster Nebula
        - Reflection Nebula

        This is just a small wrapper around the `dsos()` function, so any `kwargs` will be passed through.
        """
        self.dsos(
            types=[
                DsoType.NEBULA,
                DsoType.PLANETARY_NEBULA,
                DsoType.EMISSION_NEBULA,
                DsoType.STAR_CLUSTER_NEBULA,
                DsoType.REFLECTION_NEBULA,
            ],
            **kwargs,
        )

    def dsos(
        self,
        mag: float = 8.0,
        types: list[DsoType] = DEFAULT_DSO_TYPES,
        true_size: bool = True,
        labels: Mapping[str, str] = DSO_LABELS_DEFAULT,
        legend_labels: Mapping[DsoType, str] = DSO_LEGEND_LABELS,
        alpha_fn: Callable[[DSO], float] = None,
        where: list = None,
        where_labels: list = None,
    ):
        """
        Plots Deep Sky Objects (DSOs), from OpenNGC

        Args:
            mag: Limiting magnitude of DSOs to plot. For more control of what DSOs to plot, use the `where` kwarg. **Note:** if you pass `mag` and `where` then `mag` will be ignored
            types: List of DSO types to plot
            true_size: If True, then each DSO will be plotted as its true apparent size in the sky (note: this increases plotting time). If False, then the style's marker size will be used. Also, keep in mind not all DSOs have a defined size (according to OpenNGC) -- so these will use the style's marker size.
            labels: A dictionary that maps DSO names (as specified in OpenNGC) to the label that'll be plotted for that object. By default, the DSO's name in OpenNGC will be used as the label. If you want to hide all labels, then set this arg to `None`.
            legend_labels: A dictionary that maps a `DsoType` to the legend label that'll be plotted for that type of DSO. If you want to hide all DSO legend labels, then set this arg to `None`.
            alpha_fn: Callable for calculating the alpha value (aka "opacity") of each DSO. If `None`, then the marker style's alpha will be used.
            where: A list of expressions that determine which DSOs to plot. See [Selecting Objects](/reference-selecting-objects/) for details.
            where_labels: A list of expressions that determine which DSOs are labeled on the plot. See [Selecting Objects](/reference-selecting-objects/) for details.
        """

        # TODO: add kwarg styles

        # TODO: sort by type, and plot markers together (for better performance)

        self.logger.debug("Plotting DSOs...")
        nearby_dsos = gpd.read_file(
            DataFiles.ONGC.value,
            engine="pyogrio",
            use_arrow=True,
            bbox=self._extent_mask(),
        )

        where = where or []
        where_labels = where_labels or []

        if not where:
            where = [DSO.magnitude.is_null() | (DSO.magnitude <= mag)]

        if labels is None:
            labels = {}
        elif type(labels) != DsoLabelMaker:
            labels = DsoLabelMaker(overrides=labels)

        if legend_labels is None:
            legend_labels = {}
        else:
            legend_labels = {**DSO_LEGEND_LABELS, **legend_labels}

        nearby_dsos = nearby_dsos.replace({np.nan: None})
        dso_types = [ONGC_TYPE[dtype] for dtype in types]
        nearby_dsos = nearby_dsos[
            nearby_dsos["Type"].isin(dso_types)
            & nearby_dsos["ra_degrees"].notnull()
            & nearby_dsos["dec_degrees"].notnull()
        ]

        for _, d in nearby_dsos.iterrows():
            ra = d.ra_degrees
            dec = d.dec_degrees
            name = d.Name
            label = labels.get(name)
            dso_type = ONGC_TYPE_MAP[d.Type]
            style = self.style.get_dso_style(dso_type)
            maj_ax, min_ax, angle = d.MajAx, d.MinAx, d.PosAng
            legend_label = legend_labels.get(dso_type)
            magnitude = d["V-Mag"] or d["B-Mag"] or None
            magnitude = float(magnitude) if magnitude else None
            _dso = DSO(
                name=name,
                ra=ra / 15,
                dec=dec,
                type=dso_type,
                maj_ax=maj_ax,
                min_ax=min_ax,
                angle=angle,
                magnitude=magnitude,
                size=d.size_deg2,
            )

            if any(
                [
                    style is None,
                    not all([e.evaluate(_dso) for e in where]),
                    not self.in_bounds(ra / 15, dec),
                ]
            ):
                continue

            _alpha_fn = alpha_fn or (lambda d: style.marker.alpha)
            style.marker.alpha = _alpha_fn(_dso)

            if where_labels and not all([e.evaluate(_dso) for e in where_labels]):
                label = None

            if true_size and d.size_deg2 is not None:
                if "Polygon" == str(d.geometry.geom_type):
                    self._plot_dso_polygon(d.geometry, style)

                elif "MultiPolygon" == str(d.geometry.geom_type):
                    for polygon in d.geometry.geoms:
                        self._plot_dso_polygon(polygon, style)
                elif maj_ax:
                    # if object has a major axis then plot its actual extent
                    maj_ax_degrees = (maj_ax / 60) / 2

                    if min_ax:
                        min_ax_degrees = (min_ax / 60) / 2
                    else:
                        min_ax_degrees = maj_ax_degrees

                    poly_style = style.marker.to_polygon_style()

                    if style.marker.symbol == MarkerSymbolEnum.SQUARE:
                        self.rectangle(
                            (ra / 15, dec),
                            min_ax_degrees * 2,
                            maj_ax_degrees * 2,
                            poly_style,
                            angle or 0,
                        )
                    else:
                        self.ellipse(
                            (ra / 15, dec),
                            min_ax_degrees * 2,
                            maj_ax_degrees * 2,
                            poly_style,
                            angle or 0,
                        )

                if label:
                    self._text(
                        ra / 15,
                        dec,
                        label,
                        **style.label.matplot_kwargs(self._size_multiplier),
                    )

            else:
                # if no major axis, then just plot as a marker
                self.marker(
                    ra=ra / 15,
                    dec=dec,
                    label=label,
                    style=style,
                )

            self._objects.dsos.append(_dso)

            self._add_legend_handle_marker(legend_label, style.marker)
