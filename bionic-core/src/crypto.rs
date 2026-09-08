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