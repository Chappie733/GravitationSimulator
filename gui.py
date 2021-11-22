import pygame
from body import Body
import time
from utils import load_texture, clamp, load_spritesheet, adapt_ratio, get_angle, rotate_texture

TIME_UPDATE_EVENT = pygame.USEREVENT+1

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

    def get_by_type(self, _type: type):
        '''
            Returns the first occurrence of the widget of the given type (_type),
            if no widget of type _type is found then None is returned instead.
        '''
        for widget in self.widgets:
            if type(widget) == _type:
                return widget
        return None


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
                self.texture = load_texture(texture)
            self.texture = pygame.transform.scale(self.texture, size)       

    def on_click(self, mouse_pos):
        self.enabled = self.is_on_element(mouse_pos)

    def is_on_element(self, mouse_pos) -> bool:
        on_element = False
        abs_pos_off = (0,0) if self.parent is None else self.parent.pos # absolute position offset
        if abs_pos_off[0]+self.pos[0] < mouse_pos[0] < abs_pos_off[0]+self.pos[0] + self.size[0]: # x intersection
            if abs_pos_off[1]+self.pos[1] < mouse_pos[1] < abs_pos_off[1]+self.pos[1] + self.size[1]: # y intersection
                on_element = True
        return on_element

    def on_mouse_motion(self, *args) -> None: pass
    def on_click_release(self, *args): pass
    def handle_event(self, *args) -> None: pass
    def update(self, *args) -> None: pass

    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            surf.blit(self.texture, self.get_abs_pos())

    def get_parent_pos(self) -> tuple:
        '''
            Returns the position of the parent widget
        '''
        return (0,0) if self.parent is None else self.parent.pos

    def get_abs_pos(self, pos=None) -> tuple:
        '''
            Returns the absolute position of the widget (relative to its parent), if
            pos is not passed this uses as a position the widget's position
        '''
        pos = pos if pos is not None else self.pos
        parent_pos = self.get_parent_pos()
        return (pos[0]+parent_pos[0], pos[1]+parent_pos[1])

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

    def __init__(self, pos, size, min_val=0, val=50, max_val=100, texture=None, parent=None, 
                interactable=True, discrete=False, fill_y_offset=0, fill_y_size=0, fill_color=None,
                continuous=True) -> None:
        '''
            pos -> (x,y) pixel position of the element\n
            size -> (width, height) pixel size of the element\n
            min_val -> the minimum value the progress bar can assume\n
            val -> the initial value of the progress bar\n
            max_val -> the maximum value of the progress bar\n
            texture -> background texture\n
            parent -> the parent widget of the element\n
            interactable -> whether the progress bar's value can be changed by clicking on it\n
            discrete -> whether the progress bar can only assume discrete values\n
            fill_y_offset -> the offset between the rendering position of the texture and that of the progress bar\n
            fill_y_size -> the size of the section filled to represent the progress
        '''
        super().__init__(pos, size, texture=texture, parent=parent)
        self.min_val = min_val
        self.max_val = max_val
        self.val = val
        self.interactable = interactable
        self.discrete = discrete
        self.fill_y_size = fill_y_size if fill_y_size != 0 else self.size[1]
        self.fill_y_offset = fill_y_offset
        self.fill_color = fill_color if fill_color is not None else self.PROGRESS_COLOR
        self.continuous = continuous

    def on_click(self, mouse_pos) -> bool:
        '''
            Returns true if the value of the progress bar has been changed
        '''
        super().on_click(mouse_pos)
        if self.enabled and self.interactable:
            rel_mouse_x = mouse_pos[0] if self.parent is None else mouse_pos[0]-self.parent.pos[0]
            self.val = self.min_val+(self.max_val-self.min_val)*(rel_mouse_x-self.pos[0])/self.size[0]
            if self.discrete:
                self.val = clamp(round(self.val), self.min_val+1, self.max_val)
            return True
        return False


    def on_mouse_motion(self, mouse_pos, *args) -> None:
        '''
            Returns whether the value of the progress bar was changed (which implies the mouse is clicked)
        '''
        if self.continuous and pygame.mouse.get_pressed()[0]:
            return self.on_click(mouse_pos)
    
    def render(self, surf: pygame.Surface) -> None:
        prog_w = int((self.val-self.min_val)/(self.max_val-self.min_val)*self.size[0]) # width of the progress color (in pixels)
        src = (0,0) if self.parent is None else self.parent.pos
        if self.texture is None:
            pygame.draw.rect(surf, self.BACKGROUND_COLOR, (src[0]+self.pos[0], src[1]+self.pos[1], self.size[0], self.size[1]))
        pygame.draw.rect(surf, self.fill_color, (src[0]+self.pos[0], src[1]+self.pos[1]+self.fill_y_offset, prog_w, self.fill_y_size))
        # draws the background image if it's present
        if self.texture is not None:
            surf.blit(self.texture, self.get_abs_pos(self.pos))


