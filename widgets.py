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
                widget.handle_event(event, mouse_pos)

    def update(self):
        for widget in self.widgets:
            widget.update()

    def render(self, surf):
        if not self.enabled:
            return

        UIElement.popup_msg.render(surf)
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

    def is_on_ui(self, pos: tuple) -> bool:
        '''
            Returns whether the given (x,y) position is on one of the widgets in the ui
        '''
        for widget in self.widgets:
            if widget.is_on_element(pos) and widget.enabled:
                return True
        return False

class UIElement:
    font = None
    popup_msg = None # pop up text

    # make a list of children GUIelements, so that their position and whether they
    # are enabled or not depends on the parameters of their parent 
    def __init__(self, pos, size, texture=None, parent=None, enabled=True) -> None:
        '''
            pos -> position of the top-left corner of the gui element\n
            size -> width and height of the gui element (w,h)\n
            texture -> pygame image of the texture to be used\n
        '''
        self.pos = pos
        self.enabled = enabled
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
            self.texture = pygame.transform.smoothscale(self.texture, self.size)
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
            # do not account for the attributes every element has
            if attrib == 'parent' or attrib == 'popup_msg':
                continue
            if isinstance(self.__getattribute__(attrib), UIElement):
                widgets.append(self.__getattribute__(attrib))
        return widgets

    @staticmethod
    def init(W=800, H=600.0) -> None:
        '''
            The function initializes the font and the pop-up messages of the UI\n
            W, H --> respectively the width and the height of the screen
        '''
   #     font_location = pygame.font.match_font('arial')
        UIElement.font = pygame.font.SysFont(None, int(23*(W+H)/1400.0))
        pop_up_size = adapt_ratio((128,32), (W/800.0, H/600.0))
        UIElement.popup_msg = PopUpText(((W-pop_up_size[0])//2, int(100*H/600)), pop_up_size)

class ProgressBar(UIElement):
    BACKGROUND_COLOR = (255,128,0)
    PROGRESS_COLOR = (255,255,0)
    BORDER_COLOR = (255,255,255)

    def __init__(self, pos, size, min_val=0, val=50, max_val=100, texture=None, parent=None, 
                interactable=True, discrete=False, fill_y_offset=0, fill_y_size=0, fill_color=None,
                background_color=None, border_color=None, border_size=0, continuous=True) -> None:
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
        super().__init__(pos, size, texture=texture, parent=parent, enabled=True)
        self.min_val = min_val
        self.max_val = max_val
        self.val = val
        self.interactable = interactable
        self.discrete = discrete
        self.fill_y_size = fill_y_size if fill_y_size != 0 else self.size[1]-2*border_size
        self.fill_y_offset = fill_y_offset+border_size
        self.fill_color = fill_color if fill_color is not None else self.PROGRESS_COLOR
        self.background_color = background_color if background_color is not None else self.BACKGROUND_COLOR
        self.border_color = border_color if border_color is not None else self.BORDER_COLOR
        self.border_size = border_size
        self.continuous = continuous

    def on_click(self, mouse_pos) -> bool:
        '''
            Returns true if the value of the progress bar has been changed
        '''
        if not self.enabled:
            return

        if self.is_on_element(mouse_pos) and self.interactable:
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
        if not self.enabled:
            return

        if self.continuous and pygame.mouse.get_pressed()[0]:
            return self.on_click(mouse_pos) 
    
    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False)
        self.fill_y_size = int(self.fill_y_size*hnew/hold)
        self.fill_y_offset = int(self.fill_y_offset*hnew/hold)

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return
    
        prog_w = int((self.val-self.min_val)/(self.max_val-self.min_val)*self.size[0]) # width of the progress color (in pixels)
        src = (0,0) if self.parent is None else self.parent.pos
        if self.texture is None:
            rect = (src[0]+self.pos[0], src[1]+self.pos[1], self.size[0], self.size[1])
            pygame.draw.rect(surf, self.background_color, rect)
            if self.border_size != 0:
                pygame.draw.rect(surf, self.border_color, rect, self.border_size)
        pygame.draw.rect(surf, self.fill_color, (src[0]+self.pos[0]+self.border_size,  # x
                                                src[1]+self.pos[1]+self.fill_y_offset,  # y
                                                prog_w-self.border_size, self.fill_y_size)) # width and height
        # draws the background image if it's present
        if self.texture is not None:
            surf.blit(self.texture, self.get_abs_pos(self.pos))

class TextBox(UIElement):
    DEFAULT_TEXTURE = load_texture('textbox.png')
    # characters that can't be typed in
    FORBIDDEN_CHARS = (8, pygame.K_ESCAPE, pygame.K_RETURN)
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
        super().__init__(pos, size, texture=texture if texture is not None else self.DEFAULT_TEXTURE, parent=parent, enabled=not enable_on_click)
        self.content = ""
        self.text = self.font.render("", False, (255,255,255))
        self.max_len = max(1, max_len)
        self.char_size = (int(self.size[0]/self.max_len*letter_width), int(self.size[1]*3/5))
        self.letter_width = letter_width
        self.active = False # whether the user is writing on the textbox
        self.enable_on_click = enable_on_click
        self.numeric = numeric
        self.selected_char = 1

    def set_max_len(self, max_len: int) -> None:
        '''
            Set the maximum length of the text rendered
        '''
        self.max_len = max_len
        self.char_size = (int(self.size[0]/self.max_len*self.letter_width), int(self.size[1]*3/5))

    def set_text(self, text, disable=False) -> None:
        self.content = text
        self.selected_char = clamp(self.selected_char, 0, len(text))
        if len(text) > self.max_len:
            self.set_max_len(len(text))
        text_size = (int(self.char_size[0]*len(self.content)), int(self.char_size[1]))
        self.text = pygame.transform.scale(self.font.render(self.content, False, (255,255,255)), text_size) # the text has to be re-rendered
        if disable:
            self.active = False

    def is_valid(self, char: int) -> bool:
        '''
            Returns whether the character (as its event.unicode and event.key representation) can be typed into the textbox or not
        '''
        if len(char) == 0:
            return False
        if self.numeric:
            if ord('0') <= ord(char) <= ord('9') or char in self.NUMERICAL_EXCEPTIONS:
                return True
            return False
        return True

    def on_click(self, mouse_pos):
        '''
            Returns true if the textbox was selected/deselected
        '''
        was_active = self.active
        self.active = super().is_on_element(mouse_pos)
        if self.active:
            self.selected_char = max(1, len(self.content))
        if self.enable_on_click:
            self.enabled = self.active
        return was_active != self.active

    def handle_event(self, event) -> bool:
        '''
            Returns whether a new character was added to the content of the textbox
        '''
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            # right arrow is 275, left arrow is 276
            if event.key == 275 or event.key == 276:
                offset = 1 if event.key == 275 else -1
                self.selected_char = clamp(self.selected_char+offset, 0, len(self.content))
            elif event.key == 8: # delete key has been pressed
                if len(self.content) < 0:
                    return
                self.selected_char = clamp(self.selected_char-1, 0, len(self.content))
                self.set_text(self.content[:self.selected_char]+self.content[self.selected_char+1:])
                return True
            elif len(self.content) < self.max_len:
                # if the textbox is numeric and something that isn't a number has been typed in
                if not self.is_valid(event.unicode):
                    return False
                # add the newly typed letter into the text contained by the textbox
                self.set_text(self.content[:self.selected_char]+event.unicode+self.content[self.selected_char:]) 
                self.selected_char = clamp(self.selected_char+1, 1, len(self.content))
                return True
        return False

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False) # size, pos, texture
        # calculate new char size, letter_width is a dimensionless coefficient, no need to change it
        self.char_size = (int(self.size[0]/self.max_len*self.letter_width), int(self.size[1]*3/5)) 
        self.set_text(self.content) # re-render the text with the right size

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return
        pos = self.pos if self.parent is None else (self.parent.pos[0]+self.pos[0], self.parent.pos[1]+self.pos[1])
        surf.blit(self.texture, (pos[0], pos[1]))
        surf.blit(self.text, (pos[0]+int(self.size[0]/18), pos[1] + int(self.size[1]*1/4)))
        if time.time() % 1 > 0.5 and self.active:
            cursor_x_offset = min(int(self.char_size[0]*self.selected_char), self.size[0]-self.char_size[1])+self.char_size[0]//2
            pygame.draw.rect(surf, (255,255,255), (pos[0]+cursor_x_offset, pos[1] + int(self.size[1]*1/5), self.char_size[0]//2, self.char_size[1]))

class Button(UIElement):
    BUTTON_MASK_TEXTURE = load_spritesheet("button_mask.png", tile_w=1, tile_h=1)

    # textures is a list of textures that are drawn corresponding to the state
    # of the button, 0 -> normal, 1 -> hovered, 2 -> clicked
    def __init__(self, pos, size, textures=None, parent=None) -> None:
        '''
            pos -> position of the top-left corner of the gui element\n
            size -> width and height of the gui element (w,h)\n
            textures -> a list of three textures, the first is how the button looks by default,
            the second is the button when the user hovers over it with the mouse,
            and the third is the look of the button when it's actively being clicked\n
            parent -> the parent widget of the button\n
            text -> the text rendered on the button (if text is left as None no text is rendered)
        '''
        super().__init__(pos, size, parent=parent, enabled=True)
        self.state = 0 # default state
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
        if not self.enabled:
            return

        if self.is_on_element(mouse_pos):
            self.state = 2 # switch to the clicked texture

    def on_click_release(self, mouse_pos, *args) -> bool:
        '''
            Returns whether the button was pressed before the click was released
        '''
        if not self.enabled:
            return

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
        if not self.enabled:
            return

        src = (0,0) if self.parent is None else self.parent.pos
        surf.blit(self.textures[self.state], (self.pos[0]+src[0], self.pos[1]+src[1]))

class Tickbox(UIElement):

    def __init__(self, pos, size, textures=None, parent=None, ticked=False) -> None:
        super().__init__(pos, size, parent=parent, enabled=True)
        self.ticked = ticked
        self.texture_state = 2*int(ticked) # texture state (0 -> unticked, 1 -> clicked (but click not yet released), 2 -> ticked)
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
        if not self.enabled:
            return
        src = (0,0) if self.parent is None else self.parent.pos
        surf.blit(self.textures[self.texture_state], (self.pos[0]+src[0], self.pos[1]+src[1]))

    def set_ticked(self, ticked: bool) -> None:
        self.ticked = ticked
        self.texture_state = 0

class AngleSelector(UIElement):
    DEFAULT_TEXTURE = load_texture("angle_setter.png")
    ARROW_TEXTURE = load_texture("angle_arrow.png")

    def __init__(self, pos, size, texture=None, parent=None, arrow_scale=0.6, continuous=True) -> None:
        super().__init__(pos, size, texture=texture if texture is not None else self.DEFAULT_TEXTURE, parent=parent, enabled=True)
        self.angle = 0 # in radians
        # size of the arrow scaled with the size of the widget
        self.arrow_scale = arrow_scale
        self.arrow_size = adapt_ratio((10,22), (arrow_scale*self.size[0]/25, arrow_scale*self.size[1]/25))
        self.arrow_texture = pygame.transform.scale(self.ARROW_TEXTURE, self.arrow_size)
        self.center_pos = self.get_abs_pos((self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]//2))
        # the original rect of the image has its center in the exact middle of the widget
        self.arrow_rect = self.arrow_texture.get_rect(center=self.center_pos) 
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
        '''
            pos, size --> position and size of the widget in pixels\n
            max_len --> maximum length of the text written\n
            texture, parent --> the background texture and the parent of the UIElement\n
            letter_width --> amount of spacing between each letter\n
            numeric --> whether the text only allows numeric characters (also includes '.', '*' and so on)\n
            dims --> the width and height of the window (in pixels), used to scale the distance between the letters\n
            conversion_func --> function that takes two parameters x,y, if y is true the text is beggining to be modified
            \t\t\t\tand the function should return how the displayed text is converted to the one in the textbox, if y is false the
            opposite process is applied.
        '''
        super().__init__(pos, size, texture=None, parent=parent, enabled=True)
        self.textbox = TextBox((pos[0]-int(5*dims[0]/800.0), pos[1]-int(5*dims[1]/600.0)), 
                        size, max_len, texture, parent, True, letter_width, numeric)
        self.text = ""
        self._update_text()
        # the function that converts (text from textbox) -> base text if the second parameter is False
        # and (base text -> Textbox text) if the second parameter is True
        self.conversion_func = conversion_func if conversion_func is not None else lambda x,y: x

    def set_max_len(self, max_len: int) -> None:
        ''' Sets the maximum length of the text '''
        self.textbox.set_max_len(max_len)

    def set_text(self, text: str, update_textbox=False, disable=False) -> None:
        self.text = text
        self._update_text()
        if disable:
            self.textbox.active = False
            self.textbox.enabled = False
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

class TextButton(UIElement):

    def __init__(self, pos, size, text, texture=None, parent=None, max_len=None) -> None:
        '''
            A button, but with a text rendered on top of it
        '''
        super().__init__(pos, size, texture=None, parent=parent, enabled=True)
        self.textbox = TextBox(self.pos, self.size, max_len=len(text) if max_len is None else max_len, 
                                texture=texture, parent=self.parent, letter_width=0.9)
        self.textbox.set_text(text)
        self.button = Button(self.pos, self.size, textures=Button.BUTTON_MASK_TEXTURE, parent=self.parent)

    def on_click(self, mouse_pos):
        return self.button.on_click(mouse_pos)
    
    def on_mouse_motion(self, mouse_pos) -> None:
        return self.button.on_mouse_motion(mouse_pos)
    
    def on_click_release(self, mouse_pos, *args):
        return self.button.on_click_release(mouse_pos)

    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            self.textbox.render(surf)
            self.button.render(surf)

class DropDownList(UIElement):
    DEFAULT_ENTRY_TEXTURE = load_texture("dropdown_entry.png")
    
    def __init__(self, pos, size, entries=[' '], parent=None, dims=(800.0,600.0), initial_element=None) -> None:
        '''
            dims -> the size of the window (or of the surface the widget is being rendered on)
        '''
        super().__init__(pos, size, None, parent=parent)
        max_text_len = max([len(entry) for entry in entries]) # length of longest text that will be rendered
        self.main_textbox = TextBox(self.pos, self.size, max_text_len+2, letter_width=0.8, parent=parent) # the +2 is so the text doesn't override the button
        button_size = adapt_ratio((30,16), (dims[0]/800.0, dims[1]/600.0))
        # margin of the dropdown button from the left-top most corner
        margin_offset = adapt_ratio((9, 7), (self.size[0]/196, self.size[1]/25)) # absolute margin of the 
        self.dropdown_button = Button((self.pos[0]+self.size[0]-button_size[0]-margin_offset[0], self.pos[1]+margin_offset[1]),
                                        button_size,
                                        textures=load_spritesheet("dropdown_button.png", tile_w=30, tile_h=16),
                                        parent=parent)
        self.opened = False # whether the list is open
        self.set_entries(entries, initial_element)

    def set_selected(self, selected_entry_idx: int) -> None:
        ''' Sets the selection of the drop-down list to the one at the given index '''
        self.selected_entry_idx = selected_entry_idx
        # make sure to put an empty text if the index isn't valid
        new_text = "" if not (0 <= selected_entry_idx < len(self.entries)) else self.entries[selected_entry_idx]
        self.main_textbox.set_text(new_text)

    def set_entries(self, entries=[], initial_element=None) -> None:
        self.entries_buttons = []
        self.entries = entries
        max_text_len = max([len(entry) for entry in entries])
        self.main_textbox = TextBox(self.pos, self.size, max_text_len+2, letter_width=0.8, parent=self.parent)
        if initial_element is None or initial_element not in self.entries:
            self.set_selected(0)
        else:
            self.set_selected(self.entries.index(initial_element))

        # 3/4 of the width of this widget (or maybe 4/5), and as a height the same as this widget's
        for entry_idx in range(len(entries)):
            choice_box_size = (int(self.size[0]*4/5), self.size[1])
            choice_box_pos = (self.pos[0]+self.size[0]//10, self.pos[1]+self.size[1]*(entry_idx+1))
            entry_button = TextButton(choice_box_pos, choice_box_size, entries[entry_idx], 
                                        parent=self.parent, max_len=max_text_len)
            entry_button.enabled = self.opened
            self.entries_buttons.append(entry_button)

    def remove_entry(self, entry: str) -> None:
        ''' Removes the entry from the dropdown list, if the entry isn't in the list the return value is -1 '''
        try:
            entry_idx = self.entries.index(entry)
        except ValueError:
            return -1
        # shift up the position of every choice after the one being removed 
        for succ_entry in range(entry_idx, len(self.entries)):
            self.entries_buttons[succ_entry].pos = (self.pos[0]+self.size[0]//10, self.pos[1]+self.size[1]*succ_entry)
        self.entries_buttons.pop(entry_idx)
        self.entries.pop(entry_idx)
        if entry_idx == self.selected_entry_idx:
            self.set_selected(clamp(entry_idx-1, 0, len(self.entries)-1))

    def add_entry(self, entry: str) -> None:
        ''' Adds an entry to the drop down list '''

    def set_opened(self, opened) -> None:
        self.opened = opened
        for i in range(len(self.entries)):
            self.entries_buttons[i].enabled = opened

    def is_on_element(self, mouse_pos) -> bool:
        if super().is_on_element(mouse_pos):
            return True
        if self.opened:
            for button in self.entries_buttons:
                if button.is_on_element(mouse_pos):
                    return True
        return False

    def on_click(self, mouse_pos):
        ''' Returns whether the click was on the widget '''
        if not self.is_on_element(mouse_pos):
            self.set_opened(False)
            return False

        self.dropdown_button.on_click(mouse_pos)
        for entry_button in self.entries_buttons:
            entry_button.on_click(mouse_pos)
        return True

    def on_mouse_motion(self, mouse_pos) -> None:
        self.dropdown_button.on_mouse_motion(mouse_pos)
        for entry_button in self.entries_buttons:
            entry_button.on_mouse_motion(mouse_pos)

    def on_click_release(self, mouse_pos, *args):
        ''' Returns whether an option was chosen '''
        if self.dropdown_button.on_click_release(mouse_pos):
            self.set_opened(not self.opened)
        for entry_idx in range(len(self.entries)):
            if self.entries_buttons[entry_idx].on_click_release(mouse_pos):
                self.set_selected(entry_idx)
                self.set_opened(False)
                return True
        return False

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=True)
        for entry_idx in range(len(self.entries)):
            self.entries_buttons[entry_idx].on_window_resize(wold, hold, wnew, hnew)

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return

        self.main_textbox.render(surf)
        self.dropdown_button.render(surf)

        for entry in range(len(self.entries)):
            self.entries_buttons[entry].render(surf)

    def get_selected(self) -> str:
        return self.entries[self.selected_entry_idx]

class PopUpText(UIElement):

    def __init__(self, pos, size, text="", last_time=1, fade_time=0.2) -> None:
        '''
            pos -> (x,y) position on the screen\n
            size -> (width, height) size of the pop-up in pixels\n
            text -> the text rendered\n 
            last_time -> the amount of time (in seconds) that the pop up lasts\n
            fade_time -> amount of time to fade in and fade out
        '''
        super().__init__(pos, size, texture=None, enabled=False)
        self.textbox = TextBox((0,0), size, max_len=len(text), letter_width=0.95)
        self.textbox.set_text(text)
        self.last_time = last_time
        self.fade_time = fade_time
        # surface on which the textbox is rendered, this is done to modify its opacity
        self.render_surf = pygame.Surface(size, pygame.SRCALPHA).convert()

    def start(self) -> None:
        self.start_time = time.time()
        self.enabled = True
        self.textbox.render(self.render_surf)

    def cast(self, text: str, last_time: float, fade_time=0.2, pos=None, size=None):
        ''' Casts a pop up message on the screen '''
        self.last_time = last_time
        self.fade_time = fade_time
        self.textbox.set_text(text)
        self.textbox.set_max_len(len(text))
        self.pos = self.pos if pos is None else pos
        self.size = self.size if size is None else size
        self.start()

    def on_click(self, *args):
        pass

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return
        elapsed = time.time()-self.start_time
        if elapsed <= self.fade_time: # FADE IN
            opacity = int(elapsed/self.fade_time*255)
            self.render_surf.set_alpha(opacity)
        elif elapsed >= self.last_time-self.fade_time: # FADE OUT
            since_fade_out = elapsed-(self.last_time-self.fade_time)
            opacity = 255-int(since_fade_out/self.fade_time*255)
            self.render_surf.set_alpha(opacity)
        surf.blit(self.render_surf, self.pos)
        if elapsed >= self.last_time:
            self.enabled = False