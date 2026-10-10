from __future__ import annotations
import random
from enum import Enum 
from Vector2D import Vector2D
class Person:
    infected:bool = False
    alive:bool = True
    being_treated:bool = False
    immunity:float = 0
    infection_progress:int = 0
    home:Building
    work:Building
    current_building:Building

    #for rendering
    position:Vector2D
    target_position:Vector2D
    def __init__(self, home:Building, work:Building) -> None:
        self.home = home
        self.work = work
        self.current_building = home
        home.people.append(self)

        self.position = self.current_building.get_random_position_in_building()
        self.target_position = self.position.copy()

    def die(self):
        self.alive = False
        self.current_building.people.remove(self)

    def move(self, target:Building) -> None:
        if target is self.current_building:
            return
        
        self.current_building.people.remove(self)
        self.current_building = target
        target.people.append(self)
        self.target_position = target.get_random_position_in_building()

#types enum
class Building_Types(Enum):
    HOUSE = 0
    HOSPITAL = 1
    WORK = 2
    MISC = 3
    
class Building:
    assigned: int = 0
    people: list[Person]
    capacity: int
    type: int

    #for rendering
    position:Vector2D
    dimensions:Vector2D

    def __init__(self, capacity:int, type:int, position:Vector2D, dimensions:Vector2D) -> None:
        self.capacity = capacity
        self.type = type
        self.people = []

        self.position = position 
        self.dimensions = dimensions

    def get_random_position_in_building(self) -> Vector2D:
        return Vector2D(random.randint(self.position.x, self.position.x + self.dimensions.x), random.randint(self.position.y, self.position.y + self.dimensions.y))
    

class World_Settings:
    #min/max per building capacities
    per_building_capacities:dict[Building_Types:tuple[int,int]] = {
        Building_Types.HOUSE: (2, 6),
        Building_Types.WORK: (5, 15),
        Building_Types.HOSPITAL: (10, 30),
        Building_Types.MISC: (10, 30)
        }

    #lengths in ticks of the phases of the days
    #(work, misc, home)
    day_phase_lengths:tuple[int, int, int] = (40, 30, 30)

    #change for people to go to a misc building instead of going home during the misc phase
    misc_chance:float = 1/2

    #change for an infected person to interact with someone in the same building per frame
    interaction_chance:float = 1/100

    #chance for an infected person to attempt to go to the hosiptal per frame    
    hospital_chance:float = 1/100
    
    initial_infected_population:int = 10
    
    #length of (dormant_stage, infectious_stage, hospital_stage)
    infection_lengths:tuple[int] = (200,200,200)

    immunity_decay_rate:float = .9995

    #below fields only effect rendering

    building_margin = Vector2D(25, 25)

    #min and max full sizes (actually size is scaled down by capacity) 
    building_size_ranges:dict[Building_Types:tuple[int,int]] = {
        Building_Types.HOUSE: (200, 230),
        Building_Types.WORK: (300, 340),
        Building_Types.HOSPITAL: (350, 400),
        Building_Types.MISC: (350, 400),
    }

