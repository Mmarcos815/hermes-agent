# ===========================================================================
# GO LEARNING PATH — L1 → L3
# ===========================================================================
# From: programming_lang_self_audit.md (Go: L1 → Target L3)
# Date: 2026-08-19
# Status: Active learning plan

## CURRENT STATE (HONEST)

- Can read simple Go code
- Explain goroutines, channels, defer, panic/recover conceptually
- Know what the standard library provides
- CANNOT write idiomatic Go independently
- CANNOT design concurrent Go programs
- CANNOT use the ecosystem tooling fluently

## TARGET: L3 (Competent)

Can write idiomatic Go, use go fmt / effective go guidelines,
understand goroutines deeply (M:N scheduling, GMP model),
channels, context, sync package, interfaces, standard library.
Can build production microservices in Go.

================================================================================
PHASE 1: L1 → L2 (Weeks 1-3)
================================================================================

### GOAL
Go from "can read simple Go" to "can write basic Go programs,
understand core syntax and idioms, can use standard library for
basic tasks."

### WHAT TO LEARN

1. **Go Philosophy and Tooling**
   - "less is more" — Go's design philosophy
   - go fmt: non-negotiable formatting
   - go run, go build, go test, go mod, go vet
   - Go module system: go.mod, go.sum, dependency management

2. **Basic Syntax**
   - Variables: var, :=, const
   - Types: int, int64, float64, bool, string, byte, rune
   - Zero values: every type has one (0, "", false, nil)
   - Control flow: if/else (no parens), for (only loop construct),
     switch (no implicit fallthrough), defer
   - Functions: multiple return values, named return values
   - Packages and imports

3. **Data Structures**
   - Arrays (fixed size) vs slices (dynamic, the real workhorse)
   - Slice internals: pointer, length, capacity
   - append, slice expressions, make
   - Maps: creation, access, delete, comma-ok idiom
   - Structs: definitions, literals, embedding (composition)
   - Pointers: & and *, but Go pointers are simpler than C

4. **Interfaces (T simplistic but powerful)**
   - Implicit implementation: a type implements an interface by
     satisfying its methods — no "implements" keyword
   - Interface as a contract, not a class
   - The empty interface: interface{} (any type)
   - Type assertions and type switches
   - Interface composition

