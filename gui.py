from animations import Animation
from body import Body
from widgets import *
from utils import get_average, get_mg_order, load_spritesheet, adapt_ratio, get_angle, aconvert, get_available_resolutions, get_saves, del_save, parseNum

TIME_UPDATE_EVENT = pygame.USEREVENT+1
GRAPHICS_UPDATE_EVENT = pygame.USEREVENT+2 # updates in brightness or in whether the grav field is rendered
SPACE_SAVE_EVENT = pygame.USEREVENT+3
SPACE_LOAD_EVENT = pygame.USEREVENT+4
BODY_ADD_EVENT = pygame.USEREVENT+5
BODY_REMOVE_EVENT = pygame.USEREVENT+6
BODIES_SELECT_EVENT = pygame.USEREVENT+7


class TimeUI(UIElement):
    MAX_TIME_RATE = 2
    MIN_TIME_RATE = 0.25
    TIME_STEP = 0.25

    def __init__(self, w, h) -> None:
        super().__init__((0,0), (int(196*w/800),int(100*h/600)), "time_gui_background.png", enabled=True)
        self.days = 0
        self.ratio = (w/800.0, h/600.0)
        self._update_text()
        self.__init_widgets(w, h)

    def __init_widgets(self, w, h) -> None:
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
        if not self.is_on_element(mouse_pos):
            return

        self.pause_box.on_click(mouse_pos)
        self.speed_up_button.on_click(mouse_pos)
        self.slow_down_button.on_click(mouse_pos)
        if self.time_rate_bar.on_click(mouse_pos):
            pygame.event.post(pygame.event.Event(TIME_UPDATE_EVENT))

    def on_click_release(self, mouse_pos, *args) -> None:
        if not self.is_on_element(mouse_pos):
            return

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
        if not self.is_on_element(mouse_pos):
            return
        self.speed_up_button.on_mouse_motion(mouse_pos)
        self.slow_down_button.on_mouse_motion(mouse_pos)

    def _update_text(self):
        '''
            Updates the text showing the amount of days passed since the beginning
        '''
        self.time_text = self.font.render(f"Days passed: {int(self.days)}", False, (255,255,255))
        self.time_text = pygame.transform.scale(self.time_text, adapt_ratio((182,19), self.ratio))

    def update(self) -> None:
        # only update the text showing how many days passed if 
        if int(self.days+self.get_time_rate()) > int(self.days):
            self._update_text()
        self.days += self.get_time_rate()

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return

        super().render(surf)
        surf.blit(self.time_text, adapt_ratio((5,10), self.ratio)) 

        self.pause_box.render(surf)
        self.speed_up_button.render(surf)
        self.slow_down_button.render(surf)
        self.time_rate_bar.render(surf)

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=True)
        self.ratio = (wnew/800.0, hnew/600.0)
        self._update_text()

    def is_time_enabled(self) -> bool:
        return self.pause_box.ticked

    def get_time_rate(self) -> float:
        return self.TIME_STEP*self.time_rate_bar.val

    def set_time_passed(self, days: int) -> None:
        self.days = days
        self._update_text()

