//! Bionic Packet Engine v0 — native TCP/UDP packet parser
//!
//! Reads raw Ethernet/IP/TCP/UDP headers from a pcap file or stdin,
//! prints structured JSON. This is the foundation for the Rust-based
//! MCP server that will replace the Python stub.

use std::env;
use std::fs::File;
use std::io::{self, BufReader, Read};
use std::process;

#[derive(Debug)]
struct EthernetHeader {
    dst_mac: [u8; 6],
    src_mac: [u8; 6],
    ethertype: u16,
}

#[derive(Debug)]
struct IPv4Header {
    version: u8,
    ihl: u8,
    total_length: u16,
    protocol: u8,
    src_ip: [u8; 4],
    dst_ip: [u8; 4],
}

#[derive(Debug)]
struct TcpHeader {
    src_port: u16,
    dst_port: u16,
    seq: u32,
    ack: u32,
    data_offset: u8,
}

#[derive(Debug)]
struct UdpHeader {
    src_port: u16,
    dst_port: u16,
    length: u16,
}

fn parse_ethernet(buf: &[u8]) -> Option<(EthernetHeader, &[u8])> {
    if buf.len() < 14 {
        return None;
    }
    let mut dst = [0u8; 6];
    dst.copy_from_slice(&buf[0..6]);
    let mut src = [0u8; 6];
    src.copy_from_slice(&buf[6..12]);
    let ethertype = u16::from_be_bytes([buf[12], buf[13]]);
    Some((
        EthernetHeader {
            dst_mac: dst,
            src_mac: src,
            ethertype,
        },
        &buf[14..],
    ))
}

fn parse_ipv4(buf: &[u8]) -> Option<(IPv4Header, &[u8])> {
    if buf.len() < 20 {
        return None;
    }
    let version = (buf[0] >> 4) & 0xF;
    let ihl = (buf[0] & 0xF) as usize;
    let total_length = u16::from_be_bytes([buf[2], buf[3]]);
    let protocol = buf[9];
    let mut src_ip = [0u8; 4];
    src_ip.copy_from_slice(&buf[12..16]);
    let mut dst_ip = [0u8; 4];
    dst_ip.copy_from_slice(&buf[16..20]);
    let payload_start = ihl * 4;
    if buf.len() < payload_start {
        return None;
    }
    Some((
        IPv4Header {
            version,
            ihl: ihl as u8,
            total_length,
            protocol,
            src_ip,
            dst_ip,
        },
        &buf[payload_start..],
    ))
}

fn parse_tcp(buf: &[u8]) -> Option<(TcpHeader, &[u8])> {
    if buf.len() < 20 {
        return None;
    }
    let src_port = u16::from_be_bytes([buf[0], buf[1]]);
    let dst_port = u16::from_be_bytes([buf[2], buf[3]]);
    let seq = u32::from_be_bytes([buf[4], buf[5], buf[6], buf[7]]);
    let ack = u32::from_be_bytes([buf[8], buf[9], buf[10], buf[11]]);
    let data_offset = (buf[12] >> 4) as usize;
    let payload_start = data_offset * 4;
    if buf.len() < payload_start {
        return None;
    }
    Some((
        TcpHeader {
            src_port,
            dst_port,
            seq,
            ack,
            data_offset: data_offset as u8,
        },
        &buf[payload_start..],
    ))
}

fn parse_udp(buf: &[u8]) -> Option<(UdpHeader, &[u8])> {
    if buf.len() < 8 {
        return None;
    }
    let src_port = u16::from_be_bytes([buf[0], buf[1]]);
    let dst_port = u16::from_be_bytes([buf[2], buf[3]]);
    let length = u16::from_be_bytes([buf[4], buf[5]]);
    Some((
        UdpHeader {
            src_port,
            dst_port,
            length,
        },
        &buf[8..],
    ))
}

fn mac_to_str(m: &[u8; 6]) -> String {
    m.iter()
        .map(|b| format!("{:02x}", b))
        .collect::<Vec<_>>()
        .join(":")
}

fn ip_to_str(ip: &[u8; 4]) -> String {
    format!("{}.{}.{}.{}", ip[0], ip[1], ip[2], ip[3])
}