class TextBox(UIElement):
    DEFAULT_TEXTURE = load_texture('textbox.png')

    def __init__(self, pos, size, max_len=9, texture=None, parent=None, enable_on_click=False, letter_width=0.5) -> None:
        '''
        pos -> (x,y), the position of the widget\n
        size -> (w,h) the size of the textbox\n
        max_len -> maximum length of the text typed\n
        texture -> the background texture of the bar\n
        parent -> the parent widget of the bar\n
        enable_on_click -> whether the textbox is only enabled (and rendered) after it's been clicked on.\\
        letter_width -> a number determining the size of each letter (it has to be between 0 and 1)
        '''
        super().__init__(pos, size, texture=texture if texture is not None else self.DEFAULT_TEXTURE, parent=parent)
        self.content = ""
        self.text = self.font.render("", False, (255,255,255))
        self.max_len = max_len
        self.char_size = (int(self.size[0]/self.max_len*letter_width), int(self.size[1]*3/5))
        self.letter_width = letter_width
        self.active = False # whether the user is writing on the textbox
        self.enable_on_click = enable_on_click
        self.enabled = True

    def set_text(self, text) -> None:
        self.content = text
        text_size = (int(self.char_size[0]*len(self.content)), int(self.char_size[1]))
        self.text = pygame.transform.scale(self.font.render(self.content, False, (255,255,255)), text_size) # the text has to be re-rendered

    def on_click(self, mouse_pos):
        '''
            Returns true if the textbox was selected/deselected
        '''
        was_active = self.active
        self.active = super().is_on_element(mouse_pos)
        if self.enable_on_click:
            self.enabled = self.active
        return was_active != self.active

    def handle_event(self, event) -> None:
        '''
            Returns whether a new character was added to the content of the textbox
        '''
        if not self.active or not self.enabled:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == 8 and len(self.content) > 0: # delete key has been pressed
                self.set_text(self.content[:-1])
                return True
            elif len(self.content) < self.max_len and event.key not in (8,pygame.K_LSHIFT,pygame.K_RSHIFT,pygame.K_ESCAPE):
                keys = pygame.key.get_pressed()
                addition = chr(event.key)
                if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
                    addition = chr(event.key-32) # make the letter a capital
                self.set_text(self.content+addition) # add the newly typed letter into the text contained by the textbox
                return True
        return False

    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            pos = self.pos if self.parent is None else (self.parent.pos[0]+self.pos[0], self.parent.pos[1]+self.pos[1])
            surf.blit(self.texture, (pos[0], pos[1]))
            surf.blit(self.text, (pos[0]+int(self.size[0]/18), pos[1] + int(self.size[1]*1/4)))
            if time.time() % 1 > 0.5 and self.active:
                cursor_x_offset = int(self.size[0]*(len(self.content)+1)/self.max_len*self.letter_width)
                pygame.draw.rect(surf, (255,255,255), (pos[0]+cursor_x_offset, pos[1] + int(self.size[1]*1/4), self.char_size[0], self.char_size[1]))

