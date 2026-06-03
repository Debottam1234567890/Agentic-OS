from vector import Vector

class CelestialBody:
    def __init__(self, position, velocity, mass):
        self.position = position
        self.velocity = velocity
        self.mass = mass

    def apply_force(self, force):
        self.velocity += force * (1 / self.mass)

    def __repr__(self):
        return f'CelestialBody(position={self.position}, velocity={self.velocity}, mass={self.mass})'

