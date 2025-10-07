"""Interactive 2D fluid simulation demo with a tool panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pygame

from fluid_sim.fluid import FluidSettings, FluidSim
from fluid_sim.ui import Button, ButtonGroup

Color = Tuple[int, int, int]


@dataclass
class ResolutionOption:
    label: str
    grid_size: Tuple[int, int]


class FluidApp:
    SCREEN_SIZE = (1100, 720)
    PANEL_WIDTH = 240
    BACKGROUND_COLOR: Color = (18, 18, 25)

    COLORS: Dict[str, Color] = {
        "panel_bg": (32, 34, 45),
        "button": (57, 62, 78),
        "button_active": (88, 141, 255),
        "border": (20, 22, 30),
        "text": (230, 233, 240),
        "section_text": (176, 182, 196),
        "viewport_bg": (10, 12, 20),
        "obstacle": (40, 40, 45),
    }

    RESOLUTIONS = (
        ResolutionOption("Low", (64, 48)),
        ResolutionOption("Medium", (96, 72)),
        ResolutionOption("High", (128, 96)),
    )

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("2D Fluid Simulation")
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Source Sans Pro", 20)
        self.small_font = pygame.font.SysFont("Source Sans Pro", 16)
        self.section_titles: list[tuple[str, int]] = []

        self.viewport_rect = pygame.Rect(
            self.PANEL_WIDTH, 0, self.SCREEN_SIZE[0] - self.PANEL_WIDTH, self.SCREEN_SIZE[1]
        )

        self.brush_radius_pixels = 16
        self.brush_mode = "draw"
        self.show_velocity = True
        self.paused = False

        self.current_resolution = self.RESOLUTIONS[1]
        self.sim = self._create_sim(self.current_resolution)

        self.buttons: list[Button] = []
        self.button_groups: list[ButtonGroup] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _create_sim(self, option: ResolutionOption) -> FluidSim:
        w, h = option.grid_size
        settings = FluidSettings(width=w, height=h)
        return FluidSim(settings)

    def _build_ui(self) -> None:
        margin_x = 20
        y = 32
        button_width = self.PANEL_WIDTH - margin_x * 2
        button_height = 40
        gap = 12
        section_gap = 24

        def add_section(title: str) -> None:
            nonlocal y
            self.section_titles.append((title, y))
            y += self.font.get_height() + 10

        # Brush tools
        add_section("Brush Tools")
        draw_button = Button(
            "Draw Obstacles",
            pygame.Rect(margin_x, y, button_width, button_height),
            callback=lambda: self._set_brush_mode("draw"),
        )
        erase_button = Button(
            "Erase Obstacles",
            pygame.Rect(margin_x, y + button_height + gap, button_width, button_height),
            callback=lambda: self._set_brush_mode("erase"),
        )
        self.brush_group = ButtonGroup("brush", [draw_button, erase_button])
        self.brush_group.set_active(draw_button)
        self.button_groups.append(self.brush_group)
        y = erase_button.rect.bottom + gap
        self.brush_radius_pos = y
        y += self.small_font.get_height() + section_gap

        # Resolution options
        add_section("Resolution")
        res_buttons = []
        for idx, option in enumerate(self.RESOLUTIONS):
            button = Button(
                option.label,
                pygame.Rect(
                    margin_x,
                    y + idx * (button_height + gap),
                    button_width,
                    button_height,
                ),
                callback=lambda opt=option: self._change_resolution(opt),
            )
            res_buttons.append(button)
        self.res_group = ButtonGroup("resolution", res_buttons)
        self.res_group.set_active(res_buttons[1])
        self.button_groups.append(self.res_group)
        y = res_buttons[-1].rect.bottom + section_gap

        # Toggle velocity field
        add_section("Display")
        velocity_button = Button(
            "Show Velocity Field",
            pygame.Rect(margin_x, y, button_width, button_height),
            callback=lambda: self._toggle_velocity(),
            toggle=True,
            active=True,
        )
        self.velocity_button = velocity_button
        self.buttons.append(velocity_button)

        pause_button = Button(
            "Pause Simulation",
            pygame.Rect(margin_x, velocity_button.rect.bottom + gap, button_width, button_height),
            callback=self._toggle_pause,
            toggle=True,
            active=False,
        )
        self.pause_button = pause_button
        self.buttons.append(pause_button)
        y = pause_button.rect.bottom + gap

        # Reset button
        reset_button = Button(
            "Reset Simulation",
            pygame.Rect(margin_x, y, button_width, button_height),
            callback=self._reset_simulation,
        )
        self.buttons.append(reset_button)
        y = reset_button.rect.bottom + section_gap

        self.instructions_top = y

    # ------------------------------------------------------------------
    # UI callbacks
    # ------------------------------------------------------------------
    def _set_brush_mode(self, mode: str) -> None:
        self.brush_mode = mode

    def _change_resolution(self, option: ResolutionOption) -> None:
        self.current_resolution = option
        self.sim = self._create_sim(option)

    def _toggle_velocity(self) -> None:
        self.show_velocity = not self.show_velocity
        self.velocity_button.active = self.show_velocity

    def _toggle_pause(self) -> None:
        self.paused = not self.paused
        if hasattr(self, "pause_button"):
            self.pause_button.active = self.paused

    def _reset_simulation(self) -> None:
        self.sim.reset()

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _draw_panel(self) -> None:
        panel_rect = pygame.Rect(0, 0, self.PANEL_WIDTH, self.SCREEN_SIZE[1])
        pygame.draw.rect(self.screen, self.COLORS["panel_bg"], panel_rect)

        for title, top in self.section_titles:
            text = self.font.render(title, True, self.COLORS["section_text"])
            self.screen.blit(text, (20, top))

        self.brush_group.draw(self.screen, self.small_font, self.COLORS)

        radius_text = self.small_font.render(
            f"Radius: {self.brush_radius_pixels}px", True, self.COLORS["section_text"]
        )
        self.screen.blit(radius_text, (20, self.brush_radius_pos))

        self.res_group.draw(self.screen, self.small_font, self.COLORS)

        for button in self.buttons:
            button.draw(self.screen, self.small_font, self.COLORS)

        instructions = [
            "Left drag: paint",
            "Right drag: erase",
            "Scroll: adjust brush",
            "Press R: reset",
            "Space: pause/resume",
            "V: toggle velocity",
        ]
        base_y = min(self.SCREEN_SIZE[1] - 140, self.instructions_top)
        for i, line in enumerate(instructions):
            text = self.small_font.render(line, True, self.COLORS["section_text"])
            self.screen.blit(text, (20, base_y + i * 20))

    def _velocity_to_color(self, speed: float, max_speed: float) -> Color:
        if max_speed <= 1e-5:
            t = 0.0
        else:
            t = min(max(speed / max_speed, 0.0), 1.0)
        start = (30, 35, 95)
        end = (255, 220, 90)
        return (
            int(start[0] + (end[0] - start[0]) * t),
            int(start[1] + (end[1] - start[1]) * t),
            int(start[2] + (end[2] - start[2]) * t),
        )

    def _draw_velocity_field(self, surface: pygame.Surface) -> None:
        sim = self.sim
        h, w = sim.settings.height, sim.settings.width
        cell_width = self.viewport_rect.width / w
        cell_height = self.viewport_rect.height / h

        surface.fill(self.COLORS["viewport_bg"], self.viewport_rect)

        if self.show_velocity:
            speeds = np.sqrt(sim.u ** 2 + sim.v ** 2)
            sample = speeds[~sim.obstacles]
            if sample.size:
                max_speed = float(np.percentile(sample, 95))
            else:
                max_speed = 0.0
            if max_speed <= 1e-5:
                max_speed = max(sim.settings.inflow_speed, 1.0)
            for j in range(h):
                for i in range(w):
                    x0 = int(self.viewport_rect.left + i * cell_width)
                    x1 = int(self.viewport_rect.left + (i + 1) * cell_width)
                    y0 = int(self.viewport_rect.top + j * cell_height)
                    y1 = int(self.viewport_rect.top + (j + 1) * cell_height)
                    rect = pygame.Rect(x0, y0, max(1, x1 - x0), max(1, y1 - y0))
                    if sim.obstacles[j, i]:
                        pygame.draw.rect(surface, self.COLORS["obstacle"], rect)
                        continue
                    color = self._velocity_to_color(float(speeds[j, i]), max_speed)
                    pygame.draw.rect(surface, color, rect)
        else:
            for j in range(h):
                for i in range(w):
                    if sim.obstacles[j, i]:
                        x0 = int(self.viewport_rect.left + i * cell_width)
                        x1 = int(self.viewport_rect.left + (i + 1) * cell_width)
                        y0 = int(self.viewport_rect.top + j * cell_height)
                        y1 = int(self.viewport_rect.top + (j + 1) * cell_height)
                        rect = pygame.Rect(x0, y0, max(1, x1 - x0), max(1, y1 - y0))
                        pygame.draw.rect(surface, self.COLORS["obstacle"], rect)

    def _draw_grid_overlay(self) -> None:
        pygame.draw.rect(self.screen, (0, 0, 0), self.viewport_rect, width=2)

    def _draw_paused_indicator(self) -> None:
        if not self.paused:
            return
        text = self.font.render("Paused", True, self.COLORS["text"])
        text_rect = text.get_rect()
        text_rect.topright = (self.viewport_rect.right - 20, self.viewport_rect.top + 20)
        overlay = pygame.Surface((text_rect.width + 20, text_rect.height + 12), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        overlay_rect = overlay.get_rect()
        overlay_rect.topright = (self.viewport_rect.right - 30, self.viewport_rect.top + 12)
        self.screen.blit(overlay, overlay_rect)
        self.screen.blit(text, text_rect)

    # ------------------------------------------------------------------
    # Interaction helpers
    # ------------------------------------------------------------------
    def _handle_panel_event(self, event: pygame.event.Event) -> bool:
        # Button groups first (radio buttons)
        for group in self.button_groups:
            if group.handle_event(event):
                return True

        # Standalone buttons (toggles etc.)
        for button in self.buttons:
            if button.handle_event(event):
                return True
        return False

    def _apply_brush_from_mouse(self, draw: bool) -> None:
        mx, my = pygame.mouse.get_pos()
        if not self.viewport_rect.collidepoint(mx, my):
            return
        sim = self.sim
        w, h = sim.settings.width, sim.settings.height
        cell_w = self.viewport_rect.width / w
        cell_h = self.viewport_rect.height / h
        grid_x = int((mx - self.viewport_rect.left) / cell_w)
        grid_y = int(my / cell_h)
        radius = max(1, int(self.brush_radius_pixels / min(cell_w, cell_h)))
        sim.apply_brush(grid_x, grid_y, radius, draw)

    def _handle_mouse(self) -> None:
        buttons = pygame.mouse.get_pressed()
        if buttons[0]:  # Left button draws
            self._apply_brush_from_mouse(self.brush_mode == "draw")
        elif buttons[2]:  # Right button always erases
            self._apply_brush_from_mouse(False)

    def _handle_scroll(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEWHEEL:
            self.brush_radius_pixels = max(4, min(64, self.brush_radius_pixels + event.y * 2))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.viewport_rect.collidepoint(event.pos):
                        if self._handle_panel_event(event):
                            continue
                elif event.type == pygame.MOUSEWHEEL:
                    self._handle_scroll(event)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._reset_simulation()
                    elif event.key == pygame.K_SPACE:
                        self._toggle_pause()
                    elif event.key == pygame.K_v:
                        self._toggle_velocity()

            self._handle_mouse()

            if not self.paused:
                self.sim.step()

            self.screen.fill(self.BACKGROUND_COLOR)
            self._draw_panel()
            self._draw_velocity_field(self.screen)
            self._draw_grid_overlay()
            self._draw_paused_indicator()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


def main() -> None:
    app = FluidApp()
    app.run()


if __name__ == "__main__":
    main()
