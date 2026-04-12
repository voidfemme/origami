use serde::Deserialize;
use serde_json::Value;
use std::path::PathBuf;

// -- HEALTH CLASSES --
pub struct ComponentHealth {
    name: String,
    passing: Option<Vec<String>>,
    failing: Option<Vec<String>>,
}

impl ComponentHealth {
    pub fn is_healthy(&self) -> bool {
        self.failing.as_ref().map_or(true, |v| v.is_empty())
    }
}

pub struct RiceHealth {
    name: String,
    components: Option<Vec<ComponentHealth>>,
}

impl RiceHealth {
    pub fn is_healthy(&self) -> bool {
        let mut is_healthy = true;
        self.components
            .as_ref()
            .map_or(true, |v| v.iter().all(|c| c.is_healthy()))
    }
}

// -- CONFLICT CLASSES --
pub struct TargetConflict {
    component_a: String,
    component_b: String,
    target_path: PathBuf,
}

pub struct EnvConflict {
    component_a: String,
    component_b: String,
    var_name: String,
    value_a: String,
    value_b: String,
}

pub struct RiceConflicts {
    target_conflicts: Option<Vec<TargetConflict>>,
    env_conflicts: Option<Vec<EnvConflict>>,
}

impl RiceConflicts {
    pub fn has_conflicts(&self) -> bool {
        self.target_conflicts
            .as_ref()
            .map_or(false, |v| !v.is_empty())
            || self.env_conflicts.as_ref().map_or(false, |v| !v.is_empty())
    }
}

#[allow(dead_code)]
pub struct ConflictResolution {
    // stub class
}

// -- BUILD CLASSES --
#[derive(Deserialize)]
pub struct SymlinkOp {
    symlink_type: String,
    source: PathBuf,
    target: PathBuf,
}

#[derive(Deserialize)]
pub struct InstallList {
    linux: Option<Vec<SymlinkOp>>,
    macos: Option<Vec<SymlinkOp>>,
    termux: Option<Vec<SymlinkOp>>,
}

#[derive(Deserialize)]
pub struct FontDependency {
    name: String,
    required: bool,
}

#[derive(Deserialize)]
pub struct ProgramDependency {
    name: String,
    version: String,
    required: bool,
    notes: String,
}

#[derive(Deserialize)]
pub struct ConfigDependency {
    name: String,
    path: PathBuf,
    required: bool,
}

#[derive(Deserialize)]
pub struct EnvDependency {
    name: String,
    value: String,
    required: bool,
}

#[derive(Deserialize)]
pub struct DependencyList {
    programs: Option<Vec<ProgramDependency>>,
    configs: Option<Vec<ConfigDependency>>,
    paths: Option<Vec<PathBuf>>,
    fonts: Option<Vec<FontDependency>>,
    env: Option<Vec<EnvDependency>>,
}

#[derive(Deserialize)]
pub struct RepoUpstream {
    repo: String,
    branch: String,
}

#[derive(Deserialize)]
pub struct InstallHooks {
    pre_install: Option<Vec<String>>,
    post_install: Option<Vec<String>>,
    pre_uninstall: Option<Vec<String>>,
    post_uninstall: Option<Vec<String>>,
}

#[derive(Deserialize)]
pub struct BuildFile {
    pub path: PathBuf,
    pub name: String,
    pub description: String,
    pub version: String,
    pub install: InstallList,
    pub deps: DependencyList,
    pub upstream: RepoUpstream,
    pub hooks: InstallHooks,
    pub notes: String,
    pub raw_json: Value,
}
