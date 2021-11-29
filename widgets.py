import pygame
import time
from utils import adapt_ratio, load_texture, clamp, load_spritesheet, rotate_texture, get_angle

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

    def on_window_resize(self, wold, hold, wnew, hnew):
        for widget in self.widgets:
            widget.on_window_resize(wold, hold, wnew, hnew)

    def add_widget(self, widget) -> None:
        self.widgets.append(widget)

    def get_by_type(self, _type: type):
        '''
            Returns the first occurrence of the widget of the given type (_type),
            if no widget of type _type is found then None is returned instead.\n
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
        abs_pos_off = (0,0) if self.parent is None else self.parent.pos # absolute position offset
        if abs_pos_off[0]+self.pos[0] < mouse_pos[0] < abs_pos_off[0]+self.pos[0] + self.size[0]: # x intersection
            if abs_pos_off[1]+self.pos[1] < mouse_pos[1] < abs_pos_off[1]+self.pos[1] + self.size[1]: # y intersection
                return True
        return False

    def on_mouse_motion(self, *args) -> None: pass
    def on_click_release(self, *args): pass
    def handle_event(self, *args) -> None: pass
    def update(self) -> None: pass
    def on_window_resize(self, wold, hold, wnew, hnew, resize_widgets=True) -> None:
        '''
            wold and hold are respectively the old width and height of the window,\n
            whilst wnew and hnew are the new ones (after it has been resized).\n
            ignored is a subwidget that is ignored when updating every subwidget, it's important because
            if a widget calls super().on_window_resize() with resize_widgets=True this will call that
            subwidget's on_window_resize() function resulting in an endless recursion
        '''
        self.size = adapt_ratio(self.size, (wnew/wold, hnew/hold))
        self.pos = adapt_ratio(self.pos, (wnew/wold, hnew/hold))
        if self.texture is not None: # rescale the texture
            self.texture = pygame.transform.scale(self.texture, self.size)
        # automatically call the method on every sub component if it wasn't specifically requested not to
        if resize_widgets: 
            for widget in self.get_child_widgets():
                widget.on_window_resize(wold, hold, wnew, hnew)

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

    def get_child_widgets(self) -> None:
        widgets = []
        for attrib in dir(self):
            if attrib == 'parent':
                continue
            if isinstance(self.__getattribute__(attrib), UIElement):
                widgets.append(self.__getattribute__(attrib))
        return widgets

    @staticmethod
    def init_font(W=800) -> None:
        '''
            W -> the width of the screen, the font is set to assume the screen ratio is 4:3
        '''
   #     font_location = pygame.font.match_font('arial')
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
    
    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False)
        self.fill_y_size = int(self.fill_y_size*hnew/hold)
        self.fill_y_offset = int(self.fill_y_offset*hnew/hold)

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
    # characters that can't be typed in
    FORBIDDEN_CHARS = (8,pygame.K_LSHIFT,pygame.K_RSHIFT,pygame.K_ESCAPE, pygame.K_RETURN)
    # characters that can be typed in numeric mode even if they aren't numbers
    NUMERICAL_EXCEPTIONS = ('-','.','^','*','/','+') 

    def __init__(self, pos, size, max_len=9, texture=None, parent=None, enable_on_click=False, letter_width=0.5,
                    numeric=False) -> None:
        '''
        pos -> (x,y), the position of the widget\n
        size -> (w,h) the size of the textbox\n
        max_len -> maximum length of the text typed\n
        texture -> the background texture of the bar\n
        parent -> the parent widget of the bar\n
        enable_on_click -> whether the textbox is only enabled (and rendered) after it's been clicked on.\\
        letter_width -> a number determining the size of each letter (it has to be between 0 and 1)\n
        numeric -> whether the textbox only allows numeric values (digits 0.9 including - and .)
        '''
        super().__init__(pos, size, texture=texture if texture is not None else self.DEFAULT_TEXTURE, parent=parent)
        self.content = ""
        self.text = self.font.render("", False, (255,255,255))
        self.max_len = max_len
        self.char_size = (int(self.size[0]/self.max_len*letter_width), int(self.size[1]*3/5))
        self.letter_width = letter_width
        self.active = False # whether the user is writing on the textbox
        self.enable_on_click = enable_on_click
        self.numeric = numeric
        self.enabled = not enable_on_click

    def set_text(self, text) -> None:
        self.content = text
        text_size = (int(self.char_size[0]*len(self.content)), int(self.char_size[1]))
        self.text = pygame.transform.scale(self.font.render(self.content, False, (255,255,255)), text_size) # the text has to be re-rendered

    def is_valid(self, char: int) -> bool:
        '''
            Returns whether the character (as its event.key representation) can be typed into the textbox
        '''
        if char in self.FORBIDDEN_CHARS:
            return False
        if self.numeric:
            if ord('0') <= char <= ord('9') or chr(char) in self.NUMERICAL_EXCEPTIONS:
                return True
            return False
        return True

    def on_click(self, mouse_pos):
        '''
            Returns true if the textbox was selected/deselected
        '''
        was_active = self.active
        self.active = super().is_on_element(mouse_pos)
        if self.enable_on_click:
            self.enabled = self.active
        return was_active != self.active

    def handle_event(self, event) -> bool:
        '''
            Returns whether a new character was added to the content of the textbox
        '''
        if not self.active or not self.enabled:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == 8 and len(self.content) > 0: # delete key has been pressed
                self.set_text(self.content[:-1])
                return True
            elif len(self.content) < self.max_len:
                # if the textbox is numeric and something that isn't a number has been typed in
                if not self.is_valid(event.key):
                    return False
                keys = pygame.key.get_pressed()
                addition = chr(event.key)
                if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
                    addition = chr(event.key-32) # make the letter a capital
                self.set_text(self.content+addition) # add the newly typed letter into the text contained by the textbox
                return True
        return False

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False) # size, pos, texture
        # calculate new char size, letter_width is a dimensionless coefficient, no need to change it
        self.char_size = (int(self.size[0]/self.max_len*self.letter_width), int(self.size[1]*3/5)) 
        self.set_text(self.content) # re-render the text with the right size

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
    
    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False) # size, pos
        for tex_idx in range(len(self.textures)): # textures
            self.textures[tex_idx] = pygame.transform.scale(self.textures[tex_idx], self.size)
    
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

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False) # size, pos
        for tex_idx in range(len(self.textures)): # textures
            self.textures[tex_idx] = pygame.transform.scale(self.textures[tex_idx], self.size)

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
        self.arrow_scale = arrow_scale
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
            self.set_angle(get_angle((mouse_pos[0]-self.arrow_rect.center[0], mouse_pos[1]-self.arrow_rect.center[1]))) 
            return True
        return False

    def on_mouse_motion(self, mouse_pos):
        if self.continuous and pygame.mouse.get_pressed()[0]:
            return self.on_click(mouse_pos)

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False)
        # calculate new arrow size, scale the default texture to the new size, get the new position of the center of the widget
        self.arrow_size = adapt_ratio((10,22), (self.arrow_scale*self.size[0]/25, self.arrow_scale*self.size[1]/25))
        self.center_pos = self.get_abs_pos((self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]//2))
        self.set_angle(self.angle) # handles the scaling and rotation of the texture using the data calculated above

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        if self.enabled:
            surf.blit(self.arrow_texture, self.arrow_rect)

class ModifiableText(UIElement):

    # dims is the size of the screen, it's so the textbox can be moved up a little 
    # so its  text matches with the one rendered when the textbox is disabled
    def __init__(self, pos, size, max_len=9, texture=None, parent=None, letter_width=0.5, numeric=False, dims=(800.0,600.0),
                conversion_func=None) -> None:
        super().__init__(pos, size, texture=None, parent=parent)
        self.textbox = TextBox((pos[0]-int(5*dims[0]/800.0), pos[1]-int(5*dims[1]/600.0)), 
                        size, max_len, texture, parent, True, letter_width, numeric)
        self.text = ""
        self._update_text()
        self.enabled = True
        # the function that converts (text from textbox) -> base text if the second parameter is False
        # and (base text -> Textbox text) if the second parameter is True
        self.conversion_func = conversion_func if conversion_func is not None else lambda x,y: x

    def set_text(self, text: str, update_textbox=False) -> None:
        self.text = text
        self._update_text()
        if update_textbox:
            self.textbox.set_text(text)

    def _update_text(self) -> None:
        self.text_surf = super().font.render(self.text, False, (255,255,255))
    
    def on_click(self, mouse_pos):
        '''
            Returns whether the textbox was deactivated (meaning a value was passed as input)
        '''
        if self.textbox.on_click(mouse_pos):
            # if the textbox was disabled 
            if not self.textbox.enabled and len(self.textbox.content) != 0:
                self.text = self.conversion_func(self.textbox.content, False)
                self._update_text()
                return True
            else: # the textbox was enabled
                self.textbox.set_text(self.conversion_func(self.text, True))
        return False

    def handle_event(self, event) -> None:
        self.textbox.handle_event(event)

    def render(self, surf: pygame.Surface) -> None:
        if not self.textbox.enabled:
            surf.blit(self.text_surf, self.get_abs_pos())
        self.textbox.render(surf)