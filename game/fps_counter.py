import pygame
from collections import deque


class FPSCounter:
    def __init__(self, fonts):
        self.fps = 0
        self.average_fps = 0
        self.fonts = fonts
        self.frame_rates = deque([])

    def update(self, time_delta):
        if time_delta > 0.0:
            self.fps = 1.0 / time_delta
            if len(self.frame_rates) < 300:
                self.frame_rates.append(self.fps)
            else:
                self.frame_rates.popleft()
                self.frame_rates.append(self.fps)

        self.average_fps = sum(self.frame_rates) / len(self.frame_rates)

    def draw(self, surface, camera):

        fps_text_centre = [camera.dimensions[0] - 78, 24]
        background_text = self.fonts["default_32"].render("FPS: " + "{:.2f}".format(self.fps),
                                                          True, pygame.Color("#777777"))

        surface.blit(background_text, background_text.get_rect(centerx=fps_text_centre[0],
                                                               centery=fps_text_centre[1] + 1))
        surface.blit(background_text, background_text.get_rect(centerx=fps_text_centre[0],
                                                               centery=fps_text_centre[1] - 1))

        surface.blit(background_text, background_text.get_rect(centerx=fps_text_centre[0] + 1,
                                                               centery=fps_text_centre[1]))
        surface.blit(background_text, background_text.get_rect(centerx=fps_text_centre[0] - 1,
                                                               centery=fps_text_centre[1]))

        fps_text_render = self.fonts["default_32"].render("FPS: " + "{:.2f}".format(self.fps),
                                                          True, pygame.Color("#FFFFFF"))
        surface.blit(fps_text_render, fps_text_render.get_rect(centerx=fps_text_centre[0], centery=fps_text_centre[1]))

        average_fps_text_centre = [camera.dimensions[0] - 78, 50]
        average_background_text = self.fonts["default_14"].render("Average FPS: " + "{:.2f}".format(self.average_fps),
                                                                  True, pygame.Color("#777777"))

        surface.blit(average_background_text, average_background_text.get_rect(centerx=average_fps_text_centre[0],
                                                                               centery=average_fps_text_centre[1] + 1))
        surface.blit(average_background_text, average_background_text.get_rect(centerx=average_fps_text_centre[0],
                                                                               centery=average_fps_text_centre[1] - 1))

        surface.blit(average_background_text, average_background_text.get_rect(centerx=average_fps_text_centre[0] + 1,
                                                                               centery=average_fps_text_centre[1]))
        surface.blit(average_background_text, average_background_text.get_rect(centerx=average_fps_text_centre[0] - 1,
                                                                               centery=average_fps_text_centre[1]))

        average_fps_text_render = self.fonts["default_14"].render("Average FPS: " + "{:.2f}".format(self.average_fps),
                                                                  True, pygame.Color("#FFFFFF"))
        surface.blit(average_fps_text_render, average_fps_text_render.get_rect(centerx=average_fps_text_centre[0],
                                                                               centery=average_fps_text_centre[1]))
