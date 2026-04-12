use crate::datastructures::BuildFile;
use crate::error::OrigamiError;
use semver;
use serde;
use serde_json;
use serde_json::Value;
use std::path::PathBuf;

pub struct BuildLoader {
    path: PathBuf,
    schema: Value,
    raw_data: Value,
    build: BuildFile,
}

impl BuildLoader {
    pub fn new(path: PathBuf) -> Result<Self, OrigamiError> {
        let raw_schema = std::fs::read_to_string("../assets/build_schema.json").unwrap();
        let schema_value: Value = serde_json::from_str(&raw_schema).unwrap();

        let raw_build_file = std::fs::read_to_string(&path).unwrap();
        let build_file_value: Value = serde_json::from_str(&raw_build_file).unwrap();

        // Validate json:
        let validator = jsonschema::validator_for(&schema_value).unwrap();
        validator.validate(&build_file_value).unwrap();

        let errors: Vec<_> = validator.iter_errors(&build_file_value).collect();
        if !errors.is_empty() {
            // handle errors
        }

        let build: BuildFile = serde_json::from_value(build_file_value.clone())?;

        Ok(Self {
            path,
            schema: schema_value,
            raw_data: build_file_value,
            build,
        })
    }

    fn load_schema(&self, path: PathBuf) -> Value {
        let raw = std::fs::read_to_string(&path).unwrap();
        let value: Value = serde_json::from_str(&raw).unwrap();
        value
    }

    pub fn print_build_config(&self) -> () {
        println!("Config Name: {}", self.build.name);
        println!("Config Path: {}", self.build.path.to_str().unwrap());
        println!("Description: {}", self.build.description);
        println!("Version: {}", self.build.version);
        println!("Install:");
        let installation = &self.build.install;
    }
}