fn demo() -> Vec<serde_json::Value> {
    let mut results = Vec::new();

    // Synthetic TCP SYN packet (Ethernet + IPv4 + TCP)
    let mut pkt: Vec<u8> = Vec::new();
    pkt.extend_from_slice(&[0x00, 0x0c, 0x29, 0xab, 0xcd, 0xef]);
    pkt.extend_from_slice(&[0x00, 0x50, 0x56, 0xc0, 0x00, 0x08]);
    pkt.extend_from_slice(&[0x08, 0x00]);
    let mut ip = vec![0u8; 20];
    ip[0] = 0x45;
    ip[2..4].copy_from_slice(&56u16.to_be_bytes());
    ip[9] = 6;
    ip[12..16].copy_from_slice(&[192, 168, 1, 100]);
    ip[16..20].copy_from_slice(&[93, 184, 216, 35]);
    pkt.extend_from_slice(&ip);
    let mut tcp = vec![0u8; 20];
    tcp[0..2].copy_from_slice(&50000u16.to_be_bytes());
    tcp[2..4].copy_from_slice(&443u16.to_be_bytes());
    tcp[4..8].copy_from_slice(&1000u32.to_be_bytes());
    tcp[12] = 0x50;
    tcp[13] = 0x02;
    pkt.extend_from_slice(&tcp);

    if let Some((eth, rest)) = parse_ethernet(&pkt) {
        let mut record = serde_json::json!({
            "ethernet": {
                "dst_mac": mac_to_str(&eth.dst_mac),
                "src_mac": mac_to_str(&eth.src_mac),
                "ethertype": format!("0x{:04x}", eth.ethertype),
            }
        });
        if let Some((ip, rest2)) = parse_ipv4(rest) {
            record["ipv4"] = serde_json::json!({
                "src": ip_to_str(&ip.src_ip),
                "dst": ip_to_str(&ip.dst_ip),
                "protocol": ip.protocol,
                "total_length": ip.total_length,
            });
            if ip.protocol == 6 {
                if let Some((tcp, payload)) = parse_tcp(rest2) {
                    record["tcp"] = serde_json::json!({
                        "src_port": tcp.src_port,
                        "dst_port": tcp.dst_port,
                        "seq": tcp.seq,
                        "ack": tcp.ack,
                        "payload_len": payload.len(),
                    });
                }
            }
        }
        results.push(record);
    }

    // UDP DNS query (synthetic)
    let mut pkt2: Vec<u8> = Vec::new();
    pkt2.extend_from_slice(&[0xff, 0xff, 0xff, 0xff, 0xff, 0xff]);
    pkt2.extend_from_slice(&[0x00, 0x11, 0x22, 0x33, 0x44, 0x55]);
    pkt2.extend_from_slice(&[0x08, 0x00]);
    let mut ip2 = vec![0u8; 20];
    ip2[0] = 0x45;
    ip2[2..4].copy_from_slice(&40u16.to_be_bytes());
    ip2[9] = 17;
    ip2[12..16].copy_from_slice(&[10, 0, 0, 1]);
    ip2[16..20].copy_from_slice(&[8, 8, 8, 8]);
    pkt2.extend_from_slice(&ip2);
    let mut udp = vec![0u8; 8];
    udp[0..2].copy_from_slice(&12345u16.to_be_bytes());
    udp[2..4].copy_from_slice(&53u16.to_be_bytes());
    udp[4..6].copy_from_slice(&20u16.to_be_bytes());
    pkt2.extend_from_slice(&udp);
    pkt2.extend_from_slice(&[0x12, 0x34, 0x01, 0x00]);

    if let Some((eth, rest)) = parse_ethernet(&pkt2) {
        let mut record = serde_json::json!({
            "ethernet": {
                "dst_mac": mac_to_str(&eth.dst_mac),
                "src_mac": mac_to_str(&eth.src_mac),
                "ethertype": format!("0x{:04x}", eth.ethertype),
            }
        });
        if let Some((ip, rest2)) = parse_ipv4(rest) {
            record["ipv4"] = serde_json::json!({
                "src": ip_to_str(&ip.src_ip),
                "dst": ip_to_str(&ip.dst_ip),
                "protocol": ip.protocol,
            });
            if ip.protocol == 17 {
                if let Some((udp, payload)) = parse_udp(rest2) {
                    record["udp"] = serde_json::json!({
                        "src_port": udp.src_port,
                        "dst_port": udp.dst_port,
                        "payload_len": payload.len(),
                    });
                }
            }
        }
        results.push(record);
    }

    results
}

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() > 1 && args[1] == "--demo" {
        let results = demo();
        for r in results {
            println!("{}", serde_json::to_string_pretty(&r).unwrap());
        }
        return;
    }

    if args.len() > 1 && args[1] == "--mcp-stdio" {
        println!("{{\"jsonrpc\":\"2.0\",\"id\":0,\"result\":{{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{{\"tools\":{{}}}}}}}}");
        return;
    }

    if args.len() > 1 {
        let path = &args[1];
        match File::open(path) {
            Ok(f) => {
                let mut reader = BufReader::new(f);
                let mut buf = Vec::new();
                if reader.read_to_end(&mut buf).is_ok() && buf.len() >= 14 {
                    if let Some((eth, rest)) = parse_ethernet(&buf) {
                        println!(
                            "Ethernet: {} -> {} (0x{:04x})",
                            mac_to_str(&eth.src_mac),
                            mac_to_str(&eth.dst_mac),
                            eth.ethertype
                        );
                        if eth.ethertype == 0x0800 {
                            if let Some((ip, rest2)) = parse_ipv4(rest) {
                                println!(
                                    "  IPv4: {} -> {} (proto={})",
                                    ip_to_str(&ip.src_ip),
                                    ip_to_str(&ip.dst_ip),
                                    ip.protocol
                                );
                                match ip.protocol {
                                    6 => {
                                        if let Some((tcp, payload)) = parse_tcp(rest2) {
                                            println!(
                                                "    TCP: {} -> {} [SYN={}] payload={}B",
                                                tcp.src_port,
                                                tcp.dst_port,
                                                (tcp.seq > 0) as u8,
                                                payload.len()
                                            );
                                        }
                                    }
                                    17 => {
                                        if let Some((udp, payload)) = parse_udp(rest2) {
                                            println!(
                                                "    UDP: {} -> {} payload={}B",
                                                udp.src_port,
                                                udp.dst_port,
                                                payload.len()
                                            );
                                        }
                                    }
                                    _ => println!("    Protocol {} (no parser)", ip.protocol),
                                }
                            }
                        }
                    }
                }
            }
            Err(e) => {
                eprintln!("Error opening {}: {}", path, e);
                process::exit(1);
            }
        }
        return;
    }

    println!("Bionic Packet Engine v0.1.0");
    println!("Usage:");
    println!("  --demo        Parse synthetic TCP SYN + UDP DNS packets");
    println!("  --mcp-stdio   Announce MCP stdio server");
    println!("  <file>        Parse raw packet bytes from file");
}
