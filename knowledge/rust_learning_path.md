# ===========================================================================
# RUST LEARNING PATH — L1 → L3 → L4/L5
# ===========================================================================
# From: programming_lang_self_audit.md (Rust: L1 → Target L3)
# Date: 2026-08-19
# Status: Active learning plan

## CURRENT STATE (HONEST)

- Can read and explain Rust code at a basic level
- Understand ownership, borrowing, lifetimes conceptually
- Know what Cargo is, what crates are
- CANNOT write Rust code that compiles without significant struggle
- CANNOT design Rust programs independently
- CANNOT use the standard library fluently

## TARGET: L3 (Competent)

Can write code that compiles without fighting the borrow checker
constantly. Understands ownership, borrowing, lifetimes, traits,
error handling, concurrency, module system, Cargo. Can build
non-trivial Rust projects independently.

## PHASE 1: L1 → L2 (Weeks 1-4, intensive)

### GOAL
Go from "can read simple Rust" to "can write basic Rust programs
with reference materials handy, understand core syntax, can debug
simple errors."

### WHAT TO LEARN

1. **Ownership and Borrowing (THE FOUNDATION — spend real time here)**
   - Move semantics: what moves, what copies, what clones
   - &T vs &mut T — the borrowing rules
   - Scope and lifetime of borrows
   - The "one mutable OR many immutable" rule
   - Why Rust does this (memory safety without GC)

2. **Basic Syntax and Types**
   - Variables: let, let mut, const, static
   - Primitive types: i32, u64, f64, bool, char, str, String
   - &str vs String — the string type distinction (critical)
   - Arrays, slices, Vec
   - Tuples, structs, enums
   - Pattern matching: match, if let, while let
   - Functions: parameters, return values, -> syntax
   - Control flow: if, loop, while, for, break, continue, return

3. **Option and Result (Error Handling Foundation)**
   - Option<T>: Some, None, why it exists
   - Result<T, E>: Ok, Err, why it exists
   - The ? operator — how it works with From
   - Combinators: map, unwrap_or, unwrap_or_else, and_then, match

