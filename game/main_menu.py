import pygame

from game.ui_text_button import UTTextButton


class MainMenu:

    def __init__(self, fonts, camera):
        self.fonts = fonts
        self.background_image = pygame.Surface(camera.dimensions)  # pygame.image.load("images/menu_background.png").convert()
        self.background_image.fill(pygame.Color("#F0F0F0"))

        main_menu_title_string = "Vania"
        self.main_menu_title_text_render = self.fonts["julee_128"].render(main_menu_title_string,
                                                                          True, pygame.Color("#000000"))
        self.title_text_position = self.main_menu_title_text_render.get_rect(centerx=camera.dimensions[0] * 0.5,
                                                                             centery=camera.dimensions[1] * 0.2)

        button_menu_vertical_start = camera.screen_rect.centery + (0.2 * camera.dimensions[1])
        button_menu_spacing = 64

        play_game_button_rect = pygame.Rect((0, 0), (150, 35))
        play_game_button_rect.centerx = camera.screen_rect.centerx
        play_game_button_rect.centery = button_menu_vertical_start
        self.play_game_button = UTTextButton(play_game_button_rect, "Play Game", fonts, "default_16")

        edit_map_button_rect = pygame.Rect((0, 0), (150, 35))
        edit_map_button_rect.centerx = camera.screen_rect.centerx
        edit_map_button_rect.centery = button_menu_vertical_start + button_menu_spacing
        self.edit_map_button = UTTextButton(edit_map_button_rect, "Edit Map", fonts, "default_16")

    def run(self, screen):
        is_main_menu_and_index = [0, 0]
        for event in pygame.event.get():
            self.play_game_button.handle_input_event(event)
            self.edit_map_button.handle_input_event(event)
            if event.type == pygame.QUIT:
                is_main_menu_and_index[0] = 3
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    is_main_menu_and_index[0] = 3

        self.play_game_button.update()
        self.edit_map_button.update()
        
        if self.play_game_button.was_pressed():
            is_main_menu_and_index[0] = 1
        if self.edit_map_button.was_pressed():
            is_main_menu_and_index[0] = 2
                    
        screen.blit(self.background_image, (0, 0))  # draw the background
        screen.blit(self.main_menu_title_text_render, self.title_text_position)
        self.play_game_button.draw(screen)
        self.edit_map_button.draw(screen)

        return is_main_menu_and_index
