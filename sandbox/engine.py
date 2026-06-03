from body import CelestialBody
from vector import Vector

class Simulation:
    def __init__(self, bodies):
        self.bodies = bodies

    def step(self, dt):
        for i in range(len(self.bodies)):
            for j in range(len(self.bodies)):
                if i != j:
                    distance_vector = self.bodies[i].position - self.bodies[j].position
                    r_squared = distance_vector.magnitude() ** 2
                    G = 6.67430e-11  # m^3 kg^-1 s^-2*10^-11
                    distance = distance_vector.magnitude()
                    distance_vector_normalized = distance_vector / distance

                    if distance < 0.5:
                        # Quantum Repulsion
                        repulsion_strength = 0.01  # A strong repulsive constant
                        force_magnitude = repulsion_strength / (distance ** 2)
                    else:
                        # Original Gravitational Attraction
                        G = 6.67430e-11
                        force_magnitude = -(G * self.bodies[i].mass * self.bodies[j].mass) / (distance ** 2) # Note the negative sign for attraction
                    force = distance_vector_normalized * force_magnitude
                    self.bodies[i].apply_force(force)

        # Update positions using Euler integration
        for body in self.bodies:
            body.position = body.position + body.velocity * dt