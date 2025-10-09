"""UI helpers for building the tool panel in the fluid simulation demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

import pygame

Color = tuple[int, int, int]


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    callback: Callable[[], None]
    toggle: bool = False
    active: bool = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.active = not self.active
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, colors: dict[str, Color]) -> None:
        bg = colors["button_active" if self.active else "button"]
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, colors["border"], self.rect, width=2, border_radius=6)

        text = font.render(self.label, True, colors["text"])
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)


@dataclass
class ButtonGroup:
    name: str
    buttons: List[Button] = field(default_factory=list)

    def set_active(self, active_button: Button) -> None:
        for button in self.buttons:
            button.active = button is active_button

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    if button.callback:
                        button.callback()
                    self.set_active(button)
                    return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, colors: dict[str, Color]) -> None:
        for button in self.buttons:
            button.draw(surface, font, colors)


@dataclass
class Slider:
    """Simple horizontal slider widget for the control panel."""

    label: str
    rect: pygame.Rect
    min_value: float
    max_value: float
    value: float
    callback: Optional[Callable[[float], None]] = None
    precision: int = 3
    active: bool = False

    @property
    def normalized(self) -> float:
        if self.max_value == self.min_value:
            return 0.0
        return (self.value - self.min_value) / (self.max_value - self.min_value)

    def _clamp_value(self, value: float) -> float:
        return max(self.min_value, min(self.max_value, value))

    def _set_value_from_pos(self, x: int) -> None:
        width = self.rect.width
        if width <= 0:
            return
        t = (x - self.rect.left) / width
        t = max(0.0, min(1.0, t))
        new_value = self.min_value + t * (self.max_value - self.min_value)
        new_value = self._clamp_value(new_value)
        if abs(new_value - self.value) > 1e-6:
            self.value = new_value
            if self.callback:
                self.callback(self.value)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self._set_value_from_pos(event.pos[0])
                return True
        elif event.type == pygame.MOUSEMOTION and self.active:
            self._set_value_from_pos(event.pos[0])
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.active:
            self.active = False
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, colors: dict[str, Color]) -> None:
        label = f"{self.label}: {self.value:.{self.precision}f}"
        text = font.render(label, True, colors["section_text"])
        text_rect = text.get_rect(midleft=(self.rect.left, self.rect.top - 12))
        surface.blit(text, text_rect)

        track_rect = pygame.Rect(self.rect)
        track_rect.height = 6
        track_rect.centery = self.rect.centery
        pygame.draw.rect(surface, colors["border"], track_rect, border_radius=3)

        fill_rect = pygame.Rect(track_rect)
        fill_rect.width = int(track_rect.width * self.normalized)
        pygame.draw.rect(surface, colors["button_active"], fill_rect, border_radius=3)

        knob_x = int(track_rect.left + track_rect.width * self.normalized)
        knob_rect = pygame.Rect(0, 0, 12, 12)
        knob_rect.center = (knob_x, track_rect.centery)
        pygame.draw.rect(surface, colors["button"], knob_rect, border_radius=6)
        pygame.draw.rect(surface, colors["border"], knob_rect, width=2, border_radius=6)


__all__ = ["Button", "ButtonGroup", "Slider"]
