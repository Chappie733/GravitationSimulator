import pygame
import os

from body import Body

class GUI:

    def __init__(self) -> None:
        self.widgets = []
        self.enabled = True

    def handle_event(self, event, mouse_pos=None, mouse_vel=None) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
            for widget in self.widgets:
                widget.on_click(mouse_pos)
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
            for widget in self.widgets:
                widget.on_mouse_motion(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONUP:
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

class GUIElement:
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
    def init_font():
        GUIElement.font = pygame.font.SysFont('Verdana Bold Italic', 23)


class ProgressBar(GUIElement):
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

    def on_mouse_motion(self, mouse_pos) -> None:
        if pygame.mouse.get_pressed()[0]:
            self.on_click(mouse_pos)
    
    def render(self, surf: pygame.Surface) -> None:
        prog_w = int((self.val-self.min_val)/(self.max_val-self.min_val)*self.size[0]) # width of the progress color (in pixels)
        src = (0,0) if self.parent is None else self.parent.pos
        pygame.draw.rect(surf, self.BACKGROUND_COLOR, (src[0]+self.pos[0], src[1]+self.pos[1], self.size[0], self.size[1]))
        pygame.draw.rect(surf, self.PROGRESS_COLOR, (src[0]+self.pos[0], src[1]+self.pos[1], prog_w, self.size[1]))


class PlanetGUI(GUIElement):
    SUN_MASS = 3.32954355178996e5 # mass of the sun/mass of the earth
    MOON_MASS = 1.230312630186531e-2 # mass of the moon/mass of the earth

    def __init__(self, w, h) -> None:
        super().__init__((int(500/w*800),int(20/h*600)), (int(256/w*800),int(166/h*600)), "gui_background.png")
        self.w, self.h = w, h
        self.mass_bar = ProgressBar((30,38), (190,22), min_val=self.MOON_MASS, val=1, max_val=10**6, parent=self)
        self.radius_bar = ProgressBar((32,93), (190, 22), min_val=1, val=3, max_val=17, parent=self)
        self.vel_text = super().font.render("0", False, (255,255,255), 0)
        self.body = None
        self.dragging = False # whether the selected body is being dragged

    def set_velocity(self, vel: float) -> None:
        self.vel_text = super().font.render(str(round(vel, 2))+"*10^6 km/day", False, (255,255,255))

    def on_click(self, mouse_pos) -> None:
        self.mass_bar.on_click(mouse_pos)
        self.radius_bar.on_click(mouse_pos)
        if self.body is not None:
            if self.body.is_on_body(mouse_pos):
                self.dragging = True
                self.body.set_vel((0,0))

    def on_mouse_motion(self, mouse_pos) -> None:
        self.mass_bar.on_mouse_motion(mouse_pos)
        self.radius_bar.on_mouse_motion(mouse_pos)
        if self.dragging:
            self.body.set_pos(mouse_pos)
    
    def on_click_release(self, *args) -> None:
        if self.dragging:
            self.dragging = False
            self.body.set_vel(args[1]) # args[1] is the displacement of the mouse from the last frame

    def log_body(self, body: Body, enable=True, mouse_pos=None) -> None:
        if body is None:
            mouse_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
            super().on_click(mouse_pos)
            return
        self.enabled = enable
        self.mass_bar.val = body.mass
        self.radius_bar.val = body.radius
        self.set_velocity(body.get_abs_vel()) # re-render the velocity text
        self.body = body

    def render(self, surf: pygame.Surface) -> None:
        super().render(surf)
        if self.enabled:
            self.set_velocity(self.body.get_abs_vel())
            self.mass_bar.render(surf)
            self.radius_bar.render(surf)
            surf.blit(self.vel_text, (self.pos[0]+int(105*self.w/800.0), self.pos[1]+int(135*self.h/600))) # velocity text

            # if the mass or the radius was changed, change the body's parameters accordingly
            if self.mass_bar.enabled:
                self.body.set_mass(self.mass_bar.val)
            elif self.radius_bar.enabled: 
                self.body.radius = int(self.radius_bar.val)