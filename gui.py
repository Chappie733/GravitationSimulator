import pygame
import os
from body import Body
import time

class UI:

    def __init__(self) -> None:
        self.widgets = []
        self.enabled = True

    def handle_event(self, event, mouse_pos=None, mouse_vel=None) -> None:
        '''
            Handles the pygame event event.\n
            mouse_pos -> position of the mouse.\\
            mouse_vel -> displacement of the mouse from the last tick (in pixels).
        '''
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()       
            for widget in self.widgets:
                widget.on_click(mouse_pos)

        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
            for widget in self.widgets:
                widget.on_mouse_motion(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
            for widget in self.widgets:
                widget.on_click_release(mouse_pos, mouse_vel)

    def render(self, surf):
        if not self.enabled:
            return

        for widget in self.widgets:
            widget.render(surf)

    def add_widget(self, widget) -> None:
        self.widgets.append(widget)

class UIElement:
    font = None

    # make a list of children GUIelements, so that their position and whether they
    # are enabled or not depends on the parameters of their parent 
    def __init__(self, pos, size, texture=None, parent=None) -> None:
        '''
            pos -> position of the top-left corner of the gui element
            size -> width and height of the gui element (w,h)
            texture -> pygame image of the texture to be used
        '''
        self.pos = pos
        self.enabled = False
        self.size = size
        self.parent = parent
        self.texture = texture
        if texture is not None:
            if isinstance(texture, str):
                self.texture = pygame.image.load(os.path.join('res', texture))
            self.texture = pygame.transform.scale(self.texture, size)       

    def on_click(self, mouse_pos) -> None:
        self.enabled = False
        abs_pos_off = (0,0) if self.parent is None else self.parent.pos # absolute position offset
        if abs_pos_off[0]+self.pos[0] < mouse_pos[0] < abs_pos_off[0]+self.pos[0] + self.size[0]: # x intersection
            if abs_pos_off[1]+self.pos[1] < mouse_pos[1] < abs_pos_off[1]+self.pos[1] + self.size[1]: # y intersection
                self.enabled = True

    def on_mouse_motion(self, *args) -> None: pass
    def on_click_release(self, *args) -> None: pass

    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            src = (0,0) if self.parent is None else self.parent.pos
            surf.blit(self.texture, (src[0]+self.pos[0], src[1]+self.pos[1]))

    @staticmethod
    def init_font(W=800):
        '''
            W -> the width of the screen, the font is set to assume the screen ratio is 4:3
        '''
        UIElement.font = pygame.font.SysFont(None, int(23*W/800.0))


class ProgressBar(UIElement):
    BACKGROUND_COLOR = (255,128,0)
    PROGRESS_COLOR = (255,255,0)

    def __init__(self, pos, size, min_val=0, val=50, max_val=100, parent=None) -> None:
        super().__init__(pos, size, parent=parent)
        self.min_val = min_val
        self.max_val = max_val
        self.val = val

    def on_click(self, mouse_pos) -> None:
        super().on_click(mouse_pos)
        if self.enabled:
            rel_mouse_x = mouse_pos[0] if self.parent is None else mouse_pos[0]-self.parent.pos[0]
            self.val = self.min_val+(self.max_val-self.min_val)*(rel_mouse_x-self.pos[0])/self.size[0]

    def on_mouse_motion(self, mouse_pos, *args) -> None:
        if pygame.mouse.get_pressed()[0]:
            self.on_click(mouse_pos)
    
    def render(self, surf: pygame.Surface) -> None:
        prog_w = int((self.val-self.min_val)/(self.max_val-self.min_val)*self.size[0]) # width of the progress color (in pixels)
        src = (0,0) if self.parent is None else self.parent.pos
        pygame.draw.rect(surf, self.BACKGROUND_COLOR, (src[0]+self.pos[0], src[1]+self.pos[1], self.size[0], self.size[1]))
        pygame.draw.rect(surf, self.PROGRESS_COLOR, (src[0]+self.pos[0], src[1]+self.pos[1], prog_w, self.size[1]))


class PlanetUI(UIElement):
    MOON_MASS = 1.230312630186531e-2 # mass of the moon/mass of the earth
    MAX_THROW_VEL = 30 # maximum velocity at which an object can be thrown
    MIN_THROW_VEL = 0.4 # minimum velocity at which an object can be thrown
    MIN_CLICK_THROW_TIME = 0.5 # minimum amount of time (in seconds) for which an object has to be clicked in order to be thrown
    # minimum amount of time (in seconds) for which an object has to be clicked in order to change its velocity when it's dragged
    MIN_CLICK_CHANGE_VEL_TIME = 0.1 
#    SUN_MASS = 3.32954355178996e5 # mass of the sun/mass of the earth

    def __init__(self, w, h) -> None:
        super().__init__((int(500*w/800),int(20*h/600)), (int(256*w/800),int(166*h/600)), "gui_background.png")
        # the values were adjusted for this resolution, this way they can be scaled to any given resolution
        self.x_ratio, self.y_ratio = w/800.0, h/600.0 
        self.mass_bar = ProgressBar((int(30*self.x_ratio), int(43*self.y_ratio)), (int(190*self.x_ratio),int(22*self.y_ratio)), 
                                    min_val=self.MOON_MASS, val=1, max_val=10**6, parent=self)
        self.radius_bar = ProgressBar((int(32*self.x_ratio),int(97*self.y_ratio)), (int(190*self.x_ratio), int(22*self.y_ratio)), 
                                    min_val=1, val=3, max_val=17, parent=self)
        self.body = None
        self.dragging = False # whether the selected body is being dragged
        self.click_start = 0

    def update_texts(self) -> None:
        self.vel_text = super().font.render(str(round(self.body.get_abs_vel(), 2))+"*10^6 km/day", False, (255,255,255))
        # only update the text of the mass if it has been changed
        if self.mass_bar.enabled or 'mass_text' not in dir(self): 
            mass_text = "%.3g" % (self.body.mass*Body.EARTH_MASS) # in exponential notation ex. 1.00e5 -> 1*10^(5)
            self.mass_text = super().font.render(mass_text.replace("e", "*10^").replace("+","") + " kg", False, (255,255,255))

    def on_click(self, mouse_pos) -> None:
        self.mass_bar.on_click(mouse_pos)
        self.radius_bar.on_click(mouse_pos)
        if self.body is not None:
            if self.body.is_on_body(mouse_pos):
                self.dragging = True
                self.click_start = time.time()

    def on_mouse_motion(self, mouse_pos) -> None:
        self.mass_bar.on_mouse_motion(mouse_pos)
        self.radius_bar.on_mouse_motion(mouse_pos)
        if self.dragging:
            self.body.set_pos(mouse_pos)
            if self.body.get_abs_vel() != 0 and time.time()-self.click_start > self.MIN_CLICK_CHANGE_VEL_TIME:
                self.body.set_vel((0,0))
    
    def on_click_release(self, *args) -> None:
        if self.dragging:
            self.dragging = False
            # looks dumb but this way I don't have to import numpy just for this one line
            if time.time() - self.click_start > self.MIN_CLICK_THROW_TIME:
                if self.MIN_THROW_VEL < (args[1][0]**2+args[1][0]**2)**(0.5) < self.MAX_THROW_VEL: 
                    self.body.set_vel(args[1]) # args[1] is the displacement of the mouse from the last frame

    def log_body(self, body: Body, enable=True, mouse_pos=None) -> None:
        if body is None:
            mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
            super().on_click(mouse_pos)
            return
        self.enabled = enable
        self.mass_bar.val = body.mass
        self.radius_bar.val = body.radius
        self.body = body
        self.update_texts() # re-render the velocity text

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        if self.enabled:
            self.update_texts()
            self.mass_bar.render(surf)
            self.radius_bar.render(surf)
            surf.blit(self.vel_text, (self.pos[0]+int(115*self.x_ratio), self.pos[1]+int(135*self.y_ratio))) # velocity text
            surf.blit(self.mass_text, (self.pos[0]+int(105*self.x_ratio), self.pos[1]+int(20*self.y_ratio)))

            # if the mass or the radius was changed, change the body's parameters accordingly
            if self.mass_bar.enabled:
                self.body.set_mass(self.mass_bar.val)
            elif self.radius_bar.enabled: 
                self.body.radius = int(self.radius_bar.val)