class World:
    buildings: dict[int, list[Building]]
    people: list[Person]
    paused: bool = True
    
    day_length:int
    time:int = 0
    day:int = 0
    settings:World_Settings
    
    def __init__(self, target_population:int, target_hospital_capacity:int, settings:World_Settings) -> None:
        self.buildings = {}
        for type in Building_Types:
            self.buildings[type] = []
        self.people = []
        self.settings = settings

        #so we only have to calculate this once
        self.day_length = sum(settings.day_phase_lengths)
        
        #initialize the world
        #add misc
        self.add_buildings(Building_Types.MISC, target_population)
        #add hospitals
        self.add_buildings(Building_Types.HOSPITAL, target_hospital_capacity)
        #add work places
        self.add_buildings(Building_Types.WORK, target_population)
        #add houses
        self.add_buildings(Building_Types.HOUSE, target_population)

        for i in range(target_population):
            #pick a random house and work place with an empty spot
            house = random.choice([i for i in self.buildings[Building_Types.HOUSE] if i.capacity > i.assigned])
            work = random.choice([i for i in self.buildings[Building_Types.WORK] if i.capacity > i.assigned])
            
            house.assigned += 1
            work.assigned += 1

            self.people.append(Person(house, work))
        
        #add infected people
        for i in range(settings.initial_infected_population):
            self.people[i].infected = True
            #so initial population start out infectious instead of in the incubation phase
            self.people[i].infection_progress = settings.infection_lengths[0]

    #returns the current phase of the day
    #0 is work, 1 is misc and 2 is home
    def get_current_phase(self) -> int:
        if self.time < self.settings.day_phase_lengths[0]:
            return 0
        elif self.time < self.settings.day_phase_lengths[0] + self.settings.day_phase_lengths[1]:
            return 1
        else:
            return 2
    
    def get_all_buildings(self) -> list[Building]:
        output = []
        [output.extend(i) for i in self.buildings.values()]
        return output
    
    #checks if 2 rectangles intersect
    def intersects(position_1:Vector2D, dimensions_1:Vector2D, position_2:Vector2D, dimensions_2:Vector2D) -> bool:
        
        x_overlap = False
        y_overlap = False

        if position_1.x < position_2.x and position_1.x + dimensions_1.x > position_2.x: x_overlap = True
        elif position_1.x >= position_2.x and position_2.x + dimensions_2.x > position_1.x: x_overlap = True
        if position_1.y < position_2.y and position_1.y + dimensions_1.y > position_2.y: y_overlap = True
        elif position_1.y >= position_2.y and position_2.y + dimensions_2.y > position_1.y: y_overlap = True
            
        return x_overlap and y_overlap
    
    #generates a building position that doesnt overlap
    #ccurrently just generates random positions until it finds one

    #picks a random building to act as a starting point, moves randomly around that building until a valid spot is found
    def get_new_building_position(self, dimensions:Vector2D) -> Vector2D:
        #edge case for first building
        buildings = self.get_all_buildings()
        if len(buildings) == 0:
            return Vector2D.zero()
        
        position = random.choice(buildings).position.copy()
        margin = Vector2D(25, 25)

        while True:
            position = position + Vector2D(random.randint(-dimensions.x, dimensions.x), random.randint(-dimensions.x, dimensions.x))
            if not any(World.intersects(position - margin, dimensions + margin * 2, i.position, i.dimensions) for i in buildings):
                return position

        
                
    #randomly generates new buildings until target capacity is added
    def add_buildings(self, type:int, target_capacity:int) -> None:
        
        min_capacity, max_capacity = self.settings.per_building_capacities[type]
        current_capacity = 0
        while current_capacity < target_capacity:
            added_capacity = random.randint(min_capacity, max_capacity)
            capacity = added_capacity if current_capacity + added_capacity <= target_capacity else max(min_capacity, target_capacity - current_capacity)
            
            #scaled by capacity/max_capacity to make larger buildings bigger
            dimensions = Vector2D(random.randint(*World_Settings.building_size_ranges[type]), random.randint(*World_Settings.building_size_ranges[type]))*(capacity/max_capacity)
            #round to int since get_new_building_position() requires integer positions
            dimensions = Vector2D(round(dimensions.x), round(dimensions.y))
            position = self.get_new_building_position(dimensions)
            self.buildings[type].append(Building(capacity,type, position, dimensions))
            current_capacity += added_capacity
    
    #progresses the simulation by 1 step
    def tick(self) -> None:
        if self.paused:
            return
        
        #update people
        for person in self.people:

            if not person.alive:
                continue

            #infect another person in the same room if not in the "dormant" stage or being treated
            #random chance to "interact" with another person in the same room
            #the other person is then infected based on a formula
            if not person.being_treated and person.infection_progress > self.settings.infection_lengths[0] and random.random() < self.settings.interaction_chance and len(person.current_building.people) > 1:
                other_person = random.choice([i for i in person.current_building.people if not (i is person)])

                #chance to infect a person based on their immunity and this graph
                #https://www.desmos.com/calculator/cron2qblzw
                if random.random() < (1-other_person.immunity)**2:
                    other_person.infected = True
                    other_person.immunity = 0
            
            #progress infections & treatment
            if person.being_treated:
                person.infection_progress -= random.randint(0,1)
                if person.infection_progress == 0:
                    person.infected = False
                    person.immunity = 1
                    person.being_treated = False

            elif person.infected:
                person.infection_progress += random.randint(0,1)

                #die if person has gone through all stages of the infection
                if person.infection_progress > sum(self.settings.infection_lengths):
                    person.die()
                    continue

            #chance to go to hospital if person is in the "hospital" stage and there are hospitals available
            if not person.being_treated and person.infection_progress > sum(self.settings.infection_lengths[:2]):
                hospitals = [i for i in self.buildings[Building_Types.HOSPITAL] if i.capacity > len(i.people)]
                if len(hospitals) > 0 and random.random() < self.settings.hospital_chance:
                    person.move(random.choice(hospitals))
                    person.being_treated = True 

            #move to new location on the first tick of each phase of the day if person is not in hospital
            if not person.being_treated:
                if self.time == 0:
                    person.move(person.work)
                elif self.time == self.settings.day_phase_lengths[0]:
                    #chance to move to a random misc building during misc phase if there a building available
                    #otherwise go home
                    if random.random() < self.settings.misc_chance:
                        person.move(random.choice(self.buildings[Building_Types.MISC]))
                    else:
                        person.move(person.home)
                elif self.time == self.settings.day_phase_lengths[0] + self.settings.day_phase_lengths[1]:
                        person.move(person.home)
            
            #immunity decay
            person.immunity *= self.settings.immunity_decay_rate

            #for rendering
            #moves the person towards their target position
            person.position = Vector2D.lerp(person.position, person.target_position, 0.25)
        #update time
        self.time += 1
        if self.time >= self.day_length:
            self.time = 0
            self.day += 1