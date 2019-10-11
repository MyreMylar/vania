import pygame


class AnimSet:
    """
    A class to represent a single animation movement, e.g. run cycle, attack, jump, slide.

    There are various parameters to setup the animation set and control it's playback speed, sometimes we might want
    this playback speed to be data driven, other times we might want it to be dynamically driven by the code.

    TODO: Do we need a 'finished' test function for non looping animations?
    TODO: Add a capacity to set animation frame 'events' so that we can activate code at specific named points in an
          animation. Use pygame event queue?
    """
    def __init__(self, atlas_surface, start_pos, frame_size, num_frames,
                 base_speed, centre_offset, looping=True, x_flip=False):
        self.speed = base_speed
        self.speed_factor = 1.0
        self.looping = looping
        self.frames = []
        self.centre_offset = centre_offset
        atlas_position = start_pos
        for frame_num in range(0, num_frames):
            frame_rect = pygame.Rect(atlas_position, frame_size)
            frame_surf = atlas_surface.subsurface(frame_rect)
            if x_flip:
                frame_surf = pygame.transform.flip(frame_surf, True, False)
            self.frames.append(frame_surf)
            atlas_position[0] += frame_size[0]

        self.current_frame = self.frames[0]
        self.frame_index = 0
        self.next_frame_acc = 0.0
        self.running = True

    def start(self):
        """
        Starts an animation set playing from the beginning.
        :return:
        """
        self.speed_factor = 1.0
        self.frame_index = 0
        self.next_frame_acc = 0.0
        self.running = True
        self.current_frame = self.frames[0]

    def set_speed_factor(self, speed_factor):
        """
        The speed factor allows dynamic code control of the animation playback speed.

        :param speed_factor: A value of 1.0 is the default 'normal' playback speed, higher values will speed up the anim
                             lower values will slow it down.
        :return:
        """
        self.speed_factor = speed_factor

    def update(self, time_delta):
        """
        Updates the animation with the elapsed time per frame allowing the frames to be flipped through at the set
        speed.

        :param time_delta: the difference in time between the previous frame and the current one. In seconds.
        :return:
        """
        if self.running:
            self.next_frame_acc += time_delta * self.speed * self.speed_factor
            if self.next_frame_acc > 1.0:
                self.next_frame_acc = 0.0
                self.frame_index += 1
                if self.frame_index >= len(self.frames):
                    if not self.looping:
                        self.frame_index -= 1
                        self.running = False
                    else:
                        self.frame_index = 0
                self.current_frame = self.frames[self.frame_index]
