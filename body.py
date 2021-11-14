import pygame
import numpy as np

arrow_vertices = (np.array(((0, 100), (0, 200), (200, 200), (200, 300), (300, 150), (200, 0), (200, 100)))-150)*np.array([1.35,0.65])/5

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

# mass = 1 -> the mass of the body is the mass of the eart (5.972 x 10^24 Kg)
# with 1 pix = 10^6 km
# G is normally 10**-11 m^3/(Kg*s^2) = 10^-20 km^3/(Kg*s^2) = 10^-14 pix/(Kg*s^2)
class Body:
    G = 6.7408e-20
    EARTH_MASS = 5.9722e24
    COLOR = (153,102,0)

    def __init__(self, pos, mass, name="Body") -> None:
        if not isinstance(pos, np.ndarray):
            pos = np.array(pos, dtype=np.float64)
        self.pos = pos
        self.mass = mass
        self.vel = np.zeros((2,), dtype=np.float64)
        self.radius = max(int(np.log(self.mass*20+1)),1)
        self.name = name

    def update(self, time_step) -> None:
        self.pos += self.vel*time_step

    def render(self, surf: pygame.Surface) -> None:
        pygame.draw.circle(surf, self.COLOR, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def render_velocity(self, surf: pygame.Surface) -> None:
        if self.get_abs_vel() != 0:
            draw_vector(surf, self.vel, np.log(self.get_abs_vel()*1e-2+1), self.pos)

    def get_dist(self, pos):
        return np.linalg.norm(self.pos-pos)

    def set_mass(self, mass):
        self.mass = mass
        self.radius = max(int(np.log(self.mass*20+1)),1)

    def gravitate(self, other, time_step):
        '''
            Apply the correct acceleration to move towards the body other
        '''
        # the mass of the other object has to be converted to kilograms
        acc = self.G*(other.mass*self.EARTH_MASS)/((self.get_dist(other.pos)*1e6)**3)
        acc = acc*(other.pos-self.pos)*(86400)**2*time_step
        self.vel += acc

    def get_grav_pull(self, pos: np.ndarray, time_step):
        if np.array_equal(self.pos, pos):
            return np.zeros(2)

        # the mass of the other object has to be converted to kilograms
        acc = self.G*(self.mass*self.EARTH_MASS)/((self.get_dist(pos)*1e6)**3)
        acc = acc*(self.pos-pos)*(86400)**2*time_step
        return acc

    def get_abs_vel(self) -> float:
        return np.linalg.norm(self.vel)

    def is_on_body(self, pos) -> bool:
        '''
            Returns whether the pixel at position pos=(xpos, ypos) is inside the body
        '''
        return np.linalg.norm(self.pos-pos) <= self.radius

    def set_pos(self, pos) -> None:
        self.pos = np.array(pos, dtype=np.float64)
    
    def set_vel(self, vel) -> None:
        self.vel = np.array(vel, dtype=np.float64)