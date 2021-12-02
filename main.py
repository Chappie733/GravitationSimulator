import pygame
from gui import *
from space import *
from widgets import TextBox

BACKGROUND_COLOR = (0,0,0)

def main():
    W,H = 800, 600
    UIElement.init_font(W=W)

    win = pygame.display.set_mode((W,H))
    surf = pygame.Surface((W,H), pygame.SRCALPHA)
    fps = 30
    running = True
    clock = pygame.time.Clock()

    pygame.display.set_caption("Gravity")
    pygame.display.set_icon(load_texture("logo.png"))

    first, second = Body((W//2-148,H//2+10), 1), Body((W//2,H//2-10), 3.32954355178996e5)
    first.vel = np.array([0,29.78*1e-6*86400], dtype=np.float64)
    space = Space([first,second], tick_time=1)

    gui = UI()
    gui.add_widget(PlanetUI(W,H))
    gui.add_widget(TimeUI(W,H))
    gui.add_widget(OptionsMenu(W,H))

    while running:
        clock.tick(fps)
        mouse_vel = pygame.mouse.get_rel() # mouse velocity
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    space.on_click()
                elif event.button == 1:
                    if not gui.get_by_type(TimeUI).is_on_element(mouse_pos): # if the click wasn't on the time ui
                        loaded_body = space.get_body(mouse_pos) # get the body in the position clicked
                        gui.get_by_type(PlanetUI).log_body(loaded_body, mouse_pos) # update the planet ui with the selected body

            elif event.type == TIME_UPDATE_EVENT:
                space.tick_time = gui.get_by_type(TimeUI).get_time_rate()
            elif event.type == WINDOW_RESIZE_EVENT:
                new_win_size = event.new_size
                gui.on_window_resize(W,H, new_win_size[0], new_win_size[1])
                W,H = new_win_size
                UIElement.init_font(W)
                win = pygame.display.set_mode(new_win_size, pygame.FULLSCREEN if event.fullscreen else 0) # reinitialize the window
                surf = pygame.Surface(new_win_size) # reinitialize the surface

            gui.handle_event(event, mouse_pos=mouse_pos, mouse_vel=mouse_vel)

        surf.fill(BACKGROUND_COLOR)
        if gui.get_by_type(TimeUI).is_time_enabled():
            space.update()
            gui.update()

        space.render(surf)
        space.render_grav_field(surf, margin=int(75*(W+H)/1400.0), W=W, H=H)

        gui.render(surf)
        win.blit(surf, (0,0))
        pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    main()
    pygame.quit()
    pygame.font.quit()