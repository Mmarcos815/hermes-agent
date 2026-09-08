//! Learning Project 01 — Rust hello_world
//!
//! Real, minimal Rust program that:
//! 1. Compiles cleanly with cargo on Windows
//! 2. Outputs "Hello from Rust" + a tiny bit of system info
//! 3. Serves as the foundation for the bionic_packet_engine MCP server

use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    println!("Hello from Rust 1.98.0");
    println!("Args: {:?}", args);
    println!("PID: {}", std::process::id());
    println!("OS: {}", env::consts::OS);
    println!("ARCH: {}", env::consts::ARCH);
    println!("---");
    println!("Next: bionic_packet_engine MCP server in Rust");
}