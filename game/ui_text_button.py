import pygame
from pygame.locals import *


class UTTextButton:
    def __init__(self, rect, button_text, fonts, font_name):
        self.fonts = fonts
        self.button_text = button_text
        self.rect = rect
        self.started_button_click = False
        self.clicked_button = False
        self.is_hovered = True
        self.font_name = font_name

        self.is_enabled = True

        self.base_button_colour = pygame.Color("#4b4b4b")
        self.base_text_colour = pygame.Color("#FFFFFF")
        self.disabled_button_colour = pygame.Color("#323232")
        self.disabled_text_colour = pygame.Color("#000000")
        self.hovered_button_colour = pygame.Color("#646464")

        self.button_colour = self.base_button_colour
        self.text_colour = self.base_text_colour
        self.button_text_render = self.fonts[self.font_name].render(self.button_text, True, self.text_colour)

    def handle_input_event(self, event):
        if self.is_enabled and self.is_inside(pygame.mouse.get_pos()):
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.started_button_click = True
            if event.type == MOUSEBUTTONUP:
                if event.button == 1 and self.started_button_click:
                    self.clicked_button = True
                    self.started_button_click = False
                    
    def disable(self):
        self.is_enabled = False
        self.button_colour = self.disabled_button_colour
        self.text_colour = self.disabled_text_colour

    def enable(self):
        self.is_enabled = True
        self.button_colour = self.base_button_colour
        self.text_colour = self.base_text_colour

    def was_pressed(self):
        was_pressed = self.clicked_button
        self.clicked_button = False
        return was_pressed

    def set_text(self, text):
        self.button_text = text
        self.button_text_render = self.fonts[self.font_name].render(self.button_text, True, self.text_colour)
    
    def update(self):
        if self.is_enabled and self.is_inside(pygame.mouse.get_pos()):
            self.is_hovered = True
            self.button_colour = self.hovered_button_colour
        elif self.is_enabled:
            self.is_hovered = False
            self.button_colour = self.base_button_colour

    def is_inside(self, screen_pos):
        is_inside = False
        if self.rect[0] <= screen_pos[0] <= self.rect[0]+self.rect[2]:
            if self.rect[1] <= screen_pos[1] <= self.rect[1]+self.rect[3]:
                is_inside = True
        return is_inside

    def draw(self, screen):
        pygame.draw.rect(screen, self.button_colour,
                         pygame.Rect(self.rect[0], self.rect[1], self.rect[2], self.rect[3]), 0)
        screen.blit(self.button_text_render,
                    self.button_text_render.get_rect(centerx=self.rect[0] + self.rect[2] * 0.5,
                                                     centery=self.rect[1] + self.rect[3] * 0.5))
