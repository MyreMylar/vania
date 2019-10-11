import pygame


class Camera:
    """
    Intended as a way to coordinate moving the viewable area of a 'larger-than-one-screen' game world around that world

    May be extended to add camera like effects in the future

    IDEAS:
        - Camera shake (to add impact on big hits)
        - Post processing (probably not that workable in pygame, but maybe some fullscreen blend-mode effects?
        - Zoom (could be used to add impact or just examine smaller details)
    """
    def __init__(self, start_world_position, screen_dimensions, world_dimensions):
        self.position = [start_world_position[0], start_world_position[1]]
        self.screen_rect = pygame.Rect((0, 0), screen_dimensions)
        self.screen_rect.centerx = self.position[0]
        self.screen_rect.centery = self.position[1]
        self.target_position = [start_world_position[0], start_world_position[1]]

        self.world_dimensions = world_dimensions
        self.dimensions = (screen_dimensions[0], screen_dimensions[1])
        self.half_width = screen_dimensions[0] / 2
        self.half_height = screen_dimensions[1] / 2

        self.last_thirty_target_positions = [[coord for coord in self.target_position]]

        self.camera_y_offset = 0.0
        self.camera_y_offset_limits = (-120, 80)
        self.camera_offset_speed = 0.0
        self.camera_offset_acceleration = 600.0
        self.camera_offset_top_speed = 600.0
        self.pan_camera_up = False
        self.pan_camera_down = False

    def process_input(self, event):
        """
        Handle direct camera controls. It'ss possible we might need a bunch of different control & movement schemes
        if this is to be a generic class in the future.

        IDEAS:
            - edge scrolling with mouse
            - grab drag scrolling (mouse or tablet style)
            - analogue stick control (for control pad)
        :param event:
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.pan_camera_up = True
                self.pan_camera_down = False
            if event.key == pygame.K_DOWN:
                self.pan_camera_down = True
                self.pan_camera_up = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self.pan_camera_up = False
            if event.key == pygame.K_DOWN:
                self.pan_camera_down = False

    def set_target_position(self, target):
        self.target_position = [target[0], target[1]]

    def reset_camera_tracking(self):
        self.last_thirty_target_positions[:] = []

    def update(self, time_delta):
        """
        Here we handle the actual movement of the camera on a per frame basis. Currently used mainly as a follow camera
        with a queue of target positions helping to smooth out the camera movement and create a 'dynamic' feeling
        follow lag.

        :param time_delta:
        :return:
        """
        # Add player controls to pan the camera for vertical peeping
        if self.pan_camera_up:
            if self.camera_offset_speed < 0.0:
                self.camera_offset_speed = 0.0
            self.camera_offset_speed += self.camera_offset_acceleration * time_delta
            self.camera_offset_speed = min(self.camera_offset_top_speed, self.camera_offset_speed)
            if self.camera_y_offset > self.camera_y_offset_limits[0]:
                self.camera_y_offset -= self.camera_offset_speed * time_delta
        elif self.pan_camera_down:
            if self.camera_offset_speed > 0.0:
                self.camera_offset_speed = 0.0
            self.camera_offset_speed -= self.camera_offset_acceleration * time_delta
            self.camera_offset_speed = max(-self.camera_offset_top_speed, self.camera_offset_speed)
            if self.camera_y_offset < self.camera_y_offset_limits[1]:
                self.camera_y_offset -= self.camera_offset_speed * time_delta
        else:
            self.camera_offset_speed = 0.0
            if self.camera_y_offset > 10.0:
                self.camera_y_offset -= self.camera_offset_top_speed * time_delta
            elif self.camera_y_offset < -10.0:

                self.camera_y_offset += self.camera_offset_top_speed * time_delta
            else:
                self.camera_y_offset = 0.0

        # Add new target positions to the queue, perhaps this should be done via a timer instead of on a per frame
        # basis - this way the amount of camera follow lag is dependent on the frame rate.
        # TODO: re-implement target position queue to use a timer rather than just frame loops
        if len(self.last_thirty_target_positions) < 30:
            self.last_thirty_target_positions.append([self.target_position[0], self.target_position[1]])
        else:
            self.last_thirty_target_positions.pop(0)
            self.last_thirty_target_positions.append([self.target_position[0], self.target_position[1]])

        total_x = 0
        total_y = 0
        for position in self.last_thirty_target_positions:
            total_x += position[0]
            total_y += position[1]

        # Currently casting the camera position to an int to stabilise tiny movements which  I believe can make objects
        # in the game appear to judder between two pixel positions sometimes.
        # TODO: Consider if there is a better way to stabilise camera movement?
        self.position = [int(total_x / len(self.last_thirty_target_positions)),
                         int((total_y / len(self.last_thirty_target_positions)) + self.camera_y_offset)]

        if self.position[1] < self.half_height:
            self.position[1] = self.half_height
        if self.position[0] < self.half_width:
            self.position[0] = self.half_width

        if self.position[1] > self.world_dimensions[1] - self.half_height:
            self.position[1] = self.world_dimensions[1] - self.half_height
        if self.position[0] > self.world_dimensions[0] - self.half_width:
            self.position[0] = self.world_dimensions[0] - self.half_width
