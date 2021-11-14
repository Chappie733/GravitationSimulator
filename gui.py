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
        else:
            for widget in self.widgets:
                widget.handle_event(event)

    def update(self):
        for widget in self.widgets:
            widget.update()

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
        self.enabled = self.is_on_element(mouse_pos)

    def is_on_element(self, mouse_pos) -> bool:
        on_element = False
        abs_pos_off = (0,0) if self.parent is None else self.parent.pos # absolute position offset
        if abs_pos_off[0]+self.pos[0] < mouse_pos[0] < abs_pos_off[0]+self.pos[0] + self.size[0]: # x intersection
            if abs_pos_off[1]+self.pos[1] < mouse_pos[1] < abs_pos_off[1]+self.pos[1] + self.size[1]: # y intersection
                on_element = True
        return on_element

    def on_mouse_motion(self, *args) -> None: pass
    def on_click_release(self, *args) -> None: pass
    def handle_event(self, *args) -> None: pass
    def update(self, *args) -> None: pass

    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            src = (0,0) if self.parent is None else self.parent.pos
            surf.blit(self.texture, (src[0]+self.pos[0], src[1]+self.pos[1]))

    @staticmethod
    def init_font(W=800) -> None:
        '''
            W -> the width of the screen, the font is set to assume the screen ratio is 4:3
        '''
   #     font_location = pygame.font.match_font('arial')
    #    UIElement.font = pygame.font.Font(font_location, int(23*W/800.0))
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


class TextBox(UIElement):

    def __init__(self, pos, size, max_len=9, texture=None, parent=None) -> None:
        super().__init__(pos, size, texture=texture, parent=parent)
        self.content = ""
        self.text = self.font.render("", False, (255,255,255))
        self.max_len = max_len
        self.char_size = (int(self.size[0]/self.max_len*3/4), int(self.size[1]*3/5))

    def set_text(self, text) -> None:
        self.content = text
        text_size = (int(self.char_size[0]*len(self.content)), int(self.char_size[1]))
        self.text = pygame.transform.scale(self.font.render(self.content, False, (255,255,255)), text_size) # the text has to be re-rendered

    def handle_event(self, event) -> None:
        if not self.enabled:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == 8 and len(self.content) > 0: # delete key has been pressed
                self.set_text(self.content[:-1])
            elif len(self.content) < self.max_len and event.key not in (8,pygame.K_LSHIFT,pygame.K_RSHIFT,pygame.K_ESCAPE):
                keys = pygame.key.get_pressed()
                addition = chr(event.key)
                if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
                    addition = chr(event.key-32)
                self.set_text(self.content+addition)

    def render(self, surf: pygame.Surface) -> None:
        pos = self.pos if self.parent is None else (self.parent.pos[0]+self.pos[0], self.parent.pos[1]+self.pos[1])
        surf.blit(self.texture, (pos[0], pos[1]))
        surf.blit(self.text, (pos[0]+int(self.size[0]/18), pos[1] + int(self.size[1]*1/4)))
        if time.time() % 1 > 0.5 and self.enabled:
            cursor_x_offset = int(self.size[0]*(len(self.content)+1)/self.max_len*3/4)
            pygame.draw.rect(surf, (255,255,255), (pos[0]+cursor_x_offset, pos[1] + int(self.size[1]*1/4), self.char_size[0], self.char_size[1]))

class Button(UIElement):

    # textures is a list of textures that are drawn corresponding to the state
    # of the button, 0 -> normal, 1 -> hovered, 2 -> clicked
    def __init__(self, pos, size, textures=None, parent=None) -> None:
        super().__init__(pos, size, parent=parent)
        self.state = 0 # default state
        self.enabled = True
        self.textures = []
        # make sure the game doesn't crash if a button is created without any custom
        textures = textures if textures is not None else ["button_default.png",
                                                          "button_hovered.png",
                                                          "button_clicked.png"]
        for texture in textures:
            if isinstance(texture, str):
                texture = pygame.image.load(os.path.join('res', texture))
            self.textures.append(pygame.transform.scale(texture, size))

    def on_click(self, mouse_pos) -> None:
        if self.is_on_element(mouse_pos):
            self.state = 2

    def on_click_release(self, *args) -> None:
        if self.state == 2:
            self.state = 1
    
    def on_mouse_motion(self, mouse_pos) -> None:
        if super().is_on_element(mouse_pos) and self.state != 2:
            self.state = 1
        elif self.state != 0:
            self.state = 0
            
    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            src = (0,0) if self.parent is None else self.parent.pos
            surf.blit(self.textures[self.state], (self.pos[0]+src[0], self.pos[1]+src[1]))

class CheckBox(UIElement):

    def __init__(self, pos, size, textures=None, parent=None) -> None:
        super().__init__(pos, size, parent=parent)
        self.ticked = False
        self.texture_state = 0 # texture state (0 -> unticked, 1 -> clicked (but click not yet released), 2 -> ticked)
        self.textures = []
        # make sure the game doesn't just crash if no custom texture is loaded
        textures = textures if textures is not None else ["checkbox_unticked.png",
                                                          "checkbox_click.png",
                                                          "checkbox_ticked.png"]
        for texture in textures:
            if isinstance(texture, str):
                texture = pygame.image.load(os.path.join('res', texture))
            self.textures.append(pygame.transform.scale(texture, size))

    def on_click(self, mouse_pos) -> None:
        if super().is_on_element(mouse_pos):
            self.texture_state = 1

    def on_click_release(self, mouse_pos, *args) -> None:
        if super().is_on_element(mouse_pos):
            self.ticked = not self.ticked
            self.texture_state = 2*int(self.ticked)
        
    def render(self, surf: pygame.Surface) -> None:
        src = (0,0) if self.parent is None else self.parent.pos
        surf.blit(self.textures[self.texture_state], (self.pos[0]+src[0], self.pos[1]+src[1]))

