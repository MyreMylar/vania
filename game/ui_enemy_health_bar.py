import pygame


class UIEnemyHealthBar(pygame.sprite.Sprite):
    """
    A UI that will display the enemy's health capacity and their current health.
    """
    def __init__(self, enemy, *groups):
        super().__init__(*groups)
        self.enemy = enemy
        self.position = enemy.screen_position[:]
        self.width = int(enemy.rect.width*0.75)
        self.height = 10
        self.rect = pygame.Rect(self.position, (self.width, self.height))
        self.background_colour = pygame.Color("#000000")
        self.background_surface = pygame.Surface((self.rect.w, self.rect.h)).convert()
        self.background_surface.fill(self.background_colour)

        self.image = pygame.Surface((self.rect.w, self.rect.h)).convert()

        self.hover_height = 10
        self.horiz_padding = 2
        self.vert_padding = 2

        self.capacity_width = self.width - (self.horiz_padding * 2)
        self.capacity_height = self.height - (self.vert_padding * 2)
        self.health_capacity_rect = pygame.Rect([self.horiz_padding,
                                                 self.vert_padding],
                                                [self.capacity_width, self.capacity_height])

        self.health_empty_colour = pygame.Color("#CCCCCC")
        self.health_colour = pygame.Color("#f4251b")

        self.current_health = 50
        self.health_capacity = 100
        self.health_percentage = self.current_health / self.health_capacity

        self.current_health_rect = pygame.Rect([self.horiz_padding,
                                                self.vert_padding],
                                               [int(self.capacity_width*self.health_percentage),
                                                self.capacity_height])

    def update(self):
        self.position = [self.enemy.screen_position[0] - self.enemy.rect.width/2,
                         self.enemy.screen_position[1] - (self.enemy.rect.height/2) - self.hover_height]

        self.current_health = self.enemy.current_health
        self.health_capacity = self.enemy.base_health
        self.health_percentage = self.current_health / self.health_capacity
        self.current_health_rect.width = int(self.capacity_width * self.health_percentage)

        self.image.blit(self.background_surface, (0, 0))
        pygame.draw.rect(self.image, self.health_empty_colour, self.health_capacity_rect)
        pygame.draw.rect(self.image, self.health_colour, self.current_health_rect)

        self.rect.x = self.position[0]
        self.rect.y = self.position[1]
