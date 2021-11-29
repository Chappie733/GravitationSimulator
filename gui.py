from animations import Animation
from body import Body
from widgets import *
from utils import load_spritesheet, adapt_ratio, get_angle, aconvert

TIME_UPDATE_EVENT = pygame.USEREVENT+1
WINDOW_RESIZE_EVENT = pygame.USEREVENT+2

'''
TODO:
    - Go through every widget and customize on_window_resize() so that the textures are also scaled
        along with the size itself
    - Also change the widget's ratio variable so when its used in render() the positions aren't messed up
    - In modifiable text as long as I initialize the font again when the window is resized, the size of the
        text it is used to render will also be adjusted, so i will just have to call UIElement.init_font(new_width)
'''


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

    def update(self) -> None:
        self.days += self.get_time_rate()

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        self._update_text()
        surf.blit(self.time_text, adapt_ratio((5,10), self.ratio)) 

        self.pause_box.render(surf)
        self.speed_up_button.render(surf)
        self.slow_down_button.render(surf)
        self.time_rate_bar.render(surf)

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=True)
        self.ratio = (wnew/800.0, hnew/600.0)

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
        super().__init__((int(530*w/800),int(400*h/600)), (int(256*w/800),int(190*h/600)), "gui_background.png")
        # the values were adjusted for this resolution, this way they can be scaled to any given resolution
        self.ratio = (w/800.0, h/600.0)
        self.mass_bar = ProgressBar(adapt_ratio((30, 37), self.ratio), 
                                    adapt_ratio((190, 22), self.ratio), 
                                    min_val=self.MOON_MASS, val=1, max_val=10**6, parent=self)
        self.mass_text = ModifiableText(adapt_ratio((103, 18), self.ratio), 
                                    adapt_ratio((125, 20), self.ratio),
                                    max_len=14, parent=self,
                                    letter_width=0.9, numeric=True,
                                    dims=(w,h), conversion_func=(lambda x,y: x[:-3] if y else x + " kg"))
        self.radius_bar = ProgressBar(adapt_ratio((30,83), self.ratio), 
                                    adapt_ratio((190,22), self.ratio), 
                                    min_val=1, val=3, max_val=17, parent=self)
        self.name_textbox = TextBox(adapt_ratio((20,-30), self.ratio), 
                                    adapt_ratio((216, 40), self.ratio), 
                                    max_len=10, 
                                    parent=self, letter_width=0.75)
        self.vel_text = ModifiableText(adapt_ratio((117, 135), self.ratio),
                                    adapt_ratio((125,20), self.ratio),
                                    max_len=14, parent=self, letter_width=0.9,
                                    numeric=True, dims=(w,h), 
                                    conversion_func=lambda x,y: x[:-7] if y else x+" km/day")
        self.angle_text = ModifiableText(adapt_ratio((128,160), self.ratio),
                                     adapt_ratio((60,25), self.ratio),
                                     max_len=3, parent=self, numeric=True)
        self.orbit_tickbox = Tickbox(adapt_ratio((175,110), self.ratio), 
                                    adapt_ratio((18,18), self.ratio), parent=self)
        self.vangle_setter = AngleSelector((30,150), (25,25), parent=self) # velocity angle setter
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
        if self.mass_bar.on_click(mouse_pos):
            self.body.set_mass(self.mass_bar.val)
        if self.radius_bar.on_click(mouse_pos):
            self.body.radius = int(self.radius_bar.val)
        
        # TEXTBOXES
        if self.mass_text.on_click(mouse_pos):
            self.body.set_mass_str(self.mass_text.text)
        if self.vel_text.on_click(mouse_pos):
            self.body.set_vel_str(self.vel_text.text)
        if self.name_textbox.on_click(mouse_pos):
            self.body.name = self.name_textbox.content   
        if self.angle_text.on_click(mouse_pos):
            parsed_deg_angle = round(float(self.angle_text.text))%360
            rad_angle = aconvert(parsed_deg_angle, rad_to_deg=False)
            self.body.set_vel_angle(rad_angle)
            self.vangle_setter.set_angle(rad_angle)

    def on_click(self, mouse_pos) -> None:
        if not self.enabled:
            return
        self.__widgets_click(mouse_pos) # let every widget handle the clicks

        # make sure the UI keeps rendering it the click was outside its region but inside the name textbox's
        if self.body is not None:
            if self.body.is_on_body(mouse_pos):
                self.dragging = True
                self.click_start = time.time()

    def handle_event(self, event) -> None:
        if not self.enabled:
            return
        self.name_textbox.handle_event(event)
        self.angle_text.handle_event(event)
        self.mass_text.handle_event(event)
        self.vel_text.handle_event(event)

    def on_mouse_motion(self, mouse_pos) -> None:
        if not self.enabled:
            return
        
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
        '''
        self.mass_text.on_window_resize(wold,hold,wnew,hnew)
        self.mass_text.on_window_resize(wold,hold,wnew,hnew)
        self.radius_bar.on_window_resize(wold,hold,wnew,hnew)
        self.name_textbox.on_window_resize(wold,hold,wnew,hnew)
        self.vel_text.on_window_resize(wold,hold,wnew,hnew)
        self.angle_text.on_window_resize(wold,hold,wnew,hnew)
        self.orbit_tickbox.on_window_resize(wold,hold,wnew,hnew)
        self.vangle_setter.on_window_resize(wold,hold,wnew,hnew)
        '''
        self.ratio = (wnew/800.0, hnew/600.0)

    def log_body(self, body: Body, mouse_pos=None) -> None:
        mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
        is_on_gui = self.is_on_element(mouse_pos)
        # if there is no body or the click was on the GUI just do nothing
        if body is None or is_on_gui:
            if not is_on_gui: # if the body is None (implied in the previous if) and the click was outside the gui
                self.enabled = False
            return
        
        self.enabled = True
        self.mass_bar.val = body.mass
        self.radius_bar.val = body.radius
        self.body = body
        self.update_texts(force_update=True) # re-render the velocity and mass text
        self.name_textbox.set_text(self.body.name)
        self.mass_text.set_text(self.body.get_mass_str())
        self.vel_text.set_text(self.body.get_vel_str())
        self.vangle_setter.set_angle(get_angle(body.vel))
        self.angle_text.set_text(body.get_angle_str())
        self.orbit_tickbox.set_ticked(False)
        self.body_path = []

    def update(self) -> None:
        if self.orbit_tickbox.ticked:
            if len(self.body_path) > self.MAX_BODY_PATH_LEN:
                self.body_path = self.body_path[1:len(self.body_path)]
            self.body_path.append((int(self.body.pos[0]), int(self.body.pos[1])))

    def render(self, surf: pygame.Surface) -> None:
        if self.enabled:
            self.update_texts()
            self.body.render_velocity(surf)

            # draw body path if "draw orbit" is ticked
            if self.orbit_tickbox.ticked:
                for pos in self.body_path:
                    pygame.draw.circle(surf, (255,255,255), pos, int(self.body.radius*3/4))

            super().render(surf) # make sure the background image is rendered after the velocity vector

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
        super().__init__((w, 0), (int(185*w/800.0),h), texture='options_menu.png')
        self.ratio = (w/800.0, h/600.0)
        # button to open or close the menu, due to its texture it merges with the rest of the menu itself
        self.toggle_button = Button(adapt_ratio((-64,0), self.ratio),
                                    adapt_ratio((64,64), self.ratio),
                                    textures=load_spritesheet('options_menu_button.png', tile_w=64, tile_h=64),
                                    parent=self)
        self.enabled = True
        # Menu opening/closing animations
        self.init_animations(w)
        self.opened = False # whether the menu is opened or not

    def init_animations(self, w) -> None:
        '''
            Initializes the open/close animation of the menu based on the given width of the screen w
        '''
        open_frames = [{'pos': (w, 0)}, {'pos': (w-self.size[0], 0), 'time': 0.4}]
        close_frames = [{'pos': (w-self.size[0],0)}, {'pos':(w,0), 'time': 0.4}]
        self.slide_animations = [Animation(open_frames), Animation(close_frames)]

    def on_click(self, mouse_pos):
        self.toggle_button.on_click(mouse_pos)

    def on_click_release(self, mouse_pos, *args):
        if self.toggle_button.on_click_release(mouse_pos):
            # opened = False -> the menu is being opened -> animation at index 0 = int(False) = int(opened)
            # opened = True -> the menu being closed -> animation at index 1 = int(True) = int(opened)
            self.slide_animations[int(self.opened)].start() # restart the animation
            self.opened = not self.opened # toggle the opening or closure of the menu

    def on_mouse_motion(self, mouse_pos) -> None:
        self.toggle_button.on_mouse_motion(mouse_pos)

    def on_window_resize(self, wold, hold, wnew, hnew) -> None:
        super().on_window_resize(wold, hold, wnew, hnew, resize_widgets=False)
        self.ratio = (wnew/800.0, hnew/600.0)
        self.init_animations(wnew)

    def update(self, *args) -> None:
        self.slide_animations[int(not self.opened)].update()

    def render(self, surf: pygame.Surface) -> None:
        if not self.enabled:
            return

        # by changing the actual position of the widget the children widgets behave appropriately
        if self.slide_animations[int(not self.opened)].running:
            self.pos = self.slide_animations[int(not self.opened)].get_pos(updating=True)

        super().render(surf)
        self.toggle_button.render(surf)