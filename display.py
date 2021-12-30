import pygame

class Display():

    def __init__(self, w=800, h=600) -> None:
        self.w, self.h = w, h
        self.fullscreen = False
        self.brightness = 255
        self.brightness_mask = pygame.Surface((w,h), pygame.SRCALPHA)
        self.brightness_mask.fill((0,0,0,0))

    def create(self, caption: str, icon: pygame.Surface, fullscreen=False) -> None:
        self.win = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption(caption)
        pygame.display.set_icon(icon)
        self.fullscreen = fullscreen

    def on_resize(self, new_w, new_h, fullscreen=False):
        self.w, self.h = new_w, new_h
        self.fullscreen = fullscreen
        self.win = pygame.display.set_mode((new_w, new_h), pygame.FULLSCREEN if fullscreen else 1)
        self.brightness_mask = pygame.Surface((new_w,new_h), pygame.SRCALPHA)
        self.brightness_mask.fill((0,0,0,255-self.brightness))

    def set_brightness(self, brightness: int) -> None:
        self.brightness_mask.fill((0,0,0,255-brightness))
        self.brightness = brightness

    def render(self, surf: pygame.Surface):
        self.win.blit(surf, (0,0))
        self.win.blit(self.brightness_mask, (0,0))

    def get_size(self) -> tuple:
        return (self.w, self.h)