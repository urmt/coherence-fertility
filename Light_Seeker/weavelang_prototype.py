import numpy as np
import random

# Simulated virtual world (e.g., Godot-like environment)
class VirtualWorld:
    def __init__(self):
        self.light_position = np.array([10.0, 10.0])  # Target light source
        self.robot_position = np.array([0.0, 0.0])    # Robot starts at origin

    def sense_light(self, position):
        # Simulate light intensity decreasing with distance
        distance = np.linalg.norm(self.light_position - position)
        return max(0, 10 - distance)  # Intensity drops off with distance

    def move_robot(self, direction):
        self.robot_position += direction
        return self.robot_position

# WeaveLang core constructs
class WeaveLang:
    def __init__(self, world):
        self.world = world
        self.model = {"expected_light": 5.0}  # Initial internal model
        self.tension_threshold = 2.0
        self.coherence = 0.0

    def sense(self, sensor_type):
        if sensor_type == "light":
            return self.world.sense_light(self.world.robot_position)
        return 0.0

    def act(self, action_type, value):
        if action_type == "move":
            return self.world.move_robot(value)
        return self.world.robot_position

    def tension(self, observed, expected):
        # Quantify mismatch between observation and expectation
        return abs(observed - expected)

    def drift(self, param, range=0.5):
        # Explore adjustments to the model
        return param + random.uniform(-range, range)

    def resolve(self, tension_value, param_name, new_value):
        # Update model if tension is reduced
        if tension_value < self.tension_threshold:
            self.model[param_name] = new_value
            self.coherence = 1 / (1 + tension_value)  # Higher coherence when tension is low
            return True
        return False

    def run_cycle(self):
        # Tension-Drift-Resolution cycle
        observed_light = self.sense("light")
        expected_light = self.model["expected_light"]
        tension_value = self.tension(observed_light, expected_light)
        print(f"Observed: {observed_light:.2f}, Expected: {expected_light:.2f}, Tension: {tension_value:.2f}")

        if tension_value > self.tension_threshold:
            # Drift: Explore a new expected value
            new_expected = self.drift(expected_light)
            new_tension = self.tension(observed_light, new_expected)
            print(f"Drift: Trying new expected value {new_expected:.2f}, New Tension: {new_tension:.2f}")

            # Resolution: Update model if tension decreases
            if self.resolve(new_tension, "expected_light", new_expected):
                print(f"Resolved: Model updated, Coherence: {self.coherence:.2f}")
            else:
                print("Resolution failed, tension too high")

        # Act: Move toward light based on current model
        direction = (self.world.light_position - self.world.robot_position) * 0.1
        self.act("move", direction)
        print(f"Robot Position: {self.world.robot_position}\n")

# Main execution
world = VirtualWorld()
weave = WeaveLang(world)

for _ in range(5):  # Simulate 5 cycles
    weave.run_cycle()