4. **Basic Tooling**
   - cargo new, cargo build, cargo run, cargo test
   - cargo fmt, cargo clippy
   - rustup: managing toolchains
   - Reading rustc error messages (they're helpful — learn to read them)

### PROJECTS (Build These)

**Project 1: Command-line Todo List**
- Add, list, complete, remove tasks
- Store in a JSON file
- Practice: structs, enums, file I/O, serde, error handling with Result
- Goal: write it without constantly checking docs, but reference is OK

**Project 2: Word Count Utility (wc clone)**
- Read files, count lines/words/characters
- Practice: File I/O, BufReader, iterators, string processing
- Handle errors properly (no unwrap in production code)

**Project 3: Simple HTTP Client**
- Use reqwest or std::net::TcpStream
- Fetch a URL, print the response
- Practice: external crates, async vs sync, error handling

### SOURCE TO READ

- The Rust Book (https://doc.rust-lang.org/book/) — read chapters 1-10
  cover to cover, do the exercises
- Rust by Example (https://doc.rust-lang.org/rust-by-example/) — work
  through the examples, type them out
- Rust Reference — skim for overview, dive into specific sections as
  questions arise

### EVIDENCE CHECKPOINTS (L2)

- [ ] Can explain ownership, borrowing, lifetimes in own words
- [ ] Can write a Rust program that compiles without borrow checker
      fights on the first or second attempt
- [ ] Can read and understand rustc error messages
- [ ] Has built 3 small Rust projects (todo, wc, http client)
- [ ] Can use Result and Option fluently
- [ ] Can use cargo: build, test, run, fmt, clippy
- [ ] Understands &str vs String and when to use each
- [ ] Can explain why Rust has no GC and how ownership replaces it

================================================================================
PHASE 2: L2 → L3 (Weeks 5-10, building competence)
================================================================================

### GOAL
Go from "can write basic Rust with reference" to "can build
non-trivial Rust projects independently, understand traits,
generics, concurrency, module system."

### WHAT TO LEARN

1. **Traits and Generics (THE TYPE SYSTEM CORE)**
   - What traits are: shared behavior, like interfaces
   - Deriving traits: Debug, Clone, PartialEq, etc.
   - Trait bounds: fn foo<T: Display>(x: T)
   - Generic functions and structs
   - The Orphan Rule: why you can't implement external traits on
     external types, and the newtype workaround
   - Common traits: Into, From, AsRef, Borrow, Default, Iterator
   - Implementing traits for your own types

2. **Lifetimes (PRACTICAL UNDERSTANDING)**
   - Why lifetimes exist: the borrow checker needs to know how long
     references are valid
   - Lifetime elision rules (the 3 rules that cover most cases)
   - When explicit lifetimes are needed
   - Lifetime subtyping (basic)
   - Common lifetime errors and how to fix them
   - 'static lifetime — what it means

3. **Error Handling DEEP**
   - Designing error types: enum with Display + From (manual)
   - Using thiserror crate for ergonomic error types
   - error chain / causes
   - When to use expect() (almost never in production)
   - When unwrap() is acceptable (tests, prototypes, unreachable)
   - The ? operator with custom error types

4. **Collections and Iterators**
   - Vec, HashMap, HashSet, BTreeMap, BTreeSet
   - Iterator trait: iter(), into_iter(), iter_mut()
   - Iterator adapters: map, filter, collect, enumerate, zip, fold,
     flat_map,chain
   - Laziness of iterators — when they execute
   - IntoIterator vs Iterator
   - Writing custom iterators (optional but valuable)

5. **Modules and Crates**
   - mod, pub, use, crate root
   - lib.rs vs main.rs
   - Organizing a crate: directory structure
   - Visibility: pub, pub(crate), pub(super)
   - Cargo: dependencies, features, workspaces
   - Semantic versioning in Rust (caret, tilde, exact)

6. **Testing**
   - #[test] attribute, cargo test
   - Assert macros: assert_eq!, assert_ne!, assert!
   - Should_panic tests
   - Test modules (mod tests { #[test] ... })
   - Integration tests vs unit tests (tests/ directory)
   - Doc tests

7. **Smart Pointers and Interior Mutability**
   - Box<T>: heap allocation, recursive types
   - Rc<T>, Arc<T>: reference counting
   - RefCell<T>, Mutex<T>: interior mutability
   - When to use each
   - Reference cycles and leaks (Rc cycle → memory leak)

8. **Concurrency (BASICS)**
   - std::thread: spawn, join
   - Move closures into threads
   - Mutex, RwLock, Arc
   - mpsc channels: sending data between threads
   - Send and Sync traits — what they mean
   - Thread safety vs Rust's guarantees

### PROJECTS (Build These)

**Project 4: Chat Server (TCP)**
- Multi-client TCP server using threads
- Broadcast messages to all connected clients
- Practice: std::net, std::thread, Arc<Mutex<>>, channels
- Handle client disconnection gracefully

**Project 5: File Watcher**
- Watch a directory for changes (use notify crate or polling)
- On change, run a command or print a message
- Practice: external crates, event handling, async or threads

**Project 6: CLI Tool with Proper Error Handling**
- A tool that does something useful (e.g., JSON validator, CSV parser,
  grep clone)
- Uses thiserror or manual error enum
- Has proper tests (unit + integration)
- Published to crates.io (optional but good evidence)

**Project 7: Rewrite One of the L2 Projects in Rust**
- Take the todo list or wc from Phase 1 and make it production-quality
- Better error handling, testing, documentation
- Clippy-clean, rustfmt-clean

### SOURCE TO READ

- The Rust Book — chapters 11-18 (traits, generics, lifetimes, testing,
  iterators, concurrency, macros, final project)
- Rustonomicon — read the chapters on unsafe Rust, lifetimes (for deeper
  understanding, not immediate practice)
- Standard library docs — read the API docs for: Vec, HashMap, Option,
  Result, Iterator, Thread, Mutex, Arc
- Read source code of small popular crates (e.g., anyhow, thiserror,
  serde — understand how they're structured)

### EVIDENCE CHECKPOINTS (L3)

- [ ] Can write Rust code that compiles without fighting the borrow
      checker constantly
- [ ] Can explain lifetimes and when explicit annotations are needed
- [ ] Can design error types using thiserror or manual enum
- [ ] Can use traits: write generic functions, implement traits for
      own types, understand the Orphan Rule
- [ ] Can use Arc<Mutex<T>> for shared mutable state across threads
- [ ] Has built at least 3 substantial Rust projects (chat server,
      file watcher, CLI tool)
- [ ] Code is clippy-clean and rustfmt-clean
- [ ] Can use cargo workspaces for multi-crate projects
- [ ] Has tests: unit tests, integration tests, doc tests
- [ ] Can read and understand source code of small popular crates
- [ ] Can explain Send and Sync and when they matter
- [ ] Can teach Rust basics to someone at L1

================================================================================
PHASE 3: L3 → L4 (Months 3-6, deepening)
================================================================================

### GOAL
Deep practical mastery. Can design Rust libraries with idiomatic APIs.
Understand unsafe Rust. Profile and optimize. Contribute to ecosystem.

### WHAT TO LEARN

1. **Unsafe Rust**
   - Raw pointers: *const T, *mut T
   - Unsafe blocks: what's allowed, what's not
   - The safety contract: what you guarantee, what Rust guarantees
   - Calling C code via FFI
   - Implementing unsafe traits
   - when unsafe is NEEDED vs when it's just convenient

2. **Advanced Patterns**
   - Newtype pattern (for Orphan Rule, encapsulation, type safety)
   - Extension traits (adding methods to external types)
   - Iterator patterns (custom iterators, streaming iterators)
   - Arena allocation
   - CRTP-like patterns in Rust
   - Type-state pattern (encoding state in types)

3. **Advanced Lifetimes**
   - Complex lifetime relationships
   - Higher-ranked trait bounds (for<'a>)
   - Lifetime annotations on structs with references

4. **Async Rust**
   - Tokio: runtime, tasks, async/await
   - Futures: what they are, how they work
   - Pin and Unpin (the hard part)
   - async traits (async-trait crate or RTIC)
   - Channels in async (tokio::sync)
   - Async error handling

5. **Macros (BASICS)**
   - Declarative macros: macro_rules!
   - Basic procedural macros: function-like, attribute, derive
   - When macros are appropriate vs when functions suffice

6. **Profiling and Optimization**
   - perf, flamegraph
   - criterion for benchmarking
   - Debugging performance issues
   - When to use #[inline], #[cold], etc.

7. **Cargo and Ecosystem Deep**
   - Publishing crates to crates.io
   - Semver in practice
   - Workspaces with multiple crates
   - Feature flags and optional dependencies

### PROJECTS (Build These)

**Project 8: async Rust Web Service**
- Use tokio, axum or actix-web
- REST API with database (sqlx or diesel)
- Proper error handling, testing
- Dockerfile for deployment

**Project 9: Contribute to an Open Source Rust Crate**
- Find a crate you use, find a bug or missing feature
- Submit a PR
- This is L4 evidence: contributing to the ecosystem

**Project 10: Write a Small Crate and Publish It**
- A useful library (not just a toy)
- Proper documentation (rustdoc)
- Tests, examples
- Published to crates.io

### SOURCE TO READ

- Rustonomicon — full read, especially unsafe Rust chapters
- Tokio tutorial — async Rust deep dive
- Read the source of a moderate-sized crate (e.g., anyhow, serde_json,
  tokio — pick one and really understand it)
- This Week in Rust — stay current with the ecosystem

### EVIDENCE CHECKPOINTS (L4)

- [ ] Can design Rust libraries with idiomatic APIs
- [ ] Can write unsafe Rust safely — understands the safety contract
- [ ] Can use advanced patterns: newtype, extension traits, type-state
- [ ] Can write async Rust with tokio — understands futures, Pin
- [ ] Can profile and optimize Rust code
- [ ] Has contributed to an open source Rust project (PR merged)
- [ ] Has published a crate to crates.io (optional but good evidence)
- [ ] Can explain the compiler's view: MIR, optimization passes (basic)
- [ ] Can read and understand source of a moderate-sized crate

================================================================================
PHASE 4: L4 → L5 (Long-term, ultimate target)
================================================================================

### GOAL
Authoritative understanding. Contribute to rust-lang/rust or major
ecosystem crates. Understand Rust's type system at the theoretical
level. Can teach Rust to beginners.

### WHAT IT TAKES

- Read and understand rustc source (at least specific components)
- Understand Rust's safety guarantees formally: what the type system
  proves, what it doesn't prove
- Have written compilers, interpreters, or significant systems software
  in Rust
- Contribute to rust-lang/rust (bugs, patches, documentation)
- Can teach Rust and explain the borrow checker intuitively
- Understand Rust's design trade-offs authoritatively

### PROJECTS

- Contribute to rust-lang/rust or a major crate (regex, serde, tokio,
  hyper, etc.)
- Write a compiler or interpreter in Rust
- Write a significant systems tool in Rust (e.g., a database engine,
  a container runtime, a network protocol implementation)
- Write a book, tutorial series, or conference talk on Rust

================================================================================
SUMMARY: RUST ROADMAP
================================================================================

| Phase | From→To | Duration | Focus                          | Key Evidence                    |
|-------|---------|----------|--------------------------------|----------------------------------|
| 1     | L1→L2   | Weeks 1-4| Ownership, syntax, basics     | 3 small projects, can compile   |
| 2     | L2→L3   | Weeks 5-10| Traits, lifetimes, concurrency| 3 substantial projects, L3 ev.  |
| 3     | L3→L4   | Months 3-6| Unsafe, async, patterns      | OSS contribution, published crate|
| 4     | L4→L5   | Long-term| rustc source, theory, teaching| Major contributions, teaching   |

Dad's priority: MEDIUM. This is a strategic language for the agent
infrastructure. The Rust journey takes time — Dad said "take your
time for make no mistakes." L3 is the first real milestone.

================================================================================
