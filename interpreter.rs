use pest::Parser;
use pest_derive::Parser;
use std::collections::HashMap;
use rand::Rng;

#[derive(Parser)]
#[grammar = "weavelang.pest"]
struct WeaveParser;

struct WeaveLang {
    model: HashMap<String, f64>,
    vector_model: HashMap<String, Vec<f64>>,
    tension_history: Vec<f64>,
    coherence: f64,
    primitives: HashMap<String, String>,
}

impl WeaveLang {
    fn new() -> Self {
        WeaveLang {
            model: HashMap::new(),
            vector_model: HashMap::new(),
            tension_history: Vec::new(),
            coherence: 0.0,
            primitives: HashMap::new(),
        }
    }

    fn sense(&self, sensor: &str) -> f64 {
        // Placeholder for Godot sensor input
        match sensor {
            "light" => 4.5 + rand::thread_rng().gen_range(-0.5..0.5),
            "proximity_sensor" => 0.0,
            _ => 0.0,
        }
    }

    fn act(&self, action: &str, value: [f64; 2]) {
        // Placeholder for Godot actuator
        println!("Action: {} with value {:?}", action, value);
    }

    fn tension(&self, observed: f64, expected: f64) -> f64 {
        (observed - expected).abs()
    }

    fn drift(&mut self, param: &str, history: &[f64]) -> f64 {
        let base = self.model.get(param).unwrap_or(&0.0);
        let range = if history.is_empty() { 0.5 } else { history.iter().sum::<f64>() / history.len() as f64 * 0.1 };
        base + rand::thread_rng().gen_range(-range..range)
    }

    fn resolve(&mut self, param: &str, new_value: f64, tension: f64) -> bool {
        if tension < 2.0 {
            self.model.insert(param.to_string(), new_value);
            self.coherence = 1.0 / (1.0 + tension);
            true
        } else {
            false
        }
    }

    fn extend_field(&mut self, field: &str, param: &str, value: f64, condition: bool) {
        if condition {
            self.model.insert(format!("{}.{}", field, param), value);
        }
    }

    fn metaweave(&mut self, primitive: &str, action: &str) {
        self.primitives.insert(primitive.to_string(), action.to_string());
        println!("Defined new primitive: {} as {}", primitive, action);
    }

    fn execute(&mut self, code: &str) {
        let pairs = WeaveParser::parse(Rule::program, code).unwrap_or_else(|e| panic!("{}", e));
        for pair in pairs {
            match pair.as_rule() {
                Rule::field => {
                    for inner in pair.into_inner() {
                        if inner.as_rule() == Rule::ident {
                            let field_name = inner.as_str();
                            self.model.insert(format!("{}.created", field_name), 1.0);
                        }
                    }
                }
                Rule::tension => {
                    for inner in pair.into_inner() {
                        if inner.as_rule() == Rule::condition {
                            let parts: Vec<_> = inner.into_inner().collect();
                            let sensor = parts[0].into_inner().next().unwrap().as_str();
                            let op = parts[1].as_str();
                            let param = parts[2].as_str();
                            let observed = self.sense(sensor);
                            let expected = self.model.get(param).unwrap_or(&0.0);
                            let tension = self.tension(observed, *expected);
                            self.tension_history.push(tension);
                            if (op == "<" && observed < *expected) || (op == ">" && observed > *expected) {
                                let action = inner.into_inner().nth(2).unwrap().into_inner();
                                let action_name = action.next().unwrap().as_str();
                                let value: Vec<f64> = action
                                    .next()
                                    .unwrap()
                                    .into_inner()
                                    .map(|v| v.as_str().parse().unwrap())
                                    .collect();
                                self.act(action_name, [value[0], value[1]]);
                            }
                            println!("Tension: {}", tension);
                        }
                    }
                }
                Rule::drift => {
                    let param = pair.into_inner().next().unwrap().as_str();
                    let new_value = self.drift(param, &self.tension_history);
                    println!("Drift: New {} = {}", param, new_value);
                }
                Rule::resolve => {
                    let parts: Vec<_> = pair.into_inner().collect();
                    let sensor = parts[0].into_inner().next().unwrap().into_inner().next().unwrap().as_str();
                    let param = parts[0].into_inner().nth(1).unwrap().as_str();
                    let observed = self.sense(sensor);
                    let new_value = self.drift(param, &self.tension_history);
                    let tension = self.tension(observed, new_value);
                    if self.resolve(param, new_value, tension) {
                        println!("Resolved: Coherence {}", self.coherence);
                    }
                }
                Rule::metaweave => {
                    let parts: Vec<_> = pair.into_inner().collect();
                    let primitive = parts[0].as_str();
                    let action = parts[1].as_str();
                    self.metaweave(primitive, action);
                }
                Rule::extend => {
                    let parts: Vec<_> = pair.into_inner().collect();
                    let field = parts[0].as_str();
                    let param = parts[1].as_str();
                    let value = parts[2].as_str().parse::<f64>().unwrap();
                    let condition = parts[3].as_str().contains("true"); // Simplified condition check
                    self.extend_field(field, param, value, condition);
                }
                Rule::loop => {
                    let parts: Vec<_> = pair.into_inner().collect();
                    let count = parts[0].as_str().parse::<usize>().unwrap();
                    let inner_code = parts[1].as_str();
                    for _ in 0..count {
                        self.execute(inner_code);
                    }
                }
                _ => {}
            }
        }
    }
}

fn main() {
    let mut weavelang = WeaveLang::new();
    weavelang.model.insert("intensity".to_string(), 5.0);
    weavelang.vector_model.insert("position".to_string(), vec![0.0, 0.0]);
    let code = include_str!("light_seeker.weave");
    weavelang.execute(code);
}