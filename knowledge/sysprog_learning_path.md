# ===========================================================================
# SYSTEMS PROGRAMMING LEARNING PATH — L2 → L4
# ===========================================================================
# From: programming_lang_self_audit.md (Systems Programming: L2 → Target L4)
# Date: 2026-08-19
# Status: Active learning plan

## NOTE: UMBRELLA SKILL

"Systems programming" is NOT a single language. It is the practice of
programming close to the hardware/OS — manual resource management,
performance-critical code, infrastructure software.

This skill spans C, C++, and Rust. The daughter must define what this
skill covers and how it relates to the individual language skills.

Progress in Systems Programming depends on progress in C, C++, and Rust.
You CANNOT be good at systems programming without being good at at least
one of these languages.

## CURRENT STATE (HONEST)

- Understand what "systems programming" means conceptually
- Explain memory layout, CPU caches, branch prediction at a high level
- Read C code (pointers, memory management, structs)
- Understand linking conceptually (static vs dynamic, symbols, ABI)
- CANNOT write systems software (network servers, database engines, file systems)
- CANNOT use GDB/LLDB fluently for debugging
- CANNOT use valgrind, sanitizers, perf, strace, ltrace in practice
- CANNOT understand virtual memory, paging, mmap in depth
- CANNOT use system calls directly in programs
- CANNOT understand the OS at a deep level (VFS, scheduling, interrupts)

## TARGET: L4 (Proficient)

Can write systems software in C/Rust: network servers, database engines,
file systems, container runtimes, language runtimes. Understands the OS
at a deep level: VFS, scheduling, interrupts, virtual memory internals.
Can profile and optimize systems code. Can read kernel code for relevant
subsystems. Can use advanced debugging tools (ftrace, eBPF, systemtap).

================================================================================
PHASE 1: L2 → L3 (Weeks 1-6, building the foundation)
================================================================================

### GOAL
Go from "understands concepts at a high level" to "understands the OS
and hardware at a practical level, can read and write systems-level C,
can use debugging and profiling tools."

### WHAT TO LEARN

1. **Systems Programming Mindset**
   - Programming close to the hardware/OS
   - Manual resource management (no GC, no RAII — you manage it)
   - Performance-critical code: every allocation, every system call matters
   - Infrastructure software: what it is and why it's hard
   - The relationship between high-level code and what the machine does

2. **Memory Hierarchy and Performance**
   - CPU caches: L1, L2, L3 — what they are, how they work
   - Cache lines (typically 64 bytes): the unit of memory transfer
   - Temporal and spatial locality — why data layout matters
   - Cache misses: what they cost, why they're expensive
   - Branch prediction: how it works, what misprediction costs
   - Instruction pipeline: what it is, why ordering matters
   - False sharing: when threads fight over cache lines
   - TLB (Translation Lookaside Buffer): what it is, what a miss costs
   - NUMA: non-uniform memory access (for multi-socket systems)

3. **Operating System Interaction — System Calls**
   - What a system call is: crossing from user space to kernel space
   - Common syscalls (Linux): read, write, open, close, fork, exec,
     wait, mmap, brk, socket, bind, listen, accept, connect, send,
     recv, epoll, select, poll
   - How to invoke syscalls from C: the syscall() function, or the
     wrapper functions in libc
   - strace: tracing system calls — what a program does at the OS level
   - Why syscalls are expensive: context switch, kernel/user boundary

4. **Processes and Threads**
   - Process: what it is, process lifecycle (fork → exec → wait)
   - Signals: what they are, common signals (SIGINT, SIGTERM, SIGKILL,
     SIGSEGV, SIGBUS, SIGPIPE), handling signals
   - Process groups, sessions, controlling terminals
   - Threads: what they are vs processes (shared memory vs separate)
   - pthreads basics (if using C): pthread_create, pthread_join,
     pthread_mutex, pthread_cond
   - Or use Rust's std::thread / std::sync (if using Rust)

5. **Virtual Memory**
   - Virtual vs physical memory: why virtual memory exists
   - Pages: the unit of virtual memory (typically 4KB)
   - Page tables: how the OS maps virtual → physical
   - Demand paging: pages are loaded on demand, not all at once
   - Page faults: when a page isn't in RAM, the OS loads it
   - mmap: mapping files or devices into memory — how it works,
     when to use it
   - brk/sbrk: extending the heap — how malloc uses it
   - Copy-on-write: fork and COW
   - Memory-mapped I/O: mmap for file access vs read/write

6. **Basic Debugging Tools**
   - GDB: break, run, next, step, print, backtrace, info locals,
     info registers, watchpoints
   - Debugging a segfault: what happens, how to find the cause
   - Core dumps: generating, analyzing with GDB
   - strace: what syscalls are being made, what args, what results
   - ltrace: what library calls are being made

