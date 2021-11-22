import pygame
from utils import *

# mass = 1 -> the mass of the body is the mass of the eart (5.972 x 10^24 Kg)
# with 1 pix = 10^6 km
# G is normally 10**-11 m^3/(Kg*s^2) = 10^-20 km^3/(Kg*s^2) = 10^-14 pix/(Kg*s^2)
class Body:
    G = 6.7408e-20
    EARTH_MASS = 5.9722e24
    COLOR = (153,102,0)

    def __init__(self, pos: tuple, mass: float, name="Body") -> None:
        if not isinstance(pos, np.ndarray):
            pos = np.array(pos, dtype=np.float64)
        self.pos = pos
        self.mass = mass
        self.vel = np.zeros((2,), dtype=np.float64)
        self.radius = max(int(np.log(self.mass*20+1)),1)
        self.name = name

    def update(self, time_step: float) -> None:
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

    def get_dist(self, pos: tuple) -> float:
        '''
            Returns the distance between the body and the given point
        '''
        return np.linalg.norm(self.pos-pos)

    def set_mass(self, mass: float):
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

    def set_abs_vel(self, vel: float) -> None:
        '''
            Sets the length of the velocity vector, its direction and verse remain unchanged
        '''
        self.vel = (self.vel/np.linalg.norm(self.vel))*vel # unit vector in direction of velocity * length

    def is_on_body(self, pos) -> bool:
        '''
            Returns whether the pixel at position pos=(xpos, ypos) is inside the body
        '''
        return np.linalg.norm(self.pos-pos) <= self.radius

    def set_pos(self, pos) -> None:
        self.pos = np.array(pos, dtype=np.float64)
    
    def set_vel(self, vel) -> None:
        self.vel = np.array(vel, dtype=np.float64)

    def set_vel_angle(self, angle: float) -> None:
        '''
            Sets the angle of the velocity to the value of angle
        '''
        self.vel = np.array([np.cos(angle), -np.sin(angle)])*np.linalg.norm(self.vel)

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

    def get_vel_str(self) -> str:
        '''
            Returns a string with the velocity of the object written in scientific notation
            in kilometers/day
        '''
        return str(round(self.get_abs_vel(), 2))+"*10^6 km/day"

    def set_vel_str(self, vel: str) -> None:
        '''
            Sets the velocity of the body based on a string in the format "a*10^b km/day"
            (or just "a*10^b")
        '''
        vel = vel.replace("km/day", '').replace(' ', '')
        self.set_abs_vel(float(vel.replace('*10^', 'e'))/10**6)

    # TODO: make some input parsing to check whether the given string is a valid number
    # ex: it doesn't contain letters, punctuation or other weird characters
    def set_mass_str(self, mass: str) -> None:
        '''
            Sets the mass of the body based on a string in the format: a*10^b kg (or a*10^b),
            where the number represented by the string is in kilograms
        '''
        mass = mass.replace("kg", '').replace(' ', '') # remove kg and any eventual empty space
        self.set_mass(float(mass.replace('*10^', 'e'))/Body.EARTH_MASS) # switch to python's exponential notation and turn to float