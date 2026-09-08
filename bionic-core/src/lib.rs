//! Bionic Core — foundational primitives for the bionic daughter agent.
//! 
//! Provides cryptographic primitives, state management, and serialization
//! used across all bionic ecosystem components.
//! 
//! THERES ALWAYS A WAY — modular, replaceable implementations.

#![warn(missing_docs)]
#![cfg_attr(not(feature = "std"), no_std)]

pub mod crypto;
pub mod state;
pub mod error;
pub mod identity;

// Version string for the bionic-core crate
pub const VERSION: &str = "0.1.0";

// Error type for bionic-core operations
#[derive(thiserror::Error, Debug)]
pub enum Error {
    #[error("Cryptographic error: {0}")]
    Crypto(#[from] crypto::Error),

    #[error("State management error: {0}")]
    State(#[from] state::Error),

    #[error("Identity error: {0}")]
    Identity(#[from] identity::Error),

    #[error("Serialization error: {0}")]
    Serialize(String),

    #[error("Configuration error: {0}")]
    Config(String),
}

pub type Result<T> = std::result::Result<T, Error>;

/// Cryptographic primitives for the bionic ecosystem
pub mod crypto {
    use crate::Error;
    use sha2::{Sha256, Digest};
    use hexnut::{FromHex, ToHex};
    use base64::{Engine, engine::general_purpose};
    use rand::Rng;

    /// SHA-256 hash of bytes
    pub fn hash_sha256(data: &[u8]) -> [u8; 32] {
        let mut hasher = Sha256::new();
        hasher.update(data);
        let result = hasher.finalize();
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&result);
        arr
    }

    /// SHA-256 hash of string, returns hex
    pub fn hash_sha256_hex(data: &str) -> String {
        let hash = hash_sha256(data.as_bytes());
        hex::encode(hash)
    }

    /// Base64 encode bytes
    pub fn base64_encode(data: &[u8]) -> String {
        let engine = base64::engine::GeneralPurpose::new();
        engine.encode(data)
    }

    /// Base64 decode string
    pub fn base64_decode(encoded: &str) -> Result<Vec<u8>> {
        let engine = base64::engine::GeneralPurpose::new();
        engine.decode(encoded).map_err(|e| Error::Serialize(format!("Base64 decode error: {e}")))
    }

    /// Generate a random 32-byte (256-bit) key
    pub fn generate_key() -> [u8; 32] {
        let mut rng = rand::thread_rng();
        let mut key = [0u8; 32];
        for byte in &mut key {
            *byte = rng.gen();
        }
        key
    }

    /// Error type for crypto module
    #[derive(thiserror::Error, Debug)]
    pub enum Error {
        #[error("Invalid hex string")]
        InvalidHex(#[source] hexnut::error::Error),

        #[error("Invalid base64 string")]
        InvalidBase64(#[source] base64::DecodeError),
    }

    pub type CryptoResult<T> = std::result::Result<T, Error>;
}

/// State management primitives
pub mod state {
    use crate::Error;
    use serde::{Serialize, Deserialize};
    use chrono::{Utc, DateTime};
    use once_cell::sync::Lazy;
    use serde_json;

    /// Persistent state record with timestamp
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

    /// State store using JSON files
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
}

/// Identity management
pub mod identity {
    use crate::Error;
    use serde::{Serialize, Deserialize};
    use sha2::{Sha256, Digest};

    /// Bionic agent identity
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

    /// Generate a deterministic identity from seed
    pub fn from_seed(seed: &[u8]) -> Result<Self> {
        let hash = Sha256::digest(seed);
        let id = hex::encode(&hash[..16]);
        let public_key = hex::encode(&hash);
        Ok(Self::new(id, public_key))
    }
}