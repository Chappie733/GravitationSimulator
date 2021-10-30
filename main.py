import pygame
from gui import *
from space import *
import os

W,H = 800,600
BACKGROUND_COLOR = (0,0,0)

def main():
    GUIElement.init_font()
    font = pygame.font.SysFont('Verdana Bold Italic', 30)

    win = pygame.display.set_mode((W,H))
    pygame.display.set_icon(pygame.image.load(os.path.join('res', 'logo.png')))
    surf = pygame.Surface((W,H))
    fps = 60
    running = True
    clock = pygame.time.Clock()

    pygame.display.set_caption("Gravity")

    first, second = Body((W//2-148,H//2+10), 1), Body((W//2,H//2-10), 3.32954355178996e5)
    first.vel = np.array([0,29.78*1e-6*86400], dtype=np.float64)
    space = Space([first,second], tick_time=1)

    gui = GUI()
    gui.add_widget(PlanetGUI(W,H))

    days = 0

    while running:
        clock.tick(fps)
        mouse_vel = pygame.mouse.get_rel() # mouse velocity

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    space.on_click()
                elif event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    loaded_body = space.get_body(mouse_pos)
                    gui.widgets[0].log_body(loaded_body, mouse_pos)

            gui.handle_event(event, mouse_vel=mouse_vel)
    
        surf.fill(BACKGROUND_COLOR)
        space.update()
        space.render(surf)

        days += 1
        time_text = font.render(f"Giorni passati: {days}", False, (0,255,255))

        space.render_grav_field(surf, margin=75)
        
        gui.render(surf)
        surf.blit(time_text, (10,10))
        win.blit(surf, (0,0))
        pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    main()
    pygame.quit()
    pygame.font.quit()