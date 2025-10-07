"""Core fluid simulation logic using a Stable Fluids style solver.

This module exposes :class:`FluidSim`, a light-weight 2D grid based solver
that supports interactive obstacle editing and a simple laminar inflow
boundary condition on the left side of the domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

import numpy as np


@dataclass
class FluidSettings:
    """Configuration parameters for the fluid simulation grid."""

    width: int
    height: int
    viscosity: float = 5e-4
    time_step: float = 0.1
    inflow_speed: float = 1.5


@dataclass
class FluidSim:
    """2D fluid simulation on a regular grid.

    The implementation is a small adaptation of Jos Stam's *Stable Fluids*
    technique.  It works well for interactive demos and is purposely kept
    compact so it is easy to extend with additional properties later.
    """

    settings: FluidSettings
    u: np.ndarray = field(init=False)
    v: np.ndarray = field(init=False)
    u_prev: np.ndarray = field(init=False)
    v_prev: np.ndarray = field(init=False)
    pressure: np.ndarray = field(init=False)
    divergence: np.ndarray = field(init=False)
    obstacles: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        h, w = self.settings.height, self.settings.width
        shape = (h, w)
        self.u = np.zeros(shape, dtype=np.float32)
        self.v = np.zeros(shape, dtype=np.float32)
        self.u_prev = np.zeros(shape, dtype=np.float32)
        self.v_prev = np.zeros(shape, dtype=np.float32)
        self.pressure = np.zeros(shape, dtype=np.float32)
        self.divergence = np.zeros(shape, dtype=np.float32)
        self.obstacles = np.zeros(shape, dtype=bool)
        self._enforce_inflow()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def size(self) -> Tuple[int, int]:
        return self.settings.width, self.settings.height

    def reset(self) -> None:
        """Clear velocity fields and remove all obstacles."""

        for grid in (self.u, self.v, self.u_prev, self.v_prev, self.pressure, self.divergence):
            grid.fill(0.0)
        self.obstacles.fill(False)
        self._enforce_inflow()

    def apply_brush(self, x: int, y: int, radius: int, draw: bool) -> None:
        """Add or remove solid obstacles within a circular brush footprint."""

        h, w = self.obstacles.shape
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))
        y_grid, x_grid = np.ogrid[:h, :w]
        mask = (x_grid - x) ** 2 + (y_grid - y) ** 2 <= radius ** 2
        if draw:
            self.obstacles[mask] = True
            self.u[mask] = 0.0
            self.v[mask] = 0.0
        else:
            self.obstacles[mask] = False
            # Clear lingering velocity inside a freshly cleared region
            self.u[mask] = 0.0
            self.v[mask] = 0.0
        self.u_prev[mask] = 0.0
        self.v_prev[mask] = 0.0

    def step(self) -> None:
        """Advance the simulation by one time step."""

        dt = self.settings.time_step
        visc = self.settings.viscosity

        self._apply_inflow_source()
        self._add_source(self.u, self.u_prev, dt)
        self._add_source(self.v, self.v_prev, dt)

        self.u_prev, self.u = self.u, self.u_prev
        self._diffuse(1, self.u, self.u_prev, visc, dt)

        self.v_prev, self.v = self.v, self.v_prev
        self._diffuse(2, self.v, self.v_prev, visc, dt)

        self._project(self.u, self.v, self.u_prev, self.v_prev)

        self.u_prev, self.u = self.u, self.u_prev
        self.v_prev, self.v = self.v, self.v_prev

        self._advect(1, self.u, self.u_prev, self.u_prev, self.v_prev, dt)
        self._advect(2, self.v, self.v_prev, self.u_prev, self.v_prev, dt)
        self._project(self.u, self.v, self.u_prev, self.v_prev)

        self._apply_obstacles()
        self._enforce_inflow()
        self.u_prev.fill(0.0)
        self.v_prev.fill(0.0)

    # ------------------------------------------------------------------
    # Core solver routines
    # ------------------------------------------------------------------
    def _diffuse(self, b: int, x: np.ndarray, x0: np.ndarray, diff: float, dt: float) -> None:
        a = dt * diff * (self.settings.width - 2) * (self.settings.height - 2)
        self._lin_solve(b, x, x0, a, 1.0 + 4.0 * a)

    def _advect(
        self,
        b: int,
        d: np.ndarray,
        d0: np.ndarray,
        u: np.ndarray,
        v: np.ndarray,
        dt: float,
    ) -> None:
        h, w = self.settings.height, self.settings.width
        dt_x = dt * (w - 2)
        dt_y = dt * (h - 2)

        for j in range(1, h - 1):
            for i in range(1, w - 1):
                if self.obstacles[j, i]:
                    d[j, i] = 0.0
                    continue

                x = i - dt_x * u[j, i]
                y = j - dt_y * v[j, i]

                x = min(max(0.5, x), w - 1.5)
                y = min(max(0.5, y), h - 1.5)

                i0, i1 = int(x), int(x) + 1
                j0, j1 = int(y), int(y) + 1

                s1, s0 = x - i0, 1.0 - (x - i0)
                t1, t0 = y - j0, 1.0 - (y - j0)

                d[j, i] = (
                    s0 * (t0 * d0[j0, i0] + t1 * d0[j1, i0])
                    + s1 * (t0 * d0[j0, i1] + t1 * d0[j1, i1])
                )

        self._set_bnd(b, d)

    def _project(
        self,
        u: np.ndarray,
        v: np.ndarray,
        p: np.ndarray,
        div: np.ndarray,
    ) -> None:
        h, w = self.settings.height, self.settings.width
        scale_x = 1.0 / (w - 2)
        scale_y = 1.0 / (h - 2)

        for j in range(1, h - 1):
            for i in range(1, w - 1):
                if self.obstacles[j, i]:
                    div[j, i] = 0.0
                    p[j, i] = 0.0
                    continue
                div[j, i] = -0.5 * (
                    scale_x * (u[j, i + 1] - u[j, i - 1])
                    + scale_y * (v[j + 1, i] - v[j - 1, i])
                )
                p[j, i] = 0.0

        self._set_bnd(0, div)
        self._set_bnd(0, p)
        self._lin_solve(0, p, div, 1.0, 4.0)

        for j in range(1, h - 1):
            for i in range(1, w - 1):
                if self.obstacles[j, i]:
                    u[j, i] = 0.0
                    v[j, i] = 0.0
                    continue
                u[j, i] -= 0.5 * (p[j, i + 1] - p[j, i - 1]) * (w - 2)
                v[j, i] -= 0.5 * (p[j + 1, i] - p[j - 1, i]) * (h - 2)

        self._set_bnd(1, u)
        self._set_bnd(2, v)

    def _lin_solve(
        self,
        b: int,
        x: np.ndarray,
        x0: np.ndarray,
        a: float,
        c: float,
        iterations: int = 20,
    ) -> None:
        h, w = self.settings.height, self.settings.width
        recip_c = 1.0 / c
        for _ in range(iterations):
            for j in range(1, h - 1):
                for i in range(1, w - 1):
                    if self.obstacles[j, i]:
                        x[j, i] = 0.0
                        continue
                    x[j, i] = (
                        x0[j, i]
                        + a
                        * (x[j, i - 1] + x[j, i + 1] + x[j - 1, i] + x[j + 1, i])
                    ) * recip_c
            self._set_bnd(b, x)

    def _set_bnd(self, b: int, x: np.ndarray) -> None:
        h, w = self.settings.height, self.settings.width
        for i in range(1, w - 1):
            x[0, i] = -x[1, i] if b == 2 else x[1, i]
            x[h - 1, i] = -x[h - 2, i] if b == 2 else x[h - 2, i]
        for j in range(1, h - 1):
            if b == 1:
                x[j, 0] = self.settings.inflow_speed if not self.obstacles[j, 0] else 0.0
            else:
                x[j, 0] = x[j, 1]
            x[j, w - 1] = -x[j, w - 2] if b == 1 else x[j, w - 2]

        x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
        x[0, w - 1] = 0.5 * (x[1, w - 1] + x[0, w - 2])
        x[h - 1, 0] = 0.5 * (x[h - 2, 0] + x[h - 1, 1])
        x[h - 1, w - 1] = 0.5 * (x[h - 2, w - 1] + x[h - 1, w - 2])

        # Solid cells completely zero out the field
        x[self.obstacles] = 0.0

    def _apply_obstacles(self) -> None:
        self.u[self.obstacles] = 0.0
        self.v[self.obstacles] = 0.0

    def _enforce_inflow(self) -> None:
        """Apply a steady inflow velocity along the left boundary."""

        inflow_speed = self.settings.inflow_speed
        column = self.u[:, 0]
        mask = ~self.obstacles[:, 0]
        column[mask] = inflow_speed
        self.v[:, 0][mask] = 0.0

    def _apply_inflow_source(self) -> None:
        """Inject a horizontal velocity source along the inflow boundary."""

        mask = ~self.obstacles[:, 0]
        inflow = self.settings.inflow_speed
        self.u_prev[:, 0][mask] = inflow
        self.v_prev[:, 0][mask] = 0.0

    @staticmethod
    def _add_source(x: np.ndarray, s: np.ndarray, dt: float) -> None:
        x += dt * s


__all__ = ["FluidSettings", "FluidSim"]
