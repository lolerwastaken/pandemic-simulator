import sys, pygame
import pygame.locals
import Simulation
import Graphing
from Vector2D import Vector2D

class Camera_Settings:
    building_colors:dict[Simulation.Building_Types, tuple[int, int, int]] = {
        Simulation.Building_Types.HOUSE: (217,217,217),
        Simulation.Building_Types.HOSPITAL: (255,191,186),
        Simulation.Building_Types.WORK: (186,234,255),
        Simulation.Building_Types.MISC: (255,222,186)
    }
    #healthy color, (dying) sick color. immune color
    people_colors:tuple[tuple[int,int,int], tuple[int,int,int]] = ((255,255,255), (0,255,0), (128,0,128))

    building_border_thickness: float = 5

    people_border_thickness: float = 5
    person_radius:float = 20

    speed: float = 25
    zoom_speed: float = .1

    font_size: int = 32

class Camera:
    settings:Camera_Settings
    screen:pygame.Surface
    screen_size:Vector2D
    font:pygame.font.Font

    world:Simulation.World
    #this field is only used externally in main.py to dynamically adjust the simulation speed
    simulation_speed:float = 1.
    grapher:Graphing.Grapher

    position: Vector2D
    follow_target:Simulation.Person = None
    zoom: float = 1
    show_ui: bool = True
    show_controls: bool = False

    controls_image: pygame.Surface

    def color_lerp(color_a:tuple[int,int,int], color_b:tuple[int,int,int], t:float) -> tuple[int, int, int]:
        r1, g1, b1 = color_a
        r2, g2, b2 = color_b

        r = (r2 - r1)*t + r1
        g = (g2 - g1)*t + g1
        b = (b2 - b1)*t + b1

        return (round(r), round(g), round(b))


    def __init__(self, screen: pygame.Surface, world:Simulation.World, grapher:Graphing.Grapher, settings:Camera_Settings):
        self.world = world
        self.grapher = grapher
        self.screen = screen
        self.settings = settings
        self.position = Vector2D.zero()
        self.screen_size = Vector2D(*screen.get_size())
        self.font = pygame.font.Font(size=settings.font_size)
        self.controls_image = pygame.image.load("controls.png")
    
    def update(self) -> None:
        #stop following dead people
        if self.follow_target != None and not self.follow_target.alive:
            self.follow_target = None

        self.handle_inputs()
        self.render()

    def handle_inputs(self) -> None:
        #keyboard inputs
        speed = self.settings.speed / self.zoom
        zoom_speed = self.settings.zoom_speed * self.zoom

        keys = pygame.key.get_pressed()
        if keys[pygame.locals.K_LEFT] or keys[pygame.locals.K_a]:
            self.position.x -= speed
        if keys[pygame.locals.K_RIGHT] or keys[pygame.locals.K_d]:
            self.position.x += speed
        if keys[pygame.locals.K_UP] or keys[pygame.locals.K_w]:
            self.position.y -= speed
        if keys[pygame.locals.K_DOWN] or keys[pygame.locals.K_s]:
            self.position.y += speed

        if keys[pygame.locals.K_EQUALS] or keys[pygame.locals.K_e]:
            self.zoom += zoom_speed
        if keys[pygame.locals.K_MINUS] or keys[pygame.locals.K_q]:
            self.zoom -= zoom_speed
        
        #mouse inputs
        dx, dy = pygame.mouse.get_rel()
        if pygame.mouse.get_pressed()[0]:
            #mouse movement
            self.position.x -= dx / self.zoom
            self.position.y -= dy / self.zoom

        
        #event handlers
        for event in pygame.event.get():
            #exit program
            if event.type == pygame.QUIT: sys.exit()

            #middle mouse to set follow target
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
                if self.follow_target != None:
                    self.follow_target = None
                else:
                    mouse_position = self.inverse_project(Vector2D(*pygame.mouse.get_pos()))
                    for person in self.world.people:
                        if (person.position - mouse_position).length() < self.settings.person_radius * self.zoom:
                            self.follow_target = person
                            break
            
            #right click to pause
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.world.paused = not self.world.paused
            
            #mouse zooming
            if event.type == pygame.MOUSEWHEEL:
                self.zoom += event.y * zoom_speed
            
            #keyboard hotkeys for control
            if event.type == pygame.KEYDOWN:
                match(event.key):
                    #g to open graph
                    case pygame.locals.K_g:
                        if self.grapher.drawing:
                            self.grapher.close()
                        else:
                            self.grapher.show()
                    
                    #p to pause
                    case pygame.locals.K_p:
                        self.world.paused = not self.world.paused
                    
                    #change sim speeds with [ and ]
                    case pygame.locals.K_LEFTBRACKET:
                        self.simulation_speed /= 2
                    
                    case pygame.locals.K_RIGHTBRACKET:
                        self.simulation_speed *= 2
                    
                    #hide ui
                    case pygame.locals.K_TAB:
                        self.show_ui = not self.show_ui

                    #recenter camera
                    case pygame.locals.K_SPACE:
                        self.position = Vector2D.zero()
                        self.zoom = 1
                    
                    #display controls
                    case pygame.locals.K_c:
                        self.show_controls = not self.show_controls
            

        #clamp sim speed:
        if self.simulation_speed < .5:
            self.simulation_speed = .5
        elif self.simulation_speed > 32:
            self.simulation_speed = 32.
        
        #clamp zoom
        if self.zoom < 0.1:
            self.zoom = 0.1
        elif self.zoom > 10:
            self.zoom = 10
        
        #follow
        if self.follow_target != None:
            self.position = self.follow_target.position - self.screen_size/2
    
    def project(self, position:Vector2D) -> Vector2D:
        return ((position - self.position) - self.screen_size/2) * self.zoom + self.screen_size/2
    
    def inverse_project(self, position:Vector2D) -> Vector2D:
        return ((position - self.screen_size/2)) * (1/self.zoom) + self.screen_size/2 + self.position
    
    def draw_ui(self) -> None:
        #render day
        day_text = self.font.render(f"day:{self.world.day}", True, (0, 0, 0), (255,255,255))
        self.screen.blit(day_text, day_text.get_rect())

        #render current phase
        phase_text = self.font.render(f"phase: {["work", "misc", "home"][self.world.get_current_phase()]}", True, (0, 0, 0), (255,255,255))
        phase_rect = phase_text.get_rect(y=self.settings.font_size)
        self.screen.blit(phase_text, phase_rect)
        
        #render current speed (or pause)
        if self.world.paused:
            speed_text = self.font.render("Paused", True, (0, 0, 0), (255,255,255))
        else:
            speed_text = self.font.render(f"{self.simulation_speed}x", True, (0, 0, 0), (255,255,255))
        speed_rect = speed_text.get_rect()
        speed_rect.right = self.screen_size.x
        self.screen.blit(speed_text, speed_rect)

        #render follow target statistics
        if self.follow_target != None:
            #y coordinate of spot above the follow target
            above_position = self.screen_size.y/2 - (self.settings.font_size/2 + self.settings.person_radius)*self.zoom 

            if self.follow_target.infected:
                if self.follow_target.infection_progress < self.world.settings.infection_lengths[0]:
                    infection_stage = 0
                elif self.follow_target.infection_progress < self.world.settings.infection_lengths[0] + self.world.settings.infection_lengths[1]:
                    infection_stage = 1
                else:
                    infection_stage = 2

                infection_stage_text = self.font.render(f"stage: {["dormant", "infectious", "hospital"][infection_stage]}", True, (0, 0, 0), (255,255,255))
                infection_stage_rect = infection_stage_text.get_rect(center = (self.screen_size.x//2, above_position - 2*self.settings.font_size))
                self.screen.blit(infection_stage_text, infection_stage_rect)

            infection_progress = self.follow_target.infection_progress/sum(self.world.settings.infection_lengths)
            infection_text = self.font.render(f"infection: {round(infection_progress*100,2)}%", True, (0, 0, 0), (255,255,255))
            infection_text_rect = infection_text.get_rect(center = (self.screen_size.x//2, above_position - self.settings.font_size))
            self.screen.blit(infection_text, infection_text_rect)

            immunity = self.follow_target.immunity
            immunity_text = self.font.render(f"immunity: {round(immunity*100,2)}%", True, (0, 0, 0), (255,255,255))
            immunity_text_rect = immunity_text.get_rect(center = (self.screen_size.x//2, above_position))
            self.screen.blit(immunity_text, immunity_text_rect)
        
        #render controls image
        if self.show_controls:
            controls_rect = self.controls_image.get_rect(center = (self.screen_size.x//2, self.screen_size.y//2))
            pygame.draw.rect(self.screen, (0,0,0), controls_rect.inflate(10,10))
            self.screen.blit(self.controls_image, controls_rect)

    def draw_people(self) -> None:
        for person in self.world.people:
            if not person.alive:
                continue 
            screen_x, screen_y = self.screen.get_size()
            position = self.project(person.position)
            radius = self.settings.person_radius * self.zoom
            border_radius = self.settings.people_border_thickness * self.zoom

            #get color
            if person.infected:
                #number from 0 to 1 representing how infected the person it
                infection_progress = person.infection_progress / sum(self.world.settings.infection_lengths)
                color = Camera.color_lerp(self.settings.people_colors[0], self.settings.people_colors[1], infection_progress)
            else:
                color = Camera.color_lerp(self.settings.people_colors[0], self.settings.people_colors[2], person.immunity)
            if position.x + radius < 0 or position.x - radius > screen_x:
                continue
            if position.y + radius < 0 or position.y - radius > screen_y:
                continue

            pygame.draw.circle(self.screen, (0, 0, 0), (position.x, position.y), radius + border_radius)
            pygame.draw.circle(self.screen, color, (position.x, position.y), radius)
            

    def draw_buildings(self) -> None:
        for building in self.world.get_all_buildings():
            screen_x, screen_y = self.screen.get_size()
            position = self.project(building.position)
            dimensions = building.dimensions * self.zoom
            border_thickness = Vector2D(self.settings.building_border_thickness,self.settings.building_border_thickness) * self.zoom
            
            #dont render off screen buildings
            if position.x < -dimensions.x or position.x > screen_x:
                continue
            if position.y < -dimensions.y or position.y > screen_y:
                continue

            #draw border
            pygame.draw.rect(self.screen, (0,0,0), pygame.Rect(position.x - border_thickness.x, position.y - border_thickness.y, dimensions.x + border_thickness.x*2, dimensions.y + border_thickness.y*2))
            pygame.draw.rect(self.screen, self.settings.building_colors[building.type], pygame.Rect(position.x, position.y, dimensions.x, dimensions.y))

    def render(self) -> None:
        self.screen.fill((5 * 16 + 15,7 * 16 + 2,7 * 16 + 4))

        self.draw_buildings()
        self.draw_people()
        
        if self.show_ui:
            self.draw_ui()

        pygame.display.update()