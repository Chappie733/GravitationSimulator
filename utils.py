import pygame
import numpy as np
import os

arrow_vertices = (np.array(((0, 100), (0, 200), (200, 200), (200, 300), (300, 150), (200, 0), (200, 100)))-150)*np.array([1.35,0.65])/5

import sys

if getattr(sys, 'frozen', False):
    path = os.path.dirname(sys.executable)
elif __file__:
    path = os.path.dirname(__file__)

res_path = os.path.join(path, 'res')

def rotate(x: np.ndarray, angle: float) -> np.ndarray:
    '''
        Rotates the 2d polygon described by the list of its vertices x by the given angle (in radians)
    '''
    rotation_mat = np.array([[np.math.cos(angle), -np.math.sin(angle)], 
                            [np.math.sin(angle), np.math.cos(angle)]])
    return x@rotation_mat

def draw_vector(surf: pygame.Surface, vector: np.ndarray, scale: float, pos) -> None:
    '''
        Draws the vector vector on the surface surf with a length of scale in the (x,y) position pos
    '''
    global arrow_vertices
    angle = np.arccos(np.clip(vector[0]/np.linalg.norm(vector), -1.0, 1.0))
    if vector[1] > 0:
        angle *= -1
    poly = arrow_vertices*min(np.log(scale*2+1),30) # scale the polygon based on gravitational force
    poly = rotate(poly, angle) # apply the correct rotation
    poly += pos # translate to the right position
    pygame.draw.polygon(surf, (255,255,255), poly)

def load_spritesheet(source, tile_w=32, tile_h=32, new_size=None):
    '''
        Loads the spritesheet in the source file where every texture has the given size.\n
        tile_w -> width of each tile\n
        tile_h -> height of each tile\n
        new_size -> the size to which each image is scaled after it's loaded
    '''
    if isinstance(source, str):
        source = pygame.image.load(os.path.join('res', source))
    
    textures = []
    num_x_tiles = source.get_width()//tile_w # number of tiles horizontally
    num_y_tiles = source.get_height()//tile_h # number of tiles vertically
    for y in range(num_y_tiles):
        for x in range(num_x_tiles):
            textures.append(source.subsurface(pygame.Rect(x*tile_w, y*tile_h, tile_w, tile_h)))
            if new_size is not None:
                textures[-1] = pygame.transform.scale(textures[-1], new_size)
    return textures

def load_texture(source: str, size=None) -> pygame.Surface:
    img = pygame.image.load(os.path.join(res_path, source))
    if size is not None:
        img = pygame.transform.scale(img, size)
    return img

def clamp(num, minimum=0, maximum=1):
    num = num if minimum <= num else minimum
    num = num if maximum >= num else maximum
    return num