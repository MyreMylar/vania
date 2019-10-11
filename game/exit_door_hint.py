import pygame


class ExitDoorHint(pygame.sprite.Sprite):
    def __init__(self, fonts, player, *groups):
        super().__init__(*groups)
        self.player = player
        text_render = fonts["default_16_bold"].render("Push UP to Exit", True, pygame.Color("#FFFFFF"))
        bg_text_render = fonts["default_16_bold"].render("Push UP to Exit", True, pygame.Color("#777777"))

        self.image = pygame.transform.scale(text_render, [text_render.get_width()+2,
                                                          text_render.get_height()+2])
        self.rect = self.image.get_rect()
        # self.image.set_alpha(128)

        self.image.blit(bg_text_render, text_render.get_rect(centerx=self.rect.centerx, centery=self.rect.centery + 1))
        self.image.blit(bg_text_render, text_render.get_rect(centerx=self.rect.centerx, centery=self.rect.centery - 1))
        self.image.blit(bg_text_render, text_render.get_rect(centerx=self.rect.centerx + 1, centery=self.rect.centery))
        self.image.blit(bg_text_render, text_render.get_rect(centerx=self.rect.centerx - 1, centery=self.rect.centery))

        self.image.blit(text_render, text_render.get_rect(centerx=self.rect.centerx, centery=self.rect.centery))

    def update(self):
        self.rect.centerx = self.player.screen_position[0]
        self.rect.centery = self.player.screen_position[1] - 52