class Button(UIElement):

    # textures is a list of textures that are drawn corresponding to the state
    # of the button, 0 -> normal, 1 -> hovered, 2 -> clicked
    def __init__(self, pos, size, textures=None, parent=None) -> None:
        '''
            pos -> position of the top-left corner of the gui element
            size -> width and height of the gui element (w,h)
            textures -> a list of three textures, the first is how the button looks by default,
            the second is the button when the user hovers over it with the mouse,
            and the third is the look of the button when it's actively being clicked
        '''
        super().__init__(pos, size, parent=parent)
        self.state = 0 # default state
        self.enabled = True
        self.textures = []
        # make sure the game doesn't crash if a button is created without any custom
        if textures is not None:
            for texture in textures:
                if isinstance(texture, str):
                    texture = load_texture(texture)
                self.textures.append(pygame.transform.scale(texture, size))
        else:
            self.textures = load_spritesheet("default_button.png", tile_w=64, tile_h=32, new_size=size)


    def on_click(self, mouse_pos) -> bool:
        '''
            Returns whether the button has been clicked
        '''
        if self.is_on_element(mouse_pos):
            self.state = 2 # switch to the clicked texture

    def on_click_release(self, mouse_pos, *args) -> bool:
        '''
            Returns whether the button was pressed before the click was released
        '''
        # if the button was clicked and the mouse is still on it
        if self.state == 2 and super().is_on_element(mouse_pos):
            self.state = 1 # return to the hovered texture
            return True
        return False

    def on_mouse_motion(self, mouse_pos) -> None:
        if super().is_on_element(mouse_pos) and self.state != 2:
            self.state = 1
        elif self.state != 0: # if the mouse isn't on the button
            self.state = 0
    
    def is_clicked(self) -> bool:
        return self.state == 2
    
    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            src = (0,0) if self.parent is None else self.parent.pos
            surf.blit(self.textures[self.state], (self.pos[0]+src[0], self.pos[1]+src[1]))

class Tickbox(UIElement):

    def __init__(self, pos, size, textures=None, parent=None) -> None:
        super().__init__(pos, size, parent=parent)
        self.ticked = False
        self.texture_state = 0 # texture state (0 -> unticked, 1 -> clicked (but click not yet released), 2 -> ticked)
        self.textures = []
        # make sure the game doesn't just crash if no custom texture is loaded
        if textures is not None:
            for texture in textures:
                if isinstance(texture, str):
                    texture = load_texture(texture)
                self.textures.append(pygame.transform.scale(texture, size))
        else:
            self.textures = load_spritesheet("tickbox.png", new_size=size)

    def _set_hovered(self):
        if len(self.textures) == 3:
            self.texture_state = 1 
        elif len(self.textures) == 4:
            self.texture_state = 1 if self.texture_state == 0 else 2

    def on_click(self, mouse_pos) -> None:
        if super().is_on_element(mouse_pos):
            self._set_hovered()

    def on_click_release(self, mouse_pos, *args) -> None:
        if super().is_on_element(mouse_pos):
            self.ticked = not self.ticked
            self.texture_state = int(self.ticked)*(len(self.textures)-1)
        
    def render(self, surf: pygame.Surface) -> None:
        src = (0,0) if self.parent is None else self.parent.pos
        surf.blit(self.textures[self.texture_state], (self.pos[0]+src[0], self.pos[1]+src[1]))

    def set_ticked(self, ticked: bool) -> None:
        self.ticked = ticked
        self.texture_state = 0

