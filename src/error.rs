use serde_json;
use thiserror;

#[derive(Debug, thiserror::Error)]
pub enum OrigamiError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("Validation error: {0}")]
    Validation(String),
}
