import pygame
from gui import *
from space import *
from display import Display

pygame.init()
pygame.font.init()

win = Display(800,600)
surf = pygame.Surface((win.w,win.h), pygame.SRCALPHA)
fps = 30
running = True
clock = pygame.time.Clock()

win.create("Celestia", load_texture("logo.png"))
UIElement.init(W=win.w, H=win.h)

first, second = Body((win.w//2-148,win.h//2+10), 1), Body((win.w//2,win.h//2-10), 3.32954355178996e5)
first.vel = np.array([0,29.78*1e-6*86400], dtype=np.float64)
space = Space([first,second], tick_time=1)

gui = UI()
gui.add_widget(PlanetUI(win.w,win.h))
gui.add_widget(TimeUI(win.w,win.h))
gui.add_widget(OptionsMenu(win.w,win.h))
gui.add_widget(BodyHandlerUI(win.w, win.h))

# MAIN GAME LOOP
while running:
    clock.tick(fps)
    mouse_vel = pygame.mouse.get_rel() # mouse velocity
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not gui.is_on_ui(mouse_pos): # if the click wasn't on the time ui
                    loaded_body = space.get_body(mouse_pos) # get the body in the position clicked
                    space.highlight([loaded_body])
                    gui.get_by_type(PlanetUI).log_body(loaded_body, mouse_pos) # update the planet ui with the selected body
        
        if event.type == TIME_UPDATE_EVENT:
            space.tick_time = gui.get_by_type(TimeUI).get_time_rate()
        elif event.type == GRAPHICS_UPDATE_EVENT:
            if win.get_size() != tuple(event.new_size) or event.fullscreen != win.fullscreen:
                new_win_size = event.new_size
                gui.on_window_resize(win.w, win.h, new_win_size[0], new_win_size[1])
                win.on_resize(new_win_size[0], new_win_size[1], event.fullscreen)
                UIElement.init(win.w, win.h)
                space.on_window_resize(w, h)
                surf = pygame.Surface(new_win_size) # reinitialize the main surface
            win.set_brightness(event.new_brightness)
            space.renders_field = event.field_rendered
        elif event.type == SPACE_SAVE_EVENT:
            space.save(event.space_name)
        elif event.type == SPACE_LOAD_EVENT:
            space.load(event.space_name)
            gui.get_by_type(TimeUI).set_time_passed(space.time_passed) # make sure to update the gui
        elif event.type == BODY_ADD_EVENT:
            new_body = Body(mouse_pos, 1)
            space.bodies.append(new_body)
            gui.get_by_type(PlanetUI).log_body(new_body, mouse_pos=mouse_pos, dragged=True)
        elif event.type == BODY_REMOVE_EVENT:
            # only one planet is selected
            if gui.get_by_type(PlanetUI).enabled:
                bodies = [gui.get_by_type(PlanetUI).body]
                gui.get_by_type(PlanetUI).enabled = False
            else:
                bodies = space.get_highlighted()
                # if no bodies have been selected just cast a message
                if len(bodies) == 0:
                    UIElement.popup_msg.cast("No body selected!", 3, 0.4)
                    continue
            
            msg = 'Body removed!' if len(bodies) == 1 else 'Bodies removed!'
            UIElement.popup_msg.cast(msg, 3, 0.4)
            space.remove_bodies(bodies)


        elif event.type == BODIES_SELECT_EVENT:
            x,y = event.pos
            w,h = event.size
            bodies = space.get_bodies_in_area(x,y,w,h) # get the bodies
            space.highlight(bodies)
            gui.get_by_type(BodyHandlerUI).select_bodies(bodies) # enable the multiple selection ui
            if len(bodies) != 1:
                gui.get_by_type(PlanetUI).enabled = False # disable the planet UI
            else:
                gui.get_by_type(PlanetUI).log_body(bodies[-1])

        gui.handle_event(event, mouse_pos=mouse_pos, mouse_vel=mouse_vel)

    surf.fill((0,0,0))
    if gui.get_by_type(TimeUI).is_time_enabled():
        space.update()
        gui.update()

    space.render(surf, win.w, win.h)
    gui.render(surf)

    win.render(surf)
    pygame.display.flip()

space.save('autosave')

pygame.quit()
pygame.font.quit()