class AngleSelector(UIElement):
    DEFAULT_TEXTURE = load_texture("angle_setter.png")
    ARROW_TEXTURE = load_texture("angle_arrow.png")

    def __init__(self, pos, size, texture=None, parent=None, arrow_scale=0.6, continuous=True) -> None:
        super().__init__(pos, size, texture=texture if texture is not None else self.DEFAULT_TEXTURE, parent=parent)
        self.angle = 0 # in radians
        # size of the arrow scaled with the size of the widget
        self.arrow_size = adapt_ratio((10,22), (arrow_scale*self.size[0]/25, arrow_scale*self.size[1]/25))
        self.arrow_texture = pygame.transform.scale(self.ARROW_TEXTURE, self.arrow_size)
        self.center_pos = self.get_abs_pos((self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]//2))
        # the original rect of the image has its center in the exact middle of the widget
        self.arrow_rect = self.arrow_texture.get_rect(center=self.center_pos) 
        self.enabled = True
        self.continuous = continuous

    def set_angle(self, angle: float):
        self.angle = angle
        self.arrow_texture = pygame.transform.scale(self.ARROW_TEXTURE, self.arrow_size) # scale to the original size
        self.arrow_texture, _ = rotate_texture(self.arrow_texture, angle, self.center_pos) # rotate the image
        # update the rect to render it in the correct position
        self.arrow_rect = self.arrow_texture.get_rect(center=self.arrow_texture.get_rect(center=self.center_pos).center) 

    def on_click(self, mouse_pos):
        '''
            Returns whether the value of the angle was changed or not
        '''
        if self.is_on_element(mouse_pos):
            # y flipped because of pygame's coordinate system, where y increases going downwards
            self.set_angle(get_angle((mouse_pos[0]-self.arrow_rect.center[0], -mouse_pos[1]+self.arrow_rect.center[1]))) 
            return True
        return False

    def on_mouse_motion(self, mouse_pos):
        if self.continuous and pygame.mouse.get_pressed()[0]:
            return self.on_click(mouse_pos)

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        if self.enabled:
            surf.blit(self.arrow_texture, self.arrow_rect)

class TimeUI(UIElement):
    MAX_TIME_RATE = 2
    MIN_TIME_RATE = 0.25
    TIME_STEP = 0.25

    def __init__(self, w, h) -> None:
        super().__init__((0,0), (int(196*w/800),int(100*h/600)), "time_gui_background.png")
        self.days = 0
        self.ratio = (w/800.0, h/600.0)
        self.enabled = True
        self.pause_box = Tickbox(adapt_ratio((82,60), self.ratio),
                                    adapt_ratio((24,24), self.ratio),
                                    textures=load_spritesheet("time_toggle.png"),
                                    parent=self)
        self.speed_up_button = Button(adapt_ratio((131,60), self.ratio),
                                      adapt_ratio((24,24), self.ratio),
                                      textures=load_spritesheet("speedup_button.png", tile_w=32, tile_h=32),
                                      parent=self)
        self.slow_down_button = Button(adapt_ratio((33,60), self.ratio),
                                      adapt_ratio((24,24), self.ratio),
                                      textures=load_spritesheet("slowdown_button.png", tile_w=32, tile_h=32),
                                      parent=self)
        self.time_rate_bar = ProgressBar(adapt_ratio((5,32), self.ratio), 
                                        adapt_ratio((180,24), self.ratio), 
                                        min_val=0, val=4, max_val=8, 
                                        texture="progressbar.png", discrete=True, 
                                        fill_y_offset=int(2*self.ratio[1]), fill_y_size=int(21*self.ratio[1]),
                                        parent=self, fill_color=(115,115,115))

    def on_click(self, mouse_pos) -> None:
        self.pause_box.on_click(mouse_pos)
        self.speed_up_button.on_click(mouse_pos)
        self.slow_down_button.on_click(mouse_pos)
        if self.time_rate_bar.on_click(mouse_pos):
            pygame.event.post(pygame.event.Event(TIME_UPDATE_EVENT))

    def on_click_release(self, mouse_pos, *args) -> None:
        self.pause_box.on_click_release(mouse_pos)
        self.time_rate_bar.on_click_release(mouse_pos)
        if self.speed_up_button.on_click_release(mouse_pos) and self.time_rate_bar.val*self.TIME_STEP < self.MAX_TIME_RATE:
            self.time_rate_bar.val += 1
            # used in the rest of the program to actually update the values
            pygame.event.post(pygame.event.Event(TIME_UPDATE_EVENT))
        elif self.slow_down_button.on_click_release(mouse_pos) and self.time_rate_bar.val*self.TIME_STEP > self.MIN_TIME_RATE:
            self.time_rate_bar.val -= 1
            # used in the rest of the program to actually update the values
            pygame.event.post(pygame.event.Event(TIME_UPDATE_EVENT))

    def on_mouse_motion(self, mouse_pos) -> None:
        self.speed_up_button.on_mouse_motion(mouse_pos)
        self.slow_down_button.on_mouse_motion(mouse_pos)

    def _update_text(self):
        '''
            Updates the text showing the amount of time passed
        '''
        self.time_text = self.font.render(f"Giorni passati: {int(self.days)}", False, (255,255,255))
        self.time_text = pygame.transform.scale(self.time_text, adapt_ratio((182,19), self.ratio))

    def update(self, *args) -> None:
        self.days += self.get_time_rate()

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        self._update_text()
        surf.blit(self.time_text, adapt_ratio((5,10), self.ratio)) 

        self.pause_box.render(surf)
        self.speed_up_button.render(surf)
        self.slow_down_button.render(surf)
        self.time_rate_bar.render(surf)

    def is_time_enabled(self) -> bool:
        return self.pause_box.ticked

    def get_time_rate(self) -> float:
        return self.TIME_STEP*self.time_rate_bar.val

class PlanetUI(UIElement):
    MOON_MASS = 1.230312630186531e-2 # mass of the moon/mass of the earth
    MAX_THROW_VEL = 30 # maximum velocity at which an object can be thrown
    MIN_THROW_VEL = 0.4 # minimum velocity at which an object can be thrown
    MIN_CLICK_THROW_TIME = 0.3 # minimum amount of time (in seconds) for which an object has to be clicked in order to be thrown
    # minimum amount of time (in seconds) for which an object has to be clicked in order to change its velocity when it's dragged
    MIN_CLICK_CHANGE_VEL_TIME = 0.1 
    MAX_BODY_PATH_LEN = 500 # the maximum amount of positions rendered when drawing the path of a body

    def __init__(self, w, h) -> None:
        super().__init__((int(500*w/800),int(400*h/600)), (int(256*w/800),int(190*h/600)), "gui_bg_new.png")
        # the values were adjusted for this resolution, this way they can be scaled to any given resolution
        self.ratio = (w/800.0, h/600.0)
        self.mass_bar = ProgressBar(adapt_ratio((30, 37), self.ratio), 
                                    adapt_ratio((190, 22), self.ratio), 
                                    min_val=self.MOON_MASS, val=1, max_val=10**6, parent=self)
        self.mass_textbox = TextBox(adapt_ratio((100, 13), self.ratio), 
                                    adapt_ratio((125, 20), self.ratio),
                                    max_len=14, parent=self,
                                    enable_on_click=True, letter_width=0.9)
        self.radius_bar = ProgressBar(adapt_ratio((30,83), self.ratio), 
                                    adapt_ratio((190,22), self.ratio), 
                                    min_val=1, val=3, max_val=17, parent=self)
        self.name_textbox = TextBox(adapt_ratio((20,-30), self.ratio), 
                                    adapt_ratio((216, 40), self.ratio), 
                                    max_len=10, 
                                    parent=self, letter_width=0.75)
        self.vel_textbox = TextBox(adapt_ratio((117, 110), self.ratio),
                                    adapt_ratio((125,20), self.ratio),
                                    max_len=14, parent=self,
                                    enable_on_click=True, letter_width=0.9)
        self.orbit_tickbox = Tickbox(adapt_ratio((175,160), self.ratio), 
                                    adapt_ratio((18,18), self.ratio), parent=self)
        self.vangle_setter = AngleSelector((30,130), (25,25), parent=self) # velocity angle setter
        self.body = None
        self.body_path = []
        self.dragging = False # whether the selected body is being dragged
        self.click_start = 0

    def update_texts(self, force_update=False) -> None:
        '''
            Update the info text about the selected body.\n
            force_update -> whether to force the update of the text of the mass of the body, if it's false (as default)
            it might not be updated due to an optimization technique.
        '''
        self.vel_text = super().font.render(self.body.get_vel_str(), False, (255,255,255))
        # only update the text of the mass if it has been changed
        if self.mass_bar.enabled or 'mass_text' not in dir(self) or force_update: 
            self.mass_text = super().font.render(self.body.get_mass_str(), False, (255,255,255))

    def on_click(self, mouse_pos) -> None:
        self.name_textbox.on_click(mouse_pos)
        self.orbit_tickbox.on_click(mouse_pos)
        
        # the angle of the velocity has been changed
        if self.vangle_setter.on_click(mouse_pos):
            self.body.set_vel_angle(self.vangle_setter.angle)
        # if the mass' progress bar value was changed update it
        if self.mass_bar.on_click(mouse_pos):
            self.body.set_mass(self.mass_bar.val)
        # if the radius' progress bar value was changed update it
        if self.radius_bar.on_click(mouse_pos):
            self.body.radius = int(self.radius_bar.val)
        
        # if the velocity has been typed in apply the changes
        if self.vel_textbox.on_click(mouse_pos):
            self.body.set_vel_str(self.vel_textbox.content)
            self.vel_text = super().font.render(self.body.get_vel_str(), False, (255,255,255))
        # if the mass has been typed in apply the changes
        if self.mass_textbox.on_click(mouse_pos):
            self.body.set_mass_str(self.mass_textbox.content)
            self.mass_text = super().font.render(self.body.get_mass_str(), False, (255,255,255)) # UPDATE THE MASS' TEXT
        # make sure the UI keeps rendering it the click was outside its region but inside the name textbox's
        if self.name_textbox.active: 
            self.enabled = True
        if self.body is not None:
            if self.body.is_on_body(mouse_pos):
                self.dragging = True
                self.click_start = time.time()

    def handle_event(self, event) -> None:
        if self.name_textbox.handle_event(event):
            self.body.name = self.name_textbox.content
            print(self.body.name)
        self.mass_textbox.handle_event(event)
        self.vel_textbox.handle_event(event)
        '''
        if self.name_textbox.active and event.type == pygame.KEYDOWN: # a letter has been typed in the name field
            self.body.name = self.name_textbox.content
        '''

    def on_mouse_motion(self, mouse_pos) -> None:
        if self.dragging:
            self.body.set_pos(mouse_pos)
            if self.body.get_abs_vel() != 0 and time.time()-self.click_start > self.MIN_CLICK_CHANGE_VEL_TIME:
                self.body.set_vel((0,0))
            self.enabled = not self.is_on_element(mouse_pos)
        else:
            # if the value of the mass bar has been changed update the body's value
            if self.mass_bar.on_mouse_motion(mouse_pos):
                self.body.set_mass(self.mass_bar.val)
            # if the value of the radius bar has been changed update the body's value
            if self.radius_bar.on_mouse_motion(mouse_pos):
                self.body.radius = int(self.radius_bar.val)
            # the angle of the velocity has been changed
            if self.vangle_setter.on_mouse_motion(mouse_pos):
                self.body.set_vel_angle(self.vangle_setter.angle)

    def on_click_release(self, mouse_pos, *args) -> None:
        self.orbit_tickbox.on_click_release(mouse_pos)
        if self.dragging:
            self.dragging = False
            # looks dumb but this way I don't have to import numpy just for this one line
            if time.time() - self.click_start > self.MIN_CLICK_THROW_TIME:
                if self.MIN_THROW_VEL < (args[0][0]**2+args[0][1]**2)**(0.5) < self.MAX_THROW_VEL: 
                    self.body.set_vel(args[0]) # args[1] is the displacement of the mouse from the last frame

    def log_body(self, body: Body, mouse_pos=None) -> None:
        mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
        is_on_gui = super().is_on_element(mouse_pos)
        # if there is no body or the click was on the GUI just do nothing
        if body is None or is_on_gui:
            if body is None and not is_on_gui:
                self.enabled = False
            return
        
        self.enabled = True
        self.mass_bar.val = body.mass
        self.radius_bar.val = body.radius
        self.body = body
        self.update_texts(force_update=True) # re-render the velocity and mass text
        self.name_textbox.set_text(self.body.name)
        self.mass_textbox.set_text(self.body.get_mass_str()[:-3]) # the [:-3] part is to remove the "kg" text
        self.vel_textbox.set_text(self.body.get_vel_str()[:-7]) # the [:-7] part is to remove the " km/day" text
        self.orbit_tickbox.set_ticked(False)
        self.body_path = []

    def update(self) -> None:
        if self.orbit_tickbox.ticked:
            if len(self.body_path) > self.MAX_BODY_PATH_LEN:
                self.body_path = self.body_path[1:len(self.body_path)]
            self.body_path.append((int(self.body.pos[0]), int(self.body.pos[1])))

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        if self.enabled:
            self.update_texts()

            if self.orbit_tickbox.ticked:
                for pos in self.body_path:
                    pygame.draw.circle(surf, (255,255,255), pos, int(self.body.radius*3/4))

            self.mass_bar.render(surf)
            self.radius_bar.render(surf)
            surf.blit(self.vel_text, (self.pos[0]+int(117*self.ratio[0]), self.pos[1]+int(115*self.ratio[1]))) # velocity text
            surf.blit(self.mass_text, (self.pos[0]+int(100*self.ratio[0]), self.pos[1]+int(17*self.ratio[1])))

            self.body.render_velocity(surf)
            self.name_textbox.render(surf)
            self.orbit_tickbox.render(surf)    
            self.mass_textbox.render(surf)
            self.vel_textbox.render(surf)
            self.vangle_setter.render(surf)
