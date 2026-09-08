
use crate::Error;
use serde::{Serialize, Deserialize};
use chrono::{Utc, DateTime};
use once_cell::sync::Lazy;
use serde_json;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateRecord {
    pub key: String,
    pub value: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub version: u64,
}

impl StateRecord {
    pub fn new(key: String, value: serde_json::Value) -> Self {
        let now = Utc::now();
        Self {
            key,
            value,
            created_at: now,
            updated_at: now,
            version: 1,
        }
    }

    pub fn bump_version(&mut self) {
        self.version += 1;
        self.updated_at = Utc::now();
    }
}

pub struct StateStore {
    base_dir: std::path::PathBuf,
}

impl StateStore {
    pub fn new(base_dir: &std::path::Path) -> Result<Self> {
        std::fs::create_dir_all(base_dir)?;
        Ok(Self {
            base_dir: base_dir.to_path_buf(),
        })
    }

    pub fn get(&self, key: &str) -> Result<Option<serde_json::Value>> {
        let path = self.base_dir.join(format!("{}.json", key));
        if !path.exists() {
            return Ok(None);
        }
        let content = std::fs::read_to_string(&path)
            .map_err(|e| Error::Serialize(format!("Failed to read state file: {e}")))?;
        let record: StateRecord = serde_json::from_str(&content)
            .map_err(|e| Error::Serialize(format!("Failed to parse state file: {e}")))?;
        Ok(Some(record.value))
    }

    pub fn set(&mut self, key: String, value: serde_json::Value) -> Result<()> {
        let mut record = StateRecord::new(key.clone(), value.clone())?;
        let path = self.base_dir.join(format!("{}.json", key));
        let json = serde_json::to_string_pretty(&record)
            .map_err(|e| Error::Serialize(format!("Failed to serialize state: {e}")))?;
        std::fs::write(&path, json)
            .map_err(|e| Error::Serialize(format!("Failed to write state file: {e}")))?;
        Ok(())
    }

    pub fn increment_version(&mut self, key: &str) -> Result<()> {
        let path = self.base_dir.join(format!("{}.json", key));
        if !path.exists() {
            return Err(Error::Serialize(format!("State key not found: {key}")));
        }
        let content = std::fs::read_to_string(&path)
            .map_err(|e| Error::Serialize(format!("Failed to read state file: {e}")))?;
        let mut record: StateRecord = serde_json::from_str(&content)
            .map_err(|e| Error::Serialize(format!("Failed to parse state file: {e}")))?;
        record.bump_version();
        let json = serde_json::to_string_pretty(&record)
            .map_err(|e| Error::Serialize(format!("Failed to serialize state: {e}")))?;
        std::fs::write(&path, json)
            .map_err(|e| Error::Serialize(format!("Failed to write state file: {e}")))?;
        Ok(())
    }
}
