import numpy as np
import pygame
from body import *
from widgets import UIElement

class Space:
    SAVE_OBJECT_DELIMETER = "-"*20+"\n" # the delimeter between one thing and another when saving the space in a file
    SAVES_PATH = os.path.join(path, 'saves')

    def __init__(self, bodies=None, tick_time=1, W=800.0, H=600.0):
        '''
            tick_time -> the amount of days worth of physics calculated at each call
            of a function
        '''
        self.bodies = [] if bodies is None else bodies
        self.tick_time = tick_time
        self.renders_field = True
        self.margin = int(75*(W+H)/1400.0) # margin (in pixels) between each vector in the vector field
        self.time_passed = 0 # days passed
        self.name = "Space"

    def on_window_resize(self, wnew, hnew):
        self.margin = int(75*(wnew+hnew)/1400.0)

    def get_body(self, pos) -> Body:
        for body in self.bodies:
            if body.is_on_body(pos):
                return body
        return None

    def render_grav_field(self, surf: pygame.Surface, W=800, H=600) -> None:
        for i in range(0, W, self.margin):
            for j in range(0, H, self.margin):
                pos = np.array([i,j])
                pull = np.sum([body.get_grav_pull(pos, self.tick_time) for body in self.bodies], axis=0)
                intensity = min(1.35*np.linalg.norm(pull)/(self.tick_time), 3.5*self.margin/150)
                should_draw = intensity != 0
                for body in self.bodies:
                    if np.linalg.norm(pos-body.pos) < self.margin-body.radius:
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
        
        self.time_passed += self.tick_time
        for body in self.bodies:
            body.update(self.tick_time)

    def render(self, surf: pygame.Surface, W=800, H=600) -> None:
        if self.renders_field:
            self.render_grav_field(surf, W, H)
        
        for body in self.bodies:
            body.render(surf)
    
    def get_str_representation(self) -> str:
        '''
            Returns a string representation of the space's properties (the bodies are excluded)
        '''
        space_repr = "SPACE\n"
        space_repr += f"tick time:{self.tick_time}\nrenders field:{int(self.renders_field)}\n"
        space_repr += f"margin:{int(self.margin)}\ntime passed:{self.time_passed}\n"
        return space_repr

    def highlight(self, bodies, unhighlight_others=True) -> None:
        ''' Highlights the given bodies '''
        for body in self.bodies:
            if unhighlight_others:
                body.highlighted = body in bodies
            else:
                if body in bodies:
                    body.highlighted = True

    def remove_bodies(self, bodies: list) -> None:
        for body in bodies:
            if body in self.bodies:
                self.bodies.remove(body)

    def get_highlighted(self) -> list:
        ''' Returns all the highlighted bodies '''
        highlighted = []
        for body in self.bodies:
            if body.highlighted:
                highlighted.append(body)
        return highlighted

    def load_from_representation(self, representation: str) -> None:
        '''
            Loads the values of the space object from its corresponding string representation
        '''
        lines = representation.split('\n')[1:-1] # remove "SPACE"
        properties = dict([line.split(':') for line in lines])
        self.tick_time = float(properties['tick time'])
        self.renders_field = bool(int(properties['renders field']))
        self.margin = int(properties['margin'])
        self.time_passed = float(properties['time passed'])

    def get_bodies_in_area(self, x, y, w, h):
        '''
            Returns all the bodies in the given rectangular area with (x,y) as its top-left vertex (in pixels)
            and a size of (w,h) as (respectively) its width and height
        '''
        # make sure to shift the intervals if the width or the height is negative
        if w < 0:
            x += w
            w *= -1
        if h < 0:
            y += h
            h *= -1
        bodies = []
        for body in self.bodies:
            if x <= body.pos[0] <= x+w and y <= body.pos[1] <= y+h:
                bodies.append(body)
        return bodies

    def save(self, filename):
        # if the saves folder isn't there create it
        if 'saves' not in os.listdir(path):
            os.mkdir(self.SAVES_PATH)
        try:
            file = open(os.path.join(self.SAVES_PATH, filename), 'w')
        except OSError:
            UIElement.popup_msg.cast("Invalid name!", 3, 0.4)
            return

        # actual saving
        file.write(self.get_str_representation())
        file.write(self.SAVE_OBJECT_DELIMETER)
        for body in self.bodies:
            file.write(body.get_str_representation())
            file.write(self.SAVE_OBJECT_DELIMETER)

        file.close()
        
    def load(self, filename):
        file = open(os.path.join(self.SAVES_PATH, filename), 'r')
        content = file.read().split(self.SAVE_OBJECT_DELIMETER)[:-1] # the last string is just empty
        file.close()
        self.load_from_representation(content[0])
        self.bodies = []
        for body_repr in content[1:]:
            new_body = Body((0,0),1)
            new_body.load_from_representation(body_repr)
            self.bodies.append(new_body)