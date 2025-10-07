"""UI helpers for building the tool panel in the fluid simulation demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

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


__all__ = ["Button", "ButtonGroup"]