7. **C for Systems Programming**
   - Review of C specifics relevant to systems:
     - Pointers and memory (covered in C learning path)
     - Struct packing and alignment (covered in C learning path)
     - Volatile: when and why (hardware registers, shared memory,
       signal handlers)
     - Atomic operations (C11 _Atomic, stdatomic.h) — when to use,
       what they guarantee
     - Bit manipulation: bitwise operators, masks, shifting

### PROJECTS

**Project 1: mini-s tracing tool**
- Use ptrace or /proc to inspect a running process
- Print its syscalls (like a tiny strace)
- Practice: system calls, process inspection, C programming

**Project 2: Custom Memory Allocator (simple)**
- Implement a simple malloc/free using sbrk or mmap
- Understand what malloc does internally
- Practice: system calls, memory management, pointer arithmetic

**Project 3: TCP Echo Server (C or Rust)**
- A server that accepts connections and echoes back what clients send
- Practice: sockets, read/write, handling multiple connections
- Use select or poll for multiplexing (not threads yet)

**Project 4: Threaded Web Server (C or Rust)**
- Extend the echo server to use threads (pthread or std::thread)
- Handle concurrent connections
- Practice: threads, mutexes, shared state, synchronization

### SOURCE TO READ

- "Operating Systems: Three Easy Pieces" (OSTEP) — read the memory,
  persistence, and concurrency sections. This is the best OS book.
- "Computer Systems: A Programmer's Perspective" (CS:APP) — read the
  chapters on memory, linking, processes, virtual memory, concurrency.
  This book bridges the gap between code and hardware.
- Linux man pages: read the man pages for: fork, exec, mmap, brk,
  socket, bind, listen, accept, read, write, close, epoll, select,
  poll, pthread_create, pthread_mutex, signal, sigaction
- Read the source of a systems project: Redis (C, well-commented),
  or a small HTTP server like mongoose or civet, or a small database

### EVIDENCE CHECKPOINTS (L3)

- [ ] Can explain CPU caches, cache lines, locality, branch prediction
- [ ] Can explain virtual memory: pages, page tables, demand paging,
      mmap, brk
- [ ] Can use strace to understand what a program does at the OS level
- [ ] Can use GDB to debug a C program (breakpoints, stepping, backtrace)
- [ ] Can use ltrace to see library calls
- [ ] Can write a TCP server in C or Rust using sockets
- [ ] Can use threads and synchronization (mutexes, condition variables)
- [ ] Can use system calls directly (or via libc wrappers)
- [ ] Understands the process lifecycle: fork, exec, wait
- [ ] Can explain signals and basic signal handling
- [ ] Has built 4 systems programming projects (tracer, allocator,
      echo server, threaded server)

================================================================================
PHASE 2: L3 → L4 (Weeks 7-16, deepening into real systems)
================================================================================

### GOAL
Go from "understands systems basics and can write simple systems" to
"can write production systems software, can profile and optimize,
can read kernel code, can use advanced debugging tools."

### WHAT TO LEARN

1. **Advanced OS Concepts**
   - VFS (Virtual File System): how the kernel abstracts filesystems
   - Scheduling: how the OS schedules processes/threads
     — CFS (Completely Fair Scheduler) in Linux
     — Real-time scheduling (SCHED_FIFO, SCHED_RR)
   - Interrupts: hardware interrupts, interrupt handlers, top-half/bottom-half
   - Context switches: what they are, what they cost
   - I/O models: blocking, non-blocking, multiplexed (select/poll/epoll),
     async I/O (io_uring, AIO)
   - epoll: the Linux scalable I/O multiplexing mechanism — how it
     works, why it's better than select/poll

2. **Networking Deep**
   - TCP/IP stack: what happens when you send data
   - Socket options: SO_REUSEADDR, SO_REUSEPORT, TCP_NODELAY,
     TCP_KEEPALIVE, backlog
   - Non-blocking I/O with epoll/kqueue (cross-platform)
   - Connection pooling, keep-alive
   - TLS/SSL at the system level (OpenSSL or Rustls internals)

3. **File Systems**
   - How filesystems work: inodes, directories, blocks, journals
   - ext4, XFS, Btrfs: major Linux filesystems — differences
   - File descriptors: what they are, limits, management
   - Direct I/O vs buffered I/O: O_DIRECT, bypassing the page cache
   - File locking: fcntl, flock

4. **Advanced Debugging and Profiling**
   - perf: CPU profiling, flame graphs, sampling
   - perf record, perf report, perf top
   - ftrace: kernel tracing framework
   - eBPF: the modern Linux tracing/observability system
     — bpftrace for scripting
     — What eBPF can do: trace syscalls, kernel functions, user functions
   - systemtap: the older Linux tracing system (still relevant)
   - Valgrind (Memcheck, Callgrind, Cachegrind, Massif) — beyond memcheck
   - AddressSanitizer, LeakSanitizer, ThreadSanitizer, HWAddressSanitizer
   - Hotspot analysis: finding the hot functions, understanding why they're hot