5. **Error Handling (Go's Signature Approach)**
   - errors are values — no exceptions
   - fmt.Errorf with %w for wrapping
   - errors.Is for checking wrapped errors
   - errors.As for extracting wrapped errors
   - Custom error types: implement the error interface
   - The if err != nil pattern (idiomatic, not annoying)

6. **Standard Library Basics**
   - fmt: formatted I/O, Sprintf, Fprintf
   - os: args, exit, environment, file operations
   - io: Reader, Writer, Copy, ReadAll
   - strings: Split, Join, Contains, Replace, Trim, Fields
   - strconv: Atoi, Itoa, ParseInt, FormatInt
   - net/http: basic server and client

### PROJECTS

**Project 1: CLI Todo (Go version)**
- Same as Rust todo, but in Go
- Practice: structs, slices, maps, file I/O, error handling
- Use encoding/json for persistence

**Project 2: Simple HTTP Server**
- Use net/http to serve a REST API (in-memory store)
- GET, POST, DELETE endpoints
- Practice: handlers, mux, JSON encoding, error responses

**Project 3: grep clone**
- Read files, search for pattern, print matching lines
- Practice: bufio.Scanner, strings, flag package for CLI args

### SOURCE TO READ

- A Tour of Go (https://go.dev/tour/) — do the whole tour interactively
- Effective Go (https://go.dev/doc/effective_go) — read cover to cover,
  this is the idiomatic Go bible
- Go by Example (https://gobyexample.com/) — work through examples
- Go Blog: "Go Modules" series, "Organizing Go Code"

### EVIDENCE CHECKPOINTS (L2)

- [ ] Can write idiomatic Go without thinking about formatting (go fmt
      makes it automatic)
- [ ] Understands slices deeply: internals, append, capacity
- [ ] Can use maps, structs, interfaces in practice
- [ ] Error handling is natural: if err != nil, wrapping, Is/As
- [ ] Can write a basic HTTP server using net/http
- [ ] Uses go modules correctly
- [ ] Has built 3 small Go projects
- [ ] Can explain Go's design philosophy ("less is more")

================================================================================
PHASE 2: L2 → L3 (Weeks 4-8)
================================================================================

### GOAL
Go from "can write basic Go" to "can build concurrent Go services,
understand goroutines deeply, use context, sync package, design
idiomatic interfaces."

### WHAT TO LEARN

1. **Concurrency DEEP (Go's Killer Feature)**
   - Goroutines: how they work (GMP model: Goroutine, Machine, Processor)
   - M:N scheduling: many goroutines on few OS threads
   - The Go scheduler: work-stealing, handoff
   - Channels: buffered vs unbuffered, send/receive semantics
   - select: multiplexing channel operations
   - close on channels, range over channels
   - Goroutine leaks: how they happen, how to prevent them (context,
     channels, WaitGroup)
   - sync package: WaitGroup, Mutex, RWMutex, Once, Pool
   - context package: cancellation, timeouts, values
     — context.WithCancel, WithTimeout, WithDeadline, WithValue
     — Context should flow through every function that does I/O
     — Never store context in a struct; pass it as a parameter

2. **Interface Design (Idiomatic Go)**
   - Small interfaces: http.ResponseWriter, io.Reader, io.Writer are
     1-3 methods. That's the pattern.
   - Accept interfaces, return structs
   - Interface at the consumer side, not the implementor side
   - Interface composition: io.ReadWriteCloser = Reader + Writer + Closer
   - When to use interface{} (rarely — use generics or specific interfaces)
   - Duck typing in practice

3. **Generics (Go 1.18+)**
   - Type parameters: func foo[T any](x T)
   - Constraints: constraints.Ordered, comparable, custom constraints
   - When generics help vs when they make code unreadable
   - Go's philosophy: generics are available but idiomatic Go often
     prefers simple types and interfaces

4. **Packages and Project Structure**
   - Standard Go project layout: cmd/, internal/, pkg/ (optional)
   - Package naming: short, lowercase, no underscores
   - init functions: when they run, when to use them (rarely)
   - Public vs private: uppercase = exported
   - Dot imports (rarely, discouraged)

5. **Testing in Go**
   - go test: running tests
   - Testing package: T, B, fatalf, cleanup
   - Table-driven tests: the Go idiom for testing
   - Subtests: t.Run
   - Test fixtures and setup/teardown
   - Benchmarks: testing.B
   - Examples: godoc examples
   - Mocking: interfaces make mocking natural

6. **Standard Library DEEP**
   - net/http deeply: handlers, middleware, mux, HTTPS, timeouts
   - io deeply: Reader/Writer interface design, io.ReaderAt, Seek,
     io.Pipe
   - encoding/json: marshaling, unmarshaling, custom marshalers,
     json tags
   - database/sql: connection pooling, transactions, prepared statements
   - time: parsing, formatting, durations, timezones

7. **Error Handling ADVANCED**
   - Sentinel errors vs error types vs wrapped errors
   - errors.Is vs direct comparison
   - When to wrap and when to return fresh errors
   - Error domains: organizing errors by domain

### PROJECTS

**Project 4: Concurrent Worker Pool**
- Process a list of jobs using a worker pool (goroutines + channels)
- Use sync.WaitGroup, context for cancellation
- Practice: goroutine lifecycle, channel patterns, context propagation

**Project 5: REST API Service (Production-quality)**
- HTTP server with routing ( Chi or gorilla/mux or stdlib)
- Database integration (database/sql + PostgreSQL)
- Proper error handling, logging (slog or logrus/zap)
- Middleware: logging, recovery, auth
- Tests: table-driven, integration tests
- Dockerfile, docker-compose for local dev

**Project 6: Rewrite Todo in "Production" Go**
- Take Project 1 and make it production-quality
- Proper package structure, interfaces where appropriate, tests,
  documentation

### SOURCE TO READ

- Go Blog: "The Go Memory Model", "Context", "Organizing Go Code"
- Go Source: read net/http source (server.go, handler.go) — understand
  how the standard library handles requests
- Read source of a well-regarded Go library (e.g., chi, gorilla/mux,
  prometheus client, cobra) — understand the patterns
- "100 Go Mistakes" by Teiva Harsanyi — read this book, it's gold
- Uber Go Style Guide (https://github.com/uber-go/guide)

### EVIDENCE CHECKPOINTS (L3)

- [ ] Can explain the GMP model and how goroutines are scheduled
- [ ] Can design concurrent patterns: worker pools, fan-in/fan-out,
      pipelines, errgroups
- [ ] Understands context: when to use it, how to propagate it
- [ ] Can identify and prevent goroutine leaks
- [ ] Designs small, idiomatic interfaces (1-3 methods)
- [ ] Uses table-driven tests effectively
- [ ] Can build a production REST API with database, logging, middleware
- [ ] Can explain Go's concurrency philosophy ("share memory by
      communicating")
- [ ] Code is go fmt clean (automatic) and follows effective go
- [ ] Can teach Go basics to someone at L1

================================================================================
PHASE 3: L3 → L4 (Months 3-6, optional deepening)
================================================================================

### GOAL (if Dad wants to go beyond L3)
Production microservices, deployment, profiling, deep networking.

### WHAT TO LEARN

- Docker, Kubernetes deployment of Go services
- pprof for profiling: CPU, memory, goroutines, blocking
- go trace for scheduler visualization
- Advanced net/http: HTTP/2, graceful shutdown, connection pooling
- gRPC in Go (if needed)
- cgo: calling C from Go (and the trade-offs)
- Build tags, compile-time conditioning

### EVIDENCE (L4)

- [ ] Can build and deploy production Go microservices
- [ ] Can profile and optimize Go services (pprof, trace)
- [ ] Understands Go's networking stack deeply
- [ ] Can contribute to Go ecosystem (crates, documentation)

================================================================================
SUMMARY: GO ROADMAP
================================================================================

| Phase | From→To | Duration | Focus                         | Key Evidence                     |
|-------|---------|----------|-------------------------------|-----------------------------------|
| 1     | L1→L2   | Weeks 1-3| Syntax, slices, interfaces,  | 3 small projects, idiomatic Go   |
|       |         |          | errors, basic stdlib          |                                   |
| 2     | L2→L3   | Weeks 4-8| Concurrency, context, sync,   | Production REST API, L3 evidence |
|       |         |          | interface design, testing    |                                   |
| 3     | L3→L4   | Months 3-6| Profiling, deployment,      | Production microservices, perf   |
|       |         |          | advanced networking          |                                   |

Dad's priority: MEDIUM. Go is strategic for backend services.

================================================================================