class TimeUI(UIElement):

    def __init__(self, w, h) -> None:
        super().__init__((0,0), (int(196*w/800),int(49*h/600)), "time_gui_background.png")
        self.days = 0
        self.x_ratio, self.y_ratio = w/800.0, h/600.0 
        self.enabled = True

    def on_click(self, mouse_pos) -> None: pass

    def _update_text(self):
        self.time_text = self.font.render(f"Giorni passati: {self.days}", False, (255,255,255))
        self.time_text = pygame.transform.scale(self.time_text, (int(182*self.x_ratio), int(19*self.y_ratio)))

    def update(self, *args) -> None:
        self.days += 1

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        self._update_text()
        surf.blit(self.time_text, (int(5*self.x_ratio), int(10*self.y_ratio)))

class PlanetUI(UIElement):
    MOON_MASS = 1.230312630186531e-2 # mass of the moon/mass of the earth
    MAX_THROW_VEL = 30 # maximum velocity at which an object can be thrown
    MIN_THROW_VEL = 0.4 # minimum velocity at which an object can be thrown
    MIN_CLICK_THROW_TIME = 0.3 # minimum amount of time (in seconds) for which an object has to be clicked in order to be thrown
    # minimum amount of time (in seconds) for which an object has to be clicked in order to change its velocity when it's dragged
    MIN_CLICK_CHANGE_VEL_TIME = 0.1 
#    SUN_MASS = 3.32954355178996e5 # mass of the sun/mass of the earth

    def __init__(self, w, h) -> None:
        super().__init__((int(500*w/800),int(400*h/600)), (int(256*w/800),int(166*h/600)), "gui_background.png")
        # the values were adjusted for this resolution, this way they can be scaled to any given resolution
        self.x_ratio, self.y_ratio = w/800.0, h/600.0 
        self.mass_bar = ProgressBar((int(30*self.x_ratio), int(43*self.y_ratio)), (int(190*self.x_ratio),int(22*self.y_ratio)), 
                                    min_val=self.MOON_MASS, val=1, max_val=10**6, parent=self)
        self.radius_bar = ProgressBar((int(32*self.x_ratio),int(97*self.y_ratio)), (int(190*self.x_ratio), int(22*self.y_ratio)), 
                                    min_val=1, val=3, max_val=17, parent=self)
        self.name_bar = TextBox((int(20*self.x_ratio),int(-30*self.y_ratio)), (int(216*self.x_ratio), int(40*self.y_ratio)), 
                                    max_len=9, texture='planet_name_background.png', 
                                    parent=self)
        self.body = None
        self.dragging = False # whether the selected body is being dragged
        self.click_start = 0

    def update_texts(self, force_update=False) -> None:
        '''
            Update the info text about the selected body.\n
            force_update -> whether to force the update of the text of the mass of the body, if it's false (as default)
            it might not be updated due to an optimization technique.
        '''
        self.vel_text = super().font.render(str(round(self.body.get_abs_vel(), 2))+"*10^6 km/day", False, (255,255,255))
        # only update the text of the mass if it has been changed
        if self.mass_bar.enabled or 'mass_text' not in dir(self) or force_update: 
            mass_text = "%.3g" % (self.body.mass*Body.EARTH_MASS) # in exponential notation ex. 1.00e5 -> 1*10^(5)
            self.mass_text = super().font.render(mass_text.replace("e", "*10^").replace("+","") + " kg", False, (255,255,255))

    def on_click(self, mouse_pos) -> None:
        self.mass_bar.on_click(mouse_pos)
        self.radius_bar.on_click(mouse_pos)
        self.name_bar.on_click(mouse_pos)
        if self.name_bar.enabled:
            self.enabled = True
        if self.body is not None:
            if self.body.is_on_body(mouse_pos):
                self.dragging = True
                self.click_start = time.time()

    def handle_event(self, event) -> None:
        self.name_bar.handle_event(event)
        if self.name_bar.enabled and event.type == pygame.KEYDOWN: # a letter has been typed in the name field
            self.body.name = self.name_bar.content

    def on_mouse_motion(self, mouse_pos) -> None:
        if self.dragging:
            self.body.set_pos(mouse_pos)
            if self.body.get_abs_vel() != 0 and time.time()-self.click_start > self.MIN_CLICK_CHANGE_VEL_TIME:
                self.body.set_vel((0,0))
            self.enabled = not self.is_on_element(mouse_pos)
        else:
            self.mass_bar.on_mouse_motion(mouse_pos)
            self.radius_bar.on_mouse_motion(mouse_pos)
    
    def on_click_release(self, *args) -> None:
        if self.dragging:
            self.dragging = False
            # looks dumb but this way I don't have to import numpy just for this one line
            if time.time() - self.click_start > self.MIN_CLICK_THROW_TIME:
                if self.MIN_THROW_VEL < (args[1][0]**2+args[1][0]**2)**(0.5) < self.MAX_THROW_VEL: 
                    self.body.set_vel(args[1]) # args[1] is the displacement of the mouse from the last frame

    def log_body(self, body: Body, mouse_pos=None) -> None:
        mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
        super().on_click(mouse_pos)
        # if there is no body or the click was on the GUI just do nothing
        if body is None or self.enabled: 
            return
        self.enabled = True
        self.mass_bar.val = body.mass
        self.radius_bar.val = body.radius
        self.body = body
        self.update_texts(force_update=True) # re-render the velocity and mass text
        self.name_bar.set_text(self.body.name)

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

            self.body.render_velocity(surf)
            self.name_bar.render(surf)