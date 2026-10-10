import time
import Simulation
import Graphing
import Camera
import pygame

population = int(input("\npopulation: "))
hospital_capacity = int(input("hospital capacity: "))
ticks_between_data_points = 4

#set up world
world_settings = Simulation.World_Settings()
world_settings.initial_infected_population = int(input("initial infected population: "))
world_settings.immunity_decay_rate = 1
print("initializing, please wait")
world = Simulation.World(population, hospital_capacity, world_settings)
simulation_data = []

#set up graph
grapher = Graphing.Grapher(world, ticks_between_data_points)

#camera
pygame.init()
screen_size = width, height = 1280, 720
screen = pygame.display.set_mode(screen_size)
camera_settings = Camera.Camera_Settings()
camera_settings.font_size=64
camera = Camera.Camera(screen, world, grapher, camera_settings)

#last update times of world, camera and graph
last_update_times = [time.time(),]*3

print("initialization complete, switch to the pygame window")
#main update loop
while True:
    delta_times = [time.time() - i for i in last_update_times]
    
    #update world at 50 fps * sim speed
    if delta_times[0] > (1/50) / camera.simulation_speed:
        world.tick()

        #collect data
        if not world.paused and world.time % ticks_between_data_points == 0:
            susceptible = len([i for i in world.people if i.alive and not i.infected and i.immunity < 0.5])
            infected = len([i for i in world.people if i.alive and i.infected and not i.being_treated])
            hospitalized = len([i for i in world.people if i.alive and i.being_treated])
            immune = len([i for i in world.people if i.alive and not i.infected and i.immunity > .5])
            dead = len([i for i in world.people if not i.alive])
            simulation_data.append((susceptible, infected, hospitalized, immune, dead))
        last_update_times[0] = time.time()
    
    #update camera at 60 fps
    #(camera is also responsible for user inputs)
    if delta_times[1] > 1/60:
        camera.update()
        last_update_times[1] = time.time()

    #update graph at 10 fps
    if delta_times[2] > 1/10:
        grapher.update(simulation_data)
        last_update_times[2] = time.time()