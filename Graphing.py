import Simulation
import matplotlib
#the default backend crashes for some weird reason and it was alot easier to
#switch to this than to cater to it's needs
matplotlib.use('Qt5Agg')
from matplotlib import pyplot

class Grapher:
    world: Simulation.World
    lines: list[pyplot.Line2D]
    figure: pyplot.Figure
    axis: pyplot.Axes
    last_data: list[tuple[int, int, int, int, int]]
    ticks_between_data_points: int
    drawing: bool = False
    def __init__(self, world: Simulation.World, ticks_between_data_points:int = 1):
        self.world = world
        self.ticks_between_data_points = ticks_between_data_points
        self.last_data = []

    #since the pyplot steals focus, im adding hotkeys to the pyplot itself
    def on_press(self, event) -> None:
        if event.key == "g":
            self.close()
        
        if event.key == "p":
            self.world.paused = not self.world.paused

    def on_close(self, event) -> None:
        self.close()
    
    def close(self) -> None:
        self.drawing = False
        self.lines = None
        pyplot.close()
    
    #sets up and opens the graph window
    def show(self) -> None:
        if self.drawing:
            return
        
        #set up variables
        self.figure, self.axis = pyplot.subplots()
        self.lines = [self.axis.plot([], [])[0] for i in range(5)]

        #set up axes
        self.axis.set_ylim(0,len(self.world.people))
        self.axis.legend(["Susceptible", "Infected", "Hospitalized", "Immune", "Dead"], loc="upper right")
        self.axis.set_ylabel("people")
        self.axis.set_xlabel("day")

        #set up event listeners
        self.figure.canvas.mpl_connect("close_event", self.on_close)
        self.figure.canvas.mpl_connect("key_press_event", self.on_press)

        #show graph in interactive mode
        pyplot.ion()
        pyplot.show(block = False)
        self.drawing = True

        #initialize graph with data (so that it would display something if the world was paused (since update wouldnt run if would is paused))
        self.update_line_data(self.last_data)
        self.axis.set_xlim(0,self.ticks_between_data_points*len(self.last_data)/self.world.day_length + .5)



    
    #updates the data in the graph
    #takes data in the form [(susceptible, infected, hospitalized, Immune, Dead)]
    def update_line_data(self, data:list[tuple[int, int, int, int, int]]) -> None:
        #just in case
        if self.lines == None:
            return
        
        for index, line in enumerate(self.lines):
            line.set_data([self.ticks_between_data_points * i/self.world.day_length for i in range(len(data))], [i[index] for i in data])
    
    #draws the graph and updates data
    def update(self, data:list[tuple[int, int, int, int, int]],):
        if not self.drawing:
            return

        #required for realtime graphs to work
        #and for key press events to be received
        #will block other parts of the program from running
        #so while a graph is open the simulation will slow down
        #1/100 is arbitrary
        pyplot.pause(1/100)

        #so that graph interacation is possible when the simulation is paused
        if self.world.paused:
            return
        
        self.last_data = data
        self.update_line_data(data)

        self.axis.set_ylim(0,len(self.world.people)+.5)
        self.axis.set_xlim(0,self.ticks_between_data_points*len(data)/self.world.day_length + .5)

        