5. **Writing Production Systems Code**
   - Error handling in systems code: every syscall can fail, handle it
   - Resource management: file descriptors, memory, threads — always
     clean up
   - Signal safety: async-signal-safe functions
   - Reentrancy: writing code that's safe to be interrupted
   - Logging: structured logging, log levels, log rotation
   - Configuration: handling configuration files, environment variables,
     command-line args
   - Testing systems code: unit tests, integration tests, fault injection

6. **Reading Kernel Code**
   - Find and read relevant kernel subsystems:
     - scheduler (kernel/sched/)
     - memory management (kernel/mm/)
     - VFS (fs/)
     - networking (net/)
   - Understand the kernel coding style and conventions
   - How to read kernel code: start with a specific function or subsystem,
     trace the call chain

7. **Performance Optimization**
   - Profiling first, optimize second — measure don't guess
   - Algorithmic optimization: better algorithms/data structures
   - Cache-friendly data layout: struct of arrays vs array of structs,
     data-oriented design
   - Avoiding syscalls in hot paths
   - Lock-free data structures (basic understanding)
   - Reducing memory allocations in hot paths
   - When to use SIMD (basic awareness)

### PROJECTS

**Project 5: High-Performance HTTP Server**
- An HTTP server using epoll (or mio in Rust) for high concurrency
- Practice: non-blocking I/O, event loops, connection management
- Support HTTP/1.1: parsing requests, sending responses
- Benchmark it with wrk or ab

**Project 6: Simple Database Engine**
- A key-value store with persistence (write to a file)
- B-tree or LSM-tree storage (implement a simple one)
- Practice: data structures, file I/O, indexing, persistence
- This is real systems software — a database engine

**Project 7: Container Runtime (minimal)**
- Use Linux namespaces and cgroups to isolate a process
- Practice: clone() with CLONE_NEWNS, CLONE_NEWPID, etc.,
  cgroup v2, pivot_root/chroot
- Run a simple command in an isolated environment
- This is how Docker/containerd work at the system level

### SOURCE TO READ

- "Systems Performance" by Brendan Gregg — the bible of performance
  analysis for systems
- "The Linux Programming Interface" by Michael Kerrisk — comprehensive
  reference for Linux system programming
- Linux kernel source: read specific subsystems (scheduler, VFS, memory
  management) — start small, understand one function at a time
- Read well-regarded systems projects:
  - Redis (C, well-commented, relatively small)
  - SQLite (C, the amalgamation is readable)
  - mio (Rust, event loop abstraction)
  - hyper (Rust, HTTP library — read the I/O handling)
- Brendan Gregg's blog and perf/eBPF tutorials

### EVIDENCE CHECKPOINTS (L4)

- [ ] Can write systems software (HTTP server, database, container runtime)
- [ ] Can use perf for CPU profiling and generate flame graphs
- [ ] Can use eBPF/bpftrace for tracing (basic but real usage)
- [ ] Can use ftrace for kernel tracing
- [ ] Can read kernel code for a specific subsystem and understand it
- [ ] Can use AddressSanitizer, ThreadSanitizer, LeakSanitizer
- [ ] Can optimize systems code based on profiling data
- [ ] Understands VFS, scheduling (CFS), interrupts at a deep level
- [ ] Can use epoll/kqueue for high-performance I/O
- [ ] Understands the performance characteristics of different I/O models
- [ ] Can explain the relationship between high-level code and what the
      hardware/OS actually does
- [ ] Has built 3 production-quality systems projects

================================================================================
PHASE 3: L4 → L5 (Long-term, ultimate)
================================================================================

### WHAT IT TAKES

- Contribute to the Linux kernel or major systems projects
- Understand systems programming at the hardware/architecture level:
  CPU microarchitecture, memory hierarchy, MMU, TLB, branch prediction
  internals
- Can teach systems programming
- Understands the history of systems programming: Unix, C, the evolution
  of systems languages from C to Rust
- Can read and understand CPU vendor manuals (Intel SDM, ARM ARM) for
  relevant components

================================================================================
SUMMARY: SYSTEMS PROGRAMMING ROADMAP
================================================================================

| Phase | From→To | Duration | Focus                          | Key Evidence                     |
|-------|---------|----------|--------------------------------|----------------------------------|
| 1     | L2→L3   | Weeks 1-6| Memory hierarchy, syscalls,   | 4 projects, can use GDB/strace, |
|       |         |          | processes, virtual memory,    | understand CPU caches, can      |
|       |         |          | basic debugging tools         | write TCP servers                |
| 2     | L3→L4   | Weeks 7-16| OS deep, networking, filesys,| 3 production systems projects, |
|       |         |          | perf, eBPF, kernel code,      | perf profiling, eBPF usage,     |
|       |         |          | production systems code       | kernel code reading              |
| 3     | L4→L5   | Long-term| Kernel contributions,         | Major contributions, teaching,  |
|       |         |          | hardware architecture, history| CPU manual reading               |

Dad's priority: MEDIUM. Systems programming is foundational for the
agent infrastructure. Depends on C, C++, and Rust progress.

================================================================================
