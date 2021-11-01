import numpy as np
import pygame
from body import *

arrow_vertices = (np.array(((0, 100), (0, 200), (200, 200), (200, 300), (300, 150), (200, 0), (200, 100)))-150)*np.array([1.35,0.65])/5

def draw_vector(surf: pygame.Surface, vector: np.ndarray, scale: float, pos) -> None:
    '''
        Draws the vector vector on the surface surf with a length of scale in the (x,y) position pos
    '''
    angle = np.arccos(np.clip(vector[0]/np.linalg.norm(vector), -1.0, 1.0))
    if vector[1] > 0:
        angle *= -1
    poly = arrow_vertices*min(np.log(scale*2+1),30) # scale the polygon based on gravitational force
    poly = rotate(poly, angle) # apply the correct rotation
    poly += pos # translate to the right position
    pygame.draw.polygon(surf, (255,255,255), poly)
    

def rotate(x: np.ndarray, angle: float) -> np.ndarray:
    '''
        Rotates the 2d polygon described by the list of its vertices x by the given angle (in radians)
    '''
    rotation_mat = np.array([[np.math.cos(angle), -np.math.sin(angle)], 
                            [np.math.sin(angle), np.math.cos(angle)]])
    return x@rotation_mat

class Space:

    def __init__(self, bodies=None, tick_time=1):
        '''
            tick_time -> the amount of days worth of physics calculated at each call
            of a function
        '''
        self.bodies = [] if bodies is None else bodies
        self.tick_time = tick_time

    def on_click(self):
        pos = pygame.mouse.get_pos()
        self.bodies.append(Body(pos, 1e2))
    
    def get_body(self, pos) -> Body:
        for body in self.bodies:
            if body.is_on_body(pos):
                return body
        return None

    def render_grav_field(self, surf: pygame.Surface, margin=100, W=800, H=600) -> None:
        for i in range(0,W,margin):
            for j in range(0,H,margin):
                pos = np.array([i,j])
                pull = np.sum([body.get_grav_pull(pos, self.tick_time) for body in self.bodies], axis=0)
                intensity = min(1.35*np.linalg.norm(pull)/(self.tick_time), 3.5*margin/150)
                should_draw = True
                for body in self.bodies:
                    if np.linalg.norm(pos-body.pos) < margin:
                        should_draw = False
                if not should_draw:
                    continue
                draw_vector(surf, pull, intensity, pos)

    def update(self) -> None:
        for i in range(len(self.bodies)):
            for j in range(len(self.bodies)):
                if i == j:
                    continue
                self.bodies[i].gravitate(self.bodies[j], self.tick_time)
        
        for body in self.bodies:
            body.update(self.tick_time)

    def render(self, surf: pygame.Surface) -> None:
        for body in self.bodies:
            body.render(surf)