class PlanetUI(UIElement):
    MOON_MASS = 1.230312630186531e-2 # mass of the moon/mass of the earth
    MAX_THROW_VEL = 30 # maximum velocity at which an object can be thrown
    MIN_THROW_VEL = 0.4 # minimum velocity at which an object can be thrown
    MIN_CLICK_THROW_TIME = 0.3 # minimum amount of time (in seconds) for which an object has to be clicked in order to be thrown
    # minimum amount of time (in seconds) for which an object has to be clicked in order to change its velocity when it's dragged
    MIN_CLICK_CHANGE_VEL_TIME = 0.1 
    MAX_BODY_PATH_LEN = 500 # the maximum amount of positions rendered when drawing the path of a body

    def __init__(self, w, h) -> None:
        super().__init__((int(530*w/800),int(375*h/600)), (int(256*w/800),int(215*h/600)), "gui_background.png", enabled=False)
        # the values were adjusted for this resolution, this way they can be scaled to any given resolution
        self.ratio = (w/800.0, h/600.0)
        self.__init_widgets(w,h)
        # velocity angle setter
        self.body = None
        self.body_path = []
        self.dragging = False # whether the selected body is being dragged
        self.click_start = 0

    def __init_widgets(self, w, h) -> None:
        self.xpos_text = ModifiableText(adapt_ratio((155, 18), self.ratio), adapt_ratio((30,22),self.ratio),
                            max_len=get_mg_order(w), parent=self, letter_width=0.9, numeric=True, 
                            dims=(w,h), conversion_func=lambda x,y: x[1:-1] if y else '('+str(int(float(x)))+',')
        self.ypos_text = ModifiableText(adapt_ratio((188,18), self.ratio), adapt_ratio((30,22),self.ratio),
                            max_len=get_mg_order(h), parent=self, letter_width=0.9, numeric=True,
                            dims=(w,h), conversion_func=lambda x,y: x[1:-1] if y else ' '+str(int(float(x)))+')')
        self.mass_bar = ProgressBar(adapt_ratio((30, 58), self.ratio), 
                                    adapt_ratio((190, 22), self.ratio), 
                                    min_val=self.MOON_MASS, val=1, max_val=10**6, parent=self)
        self.mass_text = ModifiableText(adapt_ratio((140, 39), self.ratio), 
                                    adapt_ratio((110, 20), self.ratio),
                                    max_len=13, parent=self,
                                    letter_width=0.97, numeric=True,
                                    dims=(w,h), conversion_func=(lambda x,y: x[:-3] if y else x + " kg"))
        self.radius_bar = ProgressBar(adapt_ratio((30,105), self.ratio), 
                                    adapt_ratio((190,22), self.ratio), 
                                    min_val=1, val=3, max_val=17, parent=self)
        self.name_textbox = TextBox(adapt_ratio((20,-30), self.ratio), 
                                    adapt_ratio((216, 40), self.ratio), 
                                    max_len=10, 
                                    parent=self, letter_width=0.75)
        self.vel_text = ModifiableText(adapt_ratio((117, 158), self.ratio),
                                    adapt_ratio((125,20), self.ratio),
                                    max_len=14, parent=self, letter_width=0.9,
                                    numeric=True, dims=(w,h), 
                                    conversion_func=lambda x,y: x[:-7] if y else x+" km/day")
        self.angle_text = ModifiableText(adapt_ratio((175,182), self.ratio),
                                     adapt_ratio((60,25), self.ratio),
                                     max_len=3, parent=self, numeric=True)
        self.orbit_tickbox = Tickbox(adapt_ratio((175,132), self.ratio), 
                                    adapt_ratio((18,18), self.ratio), parent=self)
        self.vangle_setter = AngleSelector(adapt_ratio((35,175),self.ratio), adapt_ratio((26,26),self.ratio), parent=self)

    def update_texts(self, force_update=False) -> None:
        '''
            Update the info text about the selected body.\n
            force_update -> whether to force the update of the text of the mass of the body, if it's false (as default)
            it might not be updated due to an optimization technique.
        '''
        self.xpos_text.set_text('('+str(int(self.body.pos[0]))+',')
        self.ypos_text.set_text(' '+str(int(self.body.pos[1]))+')')
        self.vel_text.set_text(self.body.get_vel_str())
        self.angle_text.set_text(self.body.get_angle_str())
        # only update the text of the mass if it has been changed or if it hasn't been initialized
        if self.mass_bar.enabled or self.mass_text.text == '' or force_update:
            self.mass_text.set_text(self.body.get_mass_str())

    def is_on_element(self, mouse_pos) -> bool:
        if super().is_on_element(mouse_pos):
            return True
        return self.name_textbox.is_on_element(mouse_pos)

    def __widgets_click(self, mouse_pos) -> None:
        '''
            Lets every widget handle a click event in the given mouse position, and updates their
            corresponding values in the self.body instance
        '''
        self.orbit_tickbox.on_click(mouse_pos)
        # PROGRESS BARS AND TICKBOXES
        if self.vangle_setter.on_click(mouse_pos):
            self.body.set_vel_angle(self.vangle_setter.angle)
        elif self.mass_bar.on_click(mouse_pos):
            self.body.set_mass(self.mass_bar.val, change_radius=False)
        elif self.radius_bar.on_click(mouse_pos):
            self.body.set_radius(self.radius_bar.val)
        
        # TEXTBOXES
        if self.xpos_text.on_click(mouse_pos):
            xpos = parseNum(self.xpos_text.text[1:-1]) # ignore '(' and ','
            if xpos is None:
                UIElement.popup_msg.cast("Invalid value!", 3, 0.4)
            else:
                self.body.pos[0] = xpos
        elif self.ypos_text.on_click(mouse_pos):
            ypos = parseNum(self.ypos_text.text[1:-1])
            if ypos is None:
                UIElement.popup_msg.cast("Invalid value!", 3, 0.4)
            else:
                self.body.pos[1] = ypos
        elif self.mass_text.on_click(mouse_pos):
            if not self.body.set_mass_str(self.mass_text.text):
                UIElement.popup_msg.cast("Invalid value!", 3, 0.4)
        elif self.vel_text.on_click(mouse_pos):
            if not self.body.set_vel_str(self.vel_text.text):
                UIElement.popup_msg.cast("Invalid value!", 3, 0.4)
        elif self.name_textbox.on_click(mouse_pos):
            self.body.name = self.name_textbox.content   
        elif self.angle_text.on_click(mouse_pos):
            parsed_deg_angle = parseNum(self.angle_text.text)
            if parsed_deg_angle is not None:
                parsed_deg_angle = round(parsed_deg_angle)%360
                rad_angle = aconvert(parsed_deg_angle, rad_to_deg=False)
                self.body.set_vel_angle(rad_angle)
                self.vangle_setter.set_angle(rad_angle)
            else:
                UIElement.popup_msg.cast("Invalid value!", 3, 0.4)

    def on_click(self, mouse_pos) -> None:
        if not self.enabled:
            return
        if self.is_on_element(mouse_pos):
            self.__widgets_click(mouse_pos) # let every widget handle the clicks

        # make sure the UI keeps rendering it the click was outside its region but inside the name textbox's
        if self.body is not None:
            if self.body.is_on_body(mouse_pos):
                self.dragging = True
                self.click_start = time.time()

    def handle_event(self, event, *args) -> None:
        if not self.enabled:
            return
        self.name_textbox.handle_event(event)
        self.xpos_text.handle_event(event)
        self.ypos_text.handle_event(event)
        self.mass_text.handle_event(event)
        self.vel_text.handle_event(event)
        self.angle_text.handle_event(event)

    def on_mouse_motion(self, mouse_pos) -> None:
        if self.dragging:
            self.body.set_pos(mouse_pos)
            if self.body.get_abs_vel() != 0 and time.time()-self.click_start > self.MIN_CLICK_CHANGE_VEL_TIME:
                self.body.set_vel((0,0))
            self.enabled = not self.is_on_element(mouse_pos)
        else:
            if not self.enabled or not self.is_on_element(mouse_pos):
                return
            # if the value of the mass bar has been changed update the body's value
            if self.mass_bar.on_mouse_motion(mouse_pos):
                self.body.set_mass(self.mass_bar.val)
            # if the value of the radius bar has been changed update the body's value
            if self.radius_bar.on_mouse_motion(mouse_pos):
                self.body.set_radius(self.radius_bar.val)
            # the angle of the velocity has been changed
            if self.vangle_setter.on_mouse_motion(mouse_pos):
                self.body.set_vel_angle(self.vangle_setter.angle)

    def on_click_release(self, mouse_pos, mouse_vel) -> None:
        if not self.enabled:
            return
            
        self.orbit_tickbox.on_click_release(mouse_pos)
        if self.dragging:
            self.dragging = False
            # looks dumb but this way I don't have to import numpy just for this one line
            if time.time() - self.click_start > self.MIN_CLICK_THROW_TIME:
                if self.MIN_THROW_VEL < (mouse_vel[0]**2+mouse_vel[1]**2)**(0.5) < self.MAX_THROW_VEL: 
                    self.body.set_vel(mouse_vel) # args[1] is the displacement of the mouse from the last frame

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=True)
        self.ratio = (wnew/800.0, hnew/600.0)
        self.xpos_text.set_max_len(get_mg_order(wnew))
        self.ypos_text.set_max_len(get_mg_order(hnew))

    def log_body(self, body: Body, mouse_pos=None, dragged=False) -> None:
        mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
        is_on_gui = self.is_on_element(mouse_pos)
        # if there is no body
        if body is None:
            if not is_on_gui: # if the body is None (implied in the previous if) and the click was outside the gui
                self.enabled = False
            return
        
        self.enabled = True
        self.mass_bar.val = body.mass
        self.dragging = dragged # whether the body immediately starts out as being dragged
        self.radius_bar.val = body.radius
        self.body = body
        self.update_texts(force_update=True) # re-render the velocity and mass text
        self.name_textbox.set_text(self.body.name)
        self.xpos_text.set_text('('+str(int(body.pos[0]))+',', disable=True)
        self.ypos_text.set_text(' '+str(int(body.pos[1]))+')', disable=True)
        self.mass_text.set_text(self.body.get_mass_str(), disable=True)
        self.vel_text.set_text(self.body.get_vel_str(), disable=True)
        self.vangle_setter.set_angle(get_angle(body.vel))
        self.angle_text.set_text(body.get_angle_str(), disable=True)
        self.orbit_tickbox.set_ticked(False)
        self.body_path = []

    def update(self) -> None:
        if not self.enabled:
            return

        if self.orbit_tickbox.ticked:
            if len(self.body_path) > self.MAX_BODY_PATH_LEN:
                self.body_path = self.body_path[1:len(self.body_path)]
            self.body_path.append((int(self.body.pos[0]), int(self.body.pos[1])))

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return
            
        self.update_texts()
        self.body.render_velocity(surf)

        # draw body path if "draw orbit" is ticked
        if self.orbit_tickbox.ticked:
            for pos in self.body_path:
                pygame.draw.circle(surf, (255,255,255), pos, int(self.body.radius*3/4))

        super().render(surf) # make sure the background image is rendered after the velocity vector

        self.xpos_text.render(surf)
        self.ypos_text.render(surf)
        self.mass_bar.render(surf)
        self.radius_bar.render(surf)
        self.name_textbox.render(surf)
        self.orbit_tickbox.render(surf)    
        self.mass_text.render(surf)
        self.vel_text.render(surf)
        self.vangle_setter.render(surf)
        self.angle_text.render(surf)

class OptionsMenu(UIElement):

    def __init__(self, w, h) -> None:
        super().__init__((w, 0), (int(256*w/800.0),h), texture='options_menu.png')
        self.ratio = (w/800.0, h/600.0)
        # button to open or close the menu, due to its texture it merges with the rest of the menu itself
        self.toggle_button = Button(adapt_ratio((-64,0), self.ratio),
                                    adapt_ratio((64,64), self.ratio),
                                    textures=load_spritesheet('options_menu_button.png', tile_w=64, tile_h=64),
                                    parent=self)
        # Menu opening/closing animations
        self.init_animations(w)
        self.opened = False # whether the menu is opened or not
        self.init_widgets(w,h)

    def init_widgets(self, w, h):
        self.resolution_list = DropDownList(adapt_ratio((120,40), self.ratio), adapt_ratio((120,32),self.ratio),
                                            [str(res).replace('(','').replace(')','').replace(', ','x') for res in get_available_resolutions()],
                                            parent=self, dims=(w,h), initial_element=f"{w}x{h}")
        self.fullscreen_tickbox = Tickbox(adapt_ratio((160,90), self.ratio), adapt_ratio((24,24), self.ratio),
                                            parent=self)
        self.brightness_bar = ProgressBar(adapt_ratio((120, 140), self.ratio), adapt_ratio((120,32), self.ratio),
                                        min_val=100, val=255, max_val=255, parent=self,
                                        fill_color=(192,192,192), background_color=(145,145,145), border_size=3)
        self.grav_field_tickbox = Tickbox(adapt_ratio((160, 190), self.ratio), adapt_ratio((24,24), self.ratio),
                                            parent=self, ticked=True)
        self.apply_button = TextButton(adapt_ratio((92, 230), self.ratio), adapt_ratio((80,24), self.ratio), "Apply", parent=self)
        
        # SAVE/LOAD MENU
        self.save_textbox = TextBox(adapt_ratio((18, 300), self.ratio), adapt_ratio((128,32), self.ratio),
                                    max_len=9, letter_width=0.8, parent=self)
        self.save_button = TextButton(adapt_ratio((156, 300), self.ratio), adapt_ratio((64,32), self.ratio),
                                    "Save",  parent=self)
        self.load_list = DropDownList(adapt_ratio((18, 350), self.ratio), adapt_ratio((128,32), self.ratio), 
                                    entries=[x.split('.')[0] for x in get_saves()], parent=self, dims=(w,h),)
        self.load_button = TextButton(adapt_ratio((156, 350), self.ratio), adapt_ratio((64,32), self.ratio),
                                    "Load", parent=self)
        self.delete_list = DropDownList(adapt_ratio((18,400), self.ratio), adapt_ratio((128,32), self.ratio),
                                    entries=[x.split('.')[0] for x in get_saves()], parent=self, dims=(w,h))
        self.delete_button = TextButton(adapt_ratio((156,400), self.ratio), adapt_ratio((64,32),self.ratio),
                                        "Delete", parent=self)
        
    def init_animations(self, w) -> None:
        '''
            Initializes the open/close animation of the menu based on the given width of the screen w
        '''
        open_frames = [{'pos': (w, 0)}, {'pos': (w-self.size[0], 0), 'time': 0.4}]
        close_frames = [{'pos': (w-self.size[0],0)}, {'pos':(w,0), 'time': 0.4}]
        self.slide_animations = [Animation(open_frames), Animation(close_frames)]

    def on_click(self, mouse_pos):
        self.toggle_button.on_click(mouse_pos)

        if not self.opened or not self.is_on_element(mouse_pos):
            return

        if not self.resolution_list.on_click(mouse_pos):
            for widget in self.get_child_widgets():
                if widget != self.resolution_list:
                    widget.on_click(mouse_pos)

    def on_settings_apply(self) -> None:
        selected_win_size = [int(x) for x in self.resolution_list.get_selected().split("x")]
        pygame.event.post(pygame.event.Event(GRAPHICS_UPDATE_EVENT, new_brightness=int(self.brightness_bar.val), 
                                            field_rendered=self.grav_field_tickbox.ticked, new_size=selected_win_size,
                                            fullscreen=self.fullscreen_tickbox.ticked))

    def on_click_release(self, mouse_pos, *args): 
        if self.toggle_button.on_click_release(mouse_pos):
            # opened = False -> the menu is being opened -> animation at index 0 = int(False) = int(opened)
            # opened = True -> the menu being closed -> animation at index 1 = int(True) = int(opened)
            self.slide_animations[int(self.opened)].start() # restart the animation
            self.opened = not self.opened # toggle the opening or closure of the menu

        if not self.opened or not self.is_on_element(mouse_pos):
            return

        if not self.resolution_list.on_click_release(mouse_pos):
            if self.apply_button.on_click_release(mouse_pos):
                self.on_settings_apply()
                return
            self.fullscreen_tickbox.on_click_release(mouse_pos)
            self.grav_field_tickbox.on_click_release(mouse_pos)
            self.save_textbox.on_click_release(mouse_pos)
            self.load_list.on_click_release(mouse_pos)
            self.delete_list.on_click_release(mouse_pos)
            # if the delete button has been pressed delete the selected world
            if self.delete_button.on_click_release(mouse_pos):
                del_save(self.delete_list.get_selected())
                self.load_list.remove_entry(self.delete_list.get_selected()) # remove the space from the other
                self.delete_list.remove_entry(self.delete_list.get_selected()) # drop down lists
                UIElement.popup_msg.cast("Space deleted!", 3, fade_time=0.4)
                # remove the element from the other lists so one cannot try to load a deleted space
            if self.load_button.on_click_release(mouse_pos):
                pygame.event.post(pygame.event.Event(SPACE_LOAD_EVENT, space_name=self.load_list.get_selected()))
                self.save_textbox.set_text(self.load_list.get_selected())
                UIElement.popup_msg.cast("Space loaded!", 3, fade_time=0.4)

            if self.save_button.on_click_release(mouse_pos):
                if len(self.save_textbox.content) != 0:
                    pygame.event.post(pygame.event.Event(SPACE_SAVE_EVENT, space_name=self.save_textbox.content)) # call an event to save the space
                    self.save_textbox.set_text("")
                    UIElement.popup_msg.cast("Space saved!", 3, fade_time=0.4)

    def on_mouse_motion(self, mouse_pos) -> None:
        self.toggle_button.on_mouse_motion(mouse_pos)
        if not self.opened or not self.is_on_element(mouse_pos):
            return

        # check whether the resolution list is highlighted before checking if any other (possibly underlying in the menu) widget also is
        self.resolution_list.on_mouse_motion(mouse_pos)
        if self.resolution_list.is_on_element(mouse_pos):
            return
        for widget in self.get_child_widgets():
            if widget != self.toggle_button and widget != self.resolution_list:
                widget.on_mouse_motion(mouse_pos)

    def handle_event(self, event, *args) -> None:
        if not self.opened:
            return

        self.save_textbox.handle_event(event)

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=True)
        self.ratio = (wnew/800.0, hnew/600.0)
        self.init_animations(wnew)

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return

        # by changing the actual position of the widget the children widgets behave appropriately
        if self.slide_animations[int(not self.opened)].running:
            self.pos = self.slide_animations[int(not self.opened)].get_pos(updating=False)

        self.toggle_button.render(surf)

        # only render the widgets if the menu is open (or if it's closing)
        if self.opened or self.slide_animations[int(not self.opened)].running:
            super().render(surf)
            for widget in self.get_child_widgets():
                if type(widget) != DropDownList: # render these on top to avoid overlappings
                    widget.render(surf)
            self.resolution_list.render(surf)
            self.delete_list.render(surf)
            self.load_list.render(surf)


'''
    Will handle the menu that shows up when multiple bodies are selected
'''
class BodyHandlerUI(UIElement):
    DEFAULT_SELECTION_BORDER = 2

    def __init__(self, w, h) -> None:
        super().__init__((0,0), (0,0))
        self.ratio = (w/800.0, h/600.0)
        self.addbody_button = Button(adapt_ratio((20,130), self.ratio), adapt_ratio((40,40), self.ratio),
                                    textures=load_spritesheet("plus_button.png", tile_w=64, tile_h=64))
        self.removebody_button = Button(adapt_ratio((20, 180), self.ratio), adapt_ratio((40,40), self.ratio), 
                                    textures=load_spritesheet("minus_button.png", tile_w=64, tile_h=64))
        self.selecting = False # whether we are selecting a bunch of bodies or not
        self.selection = [0,0,0,0] # xy corner of the selection + wh (width and height) of the selection
        self.selection_border = int(self.DEFAULT_SELECTION_BORDER*(w+h)/1400.0)
        self.bodies_menu = BodyMenu(w, h)

    def on_click(self, mouse_pos) -> None:
        self.addbody_button.on_click(mouse_pos)
        self.removebody_button.on_click(mouse_pos)
        self.bodies_menu.on_click(mouse_pos)

    def handle_event(self, event, mouse_pos) -> None:
        # right click press --> start mutiple bodies selection
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.selecting = True
            self.selection[:2] = mouse_pos # log the position of the selection
            self.selection[2:] = (0,0) # start with an initial width and height of 0
        # right click release --> end mutiple bodies selection    
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3: 
            self.selecting = False
            pygame.event.post(pygame.event.Event(BODIES_SELECT_EVENT, pos=self.selection[:2], size=self.selection[2:]))
        self.bodies_menu.handle_event(event)

    def select_bodies(self, bodies: list) -> None:
        self.bodies_menu.log_bodies(bodies)

    def on_click_release(self, mouse_pos, *args):
        if not self.addbody_button.enabled:
            self.addbody_button.enabled = True
            self.removebody_button.enabled = True

        if self.addbody_button.on_click_release(mouse_pos):
            new_body = Body(mouse_pos, 1)
            pygame.event.post(pygame.event.Event(BODY_ADD_EVENT, body=new_body))
            UIElement.popup_msg.cast("Body added!", 3, 0.4)
            self.addbody_button.enabled = False
            self.removebody_button.enabled = False
        elif self.removebody_button.on_click_release(mouse_pos):
            pygame.event.post(pygame.event.Event(BODY_REMOVE_EVENT))
        
        self.bodies_menu.on_click_release(mouse_pos)

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=True)
        self.ratio = (wnew/800.0, hnew/800.0)

    def is_on_element(self, mouse_pos) -> bool:
        return self.addbody_button.is_on_element(mouse_pos) or self.removebody_button.is_on_element(mouse_pos)

    def on_mouse_motion(self, mouse_pos) -> None:
        self.addbody_button.on_mouse_motion(mouse_pos)
        self.removebody_button.on_mouse_motion(mouse_pos)
        self.bodies_menu.on_mouse_motion(mouse_pos)

        if self.selecting:
            self.selection[2] = mouse_pos[0]-self.selection[0]
            self.selection[3] = mouse_pos[1]-self.selection[1]
    
    def render(self, surf: pygame.Surface) -> None:
        self.addbody_button.render(surf)
        self.removebody_button.render(surf)
        self.bodies_menu.render(surf)

        if self.selecting:
            pygame.draw.rect(surf, (255,255,255), self.selection, self.selection_border)

'''
    Immediately disactivates when someone clicks
'''
class BodyMenu(UIElement):

    def __init__(self, w, h) -> None:
        super().__init__((int(580*w/800.0), int(260*h/600.0)), (int(180*w/800.0), int(341*h/600.0)), 
                        texture='bodies_menu.png', enabled=False)
        self.ratio = (w/800.0, h/600.0)
        self.__init_widgets(w, h)

    def __init_widgets(self, w, h) -> None:
        self.xpos_text = ModifiableText(adapt_ratio((95,48),self.ratio), adapt_ratio((32,25), self.ratio),
                                        max_len=get_mg_order(w), parent=self, letter_width=0.95, numeric=True,
                                        dims=(w,h), conversion_func=lambda x,y: x[1:-1] if y else '('+str(int(float(x)))+',')
        self.ypos_text = ModifiableText(adapt_ratio((126,48), self.ratio), adapt_ratio((35,25), self.ratio), 
                                        max_len=get_mg_order(h), parent=self, letter_width=0.95, numeric=True,
                                        dims=(w,h), conversion_func=lambda x,y: x[1:-1] if y else ' '+str(int(float(x)))+')')

    def log_bodies(self, bodies):
        '''
            Log the given bodies on the menu
        '''
        # there's no point in using the menu if only 1 body is selected, there's planetUI for that
        if len(bodies) <= 1:
            self.enabled = False
            return
        # TODO: there's not actual point in recreating all the buttons since the size, pos and texture don't change,
        # I just need to change the text instead, and to create new ones when there aren't enough
        self.enabled = True
        self.bodies_pos = [] # for each body this is its corresponding position, the indexing is the same as the button's
        self.body_buttons = []
        for idx in range(len(bodies)):
            self.bodies_pos.append(bodies[idx].pos)
            button_size = adapt_ratio((143,48), self.ratio)
            pos = adapt_ratio((18, 70+button_size[1]*idx), self.ratio)
            max_len = len(bodies[idx].name)+1
            self.body_buttons.append(TextButton(pos, button_size, bodies[idx].name, parent=self, max_len=max_len))

        average_pos = get_average([body.pos for body in bodies])
        self.xpos_text.set_text(f"({str(round(average_pos[0]))},", disable=True)
        self.ypos_text.set_text(f" {str(round(average_pos[1]))})", disable=True)

    def on_click(self, mouse_pos):
        if not self.is_on_element(mouse_pos):
            self.enabled = False
        if not self.enabled:
            return

        if self.xpos_text.on_click(mouse_pos):
            # TODO: change the position of each body
            avg_x_pos = get_average(self.bodies_pos)[0]
            offset = parseNum(self.xpos_text.text[1:-1])-avg_x_pos # ignore '(' and ','
            for body_pos in self.bodies_pos:
                body_pos[0] += offset
        elif self.ypos_text.on_click(mouse_pos):
            avg_y_pos = get_average(self.bodies_pos)[1]
            offset = parseNum(self.ypos_text[1:-1])-avg_y_pos
            for body_pos in self.bodies_pos:
                body_pos[1] += offset

        for button in self.body_buttons:
            # the actual click is handled on on_click_release()
            if button.on_click(mouse_pos):
                return
    
    def on_mouse_motion(self, mouse_pos) -> None:
        if not self.enabled:
            return

        self.xpos_text.on_mouse_motion(mouse_pos)
        self.ypos_text.on_mouse_motion(mouse_pos)

        for button in self.body_buttons:
            button.on_mouse_motion(mouse_pos)
        
    def handle_event(self, event) -> None:
        if not self.enabled:
            return
        
        self.xpos_text.handle_event(event)
        self.ypos_text.handle_event(event)

    def on_click_release(self, mouse_pos, *args):
        if not self.enabled:
            return

        for idx in range(len(self.body_buttons)):
            if self.body_buttons[idx].on_click_release(mouse_pos):
                pygame.event.post(pygame.event.Event(BODIES_SELECT_EVENT, pos=self.bodies_pos[idx], size=(1,1)))

    
    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        if self.enabled:
            self.xpos_text.render(surf)
            self.ypos_text.render(surf)

            for button in self.body_buttons:
                button.render(surf)