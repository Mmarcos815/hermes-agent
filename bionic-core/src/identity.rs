
use crate::Error;
use serde::{Serialize, Deserialize};
use sha2::{Sha256, Digest};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Identity {
    pub id: String,
    pub public_key: String,
    pub created_at: String,
    pub last_seen: String,
    pub metadata: serde_json::Map<String, serde_json::Value>,
}

impl Identity {
    pub fn new(id: String, public_key: String) -> Self {
        let now = chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true);
        Self {
            id,
            public_key,
            created_at: now,
            last_seen: now.clone(),
            metadata: serde_json::Map::new(),
        }
    }

    pub fn update_last_seen(&mut self) {
        self.last_seen = chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true);
    }
}

pub fn from_seed(seed: &[u8]) -> Result<Self> {
    let hash = Sha256::digest(seed);
    let id = hex::encode(&hash[..16]);
    let public_key = hex::encode(&hash);
    Ok(Self::new(id, public_key))
}
