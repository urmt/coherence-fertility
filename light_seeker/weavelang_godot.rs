use godot::prelude::*;
use godot::engine::{Node3D, Node3DVirtual, PointLight3D};
use crate::interpreter::WeaveLang;

struct WeaveLangExtension;

#[gdextension]
unsafe impl ExtensionLibrary for WeaveLangExtension {}

#[derive(GodotClass)]
#[class(base=Node3D)]
struct WeaveLangNode {
    base: Base<Node3D>,
    interpreter: WeaveLang,
    light: Option<Gd<PointLight3D>>,
}

#[godot_api]
impl Node3DVirtual for WeaveLangNode {
    fn init(base: Base<Node3D>) -> Self {
        WeaveLangNode {
            base,
            interpreter: WeaveLang::new(),
            light: None,
        }
    }

    fn ready(&mut self) {
        // Find light node in Godot scene
        if let Some(light) = self.base.get_node_as::<PointLight3D>("Light") {
            self.light = Some(light);
        }
    }

    fn physics_process(&mut self, delta: f64) {
        let code = include_str!("light_seeker.weave");
        self.interpreter.execute(code);

        // Update position in Godot
        let position = self.interpreter.vector_model.get("position").unwrap_or(&vec![0.0, 0.0]);
        self.base.set_position(Vector3::new(position[0] as f32, position[1] as f32, 0.0));
    }
}

#[godot_api]
impl WeaveLangNode {
    #[func]
    fn sense_light(&self) -> f64 {
        if let Some(light) = &self.light {
            let light_pos = light.get_position();
            let robot_pos = self.base.get_position();
            let distance = (light_pos - robot_pos).length();
            (10.0 - distance as f64).max(0.0) // Intensity decreases with distance
        } else {
            0.0
        }
    }
}
