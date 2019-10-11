import pygame


class UIPlayerHealthBar:
    """
    A UI that will display the player's health capacity and their current health.
    """
    def __init__(self, position, fonts):
        self.fonts = fonts
        self.position = position[:]
        self.width = 300
        self.height = 20
        self.background_rect = pygame.Rect(position, (self.width, self.height))
        self.background_colour = pygame.Color("#000000")
        self.background_surface = pygame.Surface((self.background_rect.w, self.background_rect.h))
        self.background_surface.fill(self.background_colour)
        self.background_surface.set_alpha(175)
        self.horiz_padding = 3
        self.vert_padding = 3
        self.capacity_width = self.width - (self.horiz_padding * 2)
        self.capacity_height = self.height - (self.vert_padding * 2)
        self.health_capacity_rect = pygame.Rect([position[0]+self.horiz_padding, position[1]+self.vert_padding],
                                                [self.capacity_width, self.capacity_height])

        self.health_outline_colour = pygame.Color("#309955FF")
        self.health_colour = pygame.Color("#70CC88FF")

        self.current_health = 50
        self.health_capacity = 100
        self.health_percentage = self.current_health / self.health_capacity

        self.current_health_rect = pygame.Rect([position[0] + self.horiz_padding + 1,
                                                position[1] + self.vert_padding + 1],
                                               [int(self.capacity_width*self.health_percentage)-2,
                                                self.capacity_height-2])

        self.background_text = self.fonts["roboto_14_bold"].render(
            str(self.current_health) + "/" + str(self.health_capacity),
            True, pygame.Color("#777777"))

        self.foreground_text = self.fonts["roboto_14_bold"].render(
            str(self.current_health) + "/" + str(self.health_capacity),
            True, pygame.Color("#FFFFFF"))

    def update(self, player):
        if player.base_health != self.health_capacity or self.current_health != player.current_health:
            self.current_health = player.current_health
            self.health_capacity = player.base_health
            self.health_percentage = self.current_health / self.health_capacity

            self.current_health_rect = pygame.Rect([self.position[0] + self.horiz_padding + 1,
                                                    self.position[1] + self.vert_padding + 1],
                                                   [int(self.capacity_width * self.health_percentage) - 2,
                                                    self.capacity_height - 2])

            self.background_text = self.fonts["roboto_14_bold"].render(
                str(self.current_health) + "/" + str(self.health_capacity),
                True, pygame.Color("#777777"))

            self.foreground_text = self.fonts["roboto_14_bold"].render(
                str(self.current_health) + "/" + str(self.health_capacity),
                True, pygame.Color("#FFFFFF"))

    def draw(self, surface):
        surface.blit(self.background_surface, self.position)
        pygame.draw.rect(surface, self.health_outline_colour, self.health_capacity_rect, 1)
        pygame.draw.rect(surface, self.health_colour, self.current_health_rect)

        surface.blit(self.background_text, self.background_text.get_rect(centerx=self.health_capacity_rect.centerx,
                                                                         centery=self.health_capacity_rect.centery+1))
        surface.blit(self.background_text, self.background_text.get_rect(centerx=self.health_capacity_rect.centerx,
                                                                         centery=self.health_capacity_rect.centery - 1))

        surface.blit(self.background_text, self.background_text.get_rect(centerx=self.health_capacity_rect.centerx + 1,
                                                                         centery=self.health_capacity_rect.centery))
        surface.blit(self.background_text, self.background_text.get_rect(centerx=self.health_capacity_rect.centerx - 1,
                                                                         centery=self.health_capacity_rect.centery))

        surface.blit(self.foreground_text, self.foreground_text.get_rect(centerx=self.health_capacity_rect.centerx,
                                                                         centery=self.health_capacity_rect.centery))
