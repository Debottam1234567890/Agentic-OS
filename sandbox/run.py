from engine import Simulation
from body import CelestialBody
from vector import Vector

# Initialize three-body system in orbital resonance
bodies = [
    CelestialBody(position=Vector(1, 0, 0), velocity=Vector(0, 1, 0), mass=1),
    CelestialBody(position=Vector(-0.5, (3**0.5)/2, 0), velocity=Vector(-(3**0.5)/2, -0.5, 0), mass=1),
    CelestialBody(position=Vector(-0.5, -(3**0.5)/2, 0), velocity=Vector((3**0.5)/2, 0.5, 0), mass=1)
]

simulation = Simulation(bodies)

for step in range(10):
    print(f'\nStep {step+1}:')
    for body in simulation.bodies:
        print(f'Position: {body.position}')
    simulation.step(0.1)