import pygame
from utils import *

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
        '''
            Updates the body's position to the one after time_step days have passed
        '''
        self.pos += self.vel*time_step

    def render(self, surf: pygame.Surface) -> None:
        '''
            Renders the body on the given pygame surface surf.
        '''
        pygame.draw.circle(surf, self.COLOR, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def render_velocity(self, surf: pygame.Surface) -> None:
        '''
            Renders the velocity vector of the body in its position
        '''
        if self.get_abs_vel() != 0:
            draw_vector(surf, self.vel, np.log(self.get_abs_vel()*1e-2+1), self.pos)

    def get_dist(self, pos) -> float:
        '''
            Returns the distance between the body and the given point
        '''
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
        '''
            Returns the gravitational field vector given by the attraction from this body in the
            given position over time_step amount of days
        '''
        if np.array_equal(self.pos, pos):
            return np.zeros(2)

        # the mass of the other object has to be converted to kilograms
        acc = self.G*(self.mass*self.EARTH_MASS)/((self.get_dist(pos)*1e6)**3)
        acc = acc*(self.pos-pos)*(86400)**2*time_step
        return acc

    def get_abs_vel(self) -> float:
        '''
            Returns the length of the velocity vector of the body
        '''
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

    def get_mass_kg(self) -> float:
        '''
            Returns the mass of the object in kilograms
        '''
        return self.mass*Body.EARTH_MASS

    def get_mass_str(self) -> str:
        '''
            Returns a string with the mass of the object written in scientific
            notation in kilograms
        '''
        return ("%.3g" % self.get_mass_kg()).replace("e", "*10^").replace("+","") + " kg"