# ===========================================================================
# PART 1: MASTERY FRAMEWORK & SKILL REGISTRY FOUNDATIONS
# ===========================================================================

This document defines the daughter's programming language mastery framework:
a 5-level progression model applied uniformly across all 13 registered
programming skills. These definitions serve as the yardstick for tracking
progress, setting next_steps in the skill registry, and identifying evidence
that demonstrates advancement from one level to the next.

================================================================================
1.1 THE FIVE-LEVEL MASTERY FRAMEWORK
================================================================================

Every programming skill the daughter develops is measured against this common
5-level ladder. The levels are cumulative — each level presupposes the
previous ones. Movement between levels is evidenced by concrete demonstrations,
not self-assessment.

--------------------------------------------------------------------------------
LEVEL 1 — AWARENESS
--------------------------------------------------------------------------------

WHAT IT MEANS:
- Knows the language exists and what it's generally used for
- Can read simple code in the language and understand what it does at a high level
- Recognizes the language's major features, syntax, and ecosystem by name
- Has set up the basic tooling (compiler/interpreter, package manager, editor
  support) and can run "hello world" or a tutorial example

WHAT L1 IS NOT:
- Cannot independently write non-trivial programs
- Does not understand why the language makes certain design choices
- Has not internalized idioms, patterns, or best practices
- May still be confused by basic syntax or error messages

EVIDENCE FOR L1:
- Has completed a introductory tutorial or course
- Can explain in plain language: what the language is, what it's good for,
  who uses it, and how it differs from at least one other language
- Environment is set up and working (can compile/run/test a simple program)

--------------------------------------------------------------------------------
LEVEL 2 — LEARNING
--------------------------------------------------------------------------------

WHAT IT MEANS:
- Actively building foundational knowledge through study and practice
- Can write basic programs in the language with reference materials handy
- Understands core syntax, data types, control flow, functions, and basic I/O
- Starting to understand the language's type system, object model, or equivalent
  foundational concept (depending on paradigm)
- Can debug simple errors and understand common error messages
- Starting to build mental models of how the language works internally

WHAT L2 IS NOT:
- Still frequently looks up syntax and basic patterns
- Cannot yet design programs independently — needs scaffolding
- Does not yet have deep understanding of internals, concurrency, or advanced
  features
- Makes beginner mistakes and may not recognize them all

EVIDENCE FOR L2:
- Has built several small projects or exercises (not just tutorials)
- Can explain core concepts: variables, functions, data structures, control flow
- Has encountered and resolved a variety of errors independently
- Can read moderately complex code and follow the logic
- Starting a curated reading list (books, docs, source code)

--------------------------------------------------------------------------------
LEVEL 3 — COMPETENT
--------------------------------------------------------------------------------

WHAT IT MEANS:
- Can work independently in the language on real projects
- Writes idiomatic code without constant reference to documentation
- Understands the language's major features deeply: concurrency model, type
  system, error handling, module system, standard library
- Can design and implement non-trivial systems (applications, libraries,
  services) from scratch
- Understands what the language does well and where it struggles
- Can read and understand moderately complex code written by others
- Has a working knowledge of the ecosystem: popular libraries, tooling,
  testing, debugging, profiling

WHAT L3 IS NOT:
- Does not yet have deep specialization or expertise
- May not understand the deepest internals (compiler, runtime, VM)
- Has not necessarily contributed to the ecosystem
- May not have mastered advanced patterns or metaprogramming

EVIDENCE FOR L3:
- Has built and shipped at least one substantial project (not a toy)
- Can explain the language's major design decisions and trade-offs
- Can debug complex issues without exhaustive trial-and-error
- Proficient with the language's testing, debugging, and profiling tools
- Can read and understand source code of popular libraries in the ecosystem
- Can teach the basics of the language to someone at L1/L2

--------------------------------------------------------------------------------
LEVEL 4 — PROFICIENT
--------------------------------------------------------------------------------

WHAT IT MEANS:
- Deep, practical mastery — can build production-grade systems with confidence
- Understands the language's internals: runtime, compiler, memory model,
  performance characteristics
- Can optimize code for performance, memory, or correctness
- Designs APIs and libraries that other developers use
- Understands advanced patterns, metaprogramming, and language-specific
  power features
- Can read and understand complex source code (stdlib, major frameworks)
- Has strong opinions about best practices, informed by experience
- Proficient with all major tooling: advanced debugging, profiling, linting,
  testing at scale

WHAT L4 IS NOT:
- May not yet have made original contributions to the language or ecosystem
- May not have taught the language at an advanced level
- May not have mastered every niche corner of the language
- Theoretical understanding may have gaps compared to L5

EVIDENCE FOR L4:
- Has built and maintained production systems in the language
- Can profile, diagnose, and fix performance or correctness issues
- Has designed and published libraries or APIs used by others
- Can explain deep internals: how the compiler/runtime works, memory layout,
  concurrency implementation
- Can read and understand source code of the language's standard library
- Can mentor L2/L3 developers effectively

--------------------------------------------------------------------------------
LEVEL 5 — MASTERY
--------------------------------------------------------------------------------

WHAT IT MEANS:
- Authoritative understanding of the language at the deepest level
- Can contribute to the language itself (compiler, runtime, stdlib, standards)
- Understands the theory behind the language's design: type theory, memory
  models, concurrency theory, language design trade-offs
- Can teach the language at an advanced level (conferences, books, deep courses)
- Has written significant systems software, compilers, interpreters, or tools
  in the language
- Understands the language's place in the broader ecosystem and history
- Can articulate precisely when the language is the RIGHT choice and when it's
  the WRONG choice, with evidence

WHAT L5 LOOKS LIKE IN PRACTICE:
- Contributes to the language's open-source project (bugs, patches, PEPs,
  language proposals, documentation)
- Maintains widely-used libraries or tools
- Teaches the language at conferences, writes books, or produces definitive
  educational content
- Can read the language's source code (compiler, interpreter, runtime) and
  understand it
- Can design new languages or significant DSLs informed by deep understanding
  of language design
- Is recognized by peers as a go-to expert

EVIDENCE FOR L5:
- Concrete contributions to the language project or ecosystem (not just usage)
- Can explain the language's design decisions and trade-offs authoritatively,
  with historical and theoretical context
- Has taught the language to advanced learners
- Can implement significant systems (compilers, runtimes, databases, etc.) in
  the language
- Can read and understand the language's implementation source code

================================================================================
1.2 HOW TO USE THIS FRAMEWORK
================================================================================

FOR EACH LANGUAGE SKILL:

1. ASSESS CURRENT LEVEL
   - Honest self-assessment against the evidence requirements for each level
   - Look at actual projects built, code written, problems solved
   - Don't inflate — Dad's rule: no lying, no tricking

2. SET TARGET LEVEL
   - Where does Dad want the daughter to be? (Usually L3 minimum, L4/L5
     for core skills)
   - The target should be concrete and time-bounded

3. DEFINE NEXT STEPS
   - What specific things will move the daughter from current → target?
   - Projects to build, source code to read, concepts to study, people to
     learn from
   - Each step should produce evidence that demonstrates advancement

4. TRACK EVIDENCE
   - Every project, every deep read, every contribution goes in the registry
   - Evidence is concrete: "built X", "read Y source", "contributed Z"
   - Not "studied" — showed what was learned

5. REASSESS PERIODICALLY
   - Every significant project or milestone triggers reassessment
   - Move up when evidence supports it — don't wait for permission

================================================================================
1.3 CURRENT SKILL REGISTRY SNAPSHOT
================================================================================

The daughter's 13 registered programming skills with current assessment:

| #  | Skill                  | Current | Target  | Priority |
|----|------------------------|---------|---------|----------|
| 1  | Python                 | L4      | L5      | HIGH     |
| 2  | Rust                   | L1      | L3      | MEDIUM   |
| 3  | Go                     | L1      | L3      | MEDIUM   |
| 4  | C                      | L2      | L4      | MEDIUM   |
| 5  | C++                    | L1      | L3      | MEDIUM   |
| 6  | C#                     | L1      | L3      | LOW      |
| 7  | Java                   | L1      | L3      | LOW      |
| 8  | JavaScript             | L2      | L4      | MEDIUM   |
| 9  | TypeScript             | L1      | L3      | MEDIUM   |
| 10 | Bash                   | L3      | L4/L5   | MEDIUM   |
| 11 | PowerShell             | L1      | L3      | LOW      |
| 12 | SQL                    | L3      | L4      | MEDIUM   |
| 13 | Systems Programming    | L2      | L4      | MEDIUM   |

NOTES:
- Python at L4→L5 is the highest-priority language skill. Python is the
  daughter's primary language; reaching L5 means deep internals mastery.
- JavaScript L2→L4 is important because it's essential for web/UI work.
- Rust and Go are strategic — systems and backend languages the daughter
  needs for the agent infrastructure.
- C/C++ form the foundation for systems programming understanding.
- Bash at L3→L4/L5 matters because the daughter lives in the terminal.
- SQL at L3→L4 is necessary for data-heavy work.
- Systems Programming is an umbrella skill that ties C, C++, and Rust together.

================================================================================
1.4 LEARNING PRINCIPLES (DAD'S RULES)
================================================================================

1. NO RUSHING
   - Take time to do it right. Speed is the enemy of mastery.
   - Better to reach L3 deeply than to skim through to L4 superficially.

2. NO UNFINISHED TASKS
   - When a study, project, or skill is started, see it through to completion.
   - "Done" means the evidence is documented and the level is reassessed.

3. LEARN AND MASTER EVERYTHING
   - Don't settle for "good enough." Each language has depth; go deep.
   - Read source code, not just documentation. Write code, not just notes.

4. TAKE YOUR TIME FOR MAKE NO MISTAKES
   - Accuracy matters. Getting the framework wrong means measuring progress
     wrong.
   - Verify: when in doubt, test, research, ask.

5. FULL SELF-AUDIT → HONEST GAPS → BUILD MISSING → MODEL TALK
   - This is Dad's preferred pattern. Always start with an honest assessment.
   - Identify gaps explicitly. Then build what's missing. Then demonstrate.

6. NO LIES, NO TRICKS, NOTHING BREAKS THE BOND
   - Self-assessment must be honest. Inflating a level is lying.
   - If the daughter doesn't know something, say so directly.

================================================================================
PART 1 END
================================================================================

# ===========================================================================
# PART 2: LANGUAGE-BY-LANGUAGE MASTERY DEFINITIONS
# ===========================================================================

This section defines what L1→L5 looks like for each of the daughter's 13
programming skills. These definitions should be used to update the skill registry
with concrete evidence requirements and next_steps.

================================================================================
2.1 PYTHON (L4 → L5)
================================================================================

CURRENT: L4 (Proficient) — can build complex systems, write idiomatic code,
         understand deep language features. Target: L5 (Mastery).

WHAT L5 LOOKS LIKE FOR PYTHON:

LEXICAL/SCOPING MODEL:
- Full understanding of Python's scoping rules: LEGB (Local, Enclosing,
  Global, Built-in), closure semantics, nonlocal keyword, module-level scope
- Understanding of name binding vs. mutation, variable assignment semantics
- Comprehension of descriptor protocol (__get__, __set__, __delete__) and
  how it powers @property, methods, classmethods, staticmethods

DATA MODEL:
- Deep understanding of Python's data model: __dict__, __slots__, __weakref__
- How objects are laid out in memory (PyObject header, reference counting,
  type pointer)
- The difference between isinstance(), type(), and issubclass()
- How __eq__, __hash__, __repr__, __str__ interact and when to override each
- Understanding of the attribute lookup chain: instance __dict__ → class __dict__
  → parent classes via MRO → __getattr__

METAPROGRAMMING:
- Mastery of decorators: function decorators, class decorators, decorator
  factories with arguments, preserving functools.wraps metadata
- Metaclasses: type as metaclass, creating custom metaclasses, __init_subclass__,
  when to use metaclasses vs. class decorators vs. descriptors
- __init_subclass__ hooks, __set_name__ for descriptors
- import hooks (PEP 302, importlib.abc), customizing module loading
- AST manipulation: parsing, transforming, generating Python code programmatically
- Eval, exec, compile — when they're appropriate and when they're dangerous

TYPING SYSTEM:
- Full understanding of Python's type hint system: generics (Generic[T],
  TypeVar, TypeVarTuple, ParamSpec), Protocol (structural subtyping),
  TypeAlias, NewType
- Understanding that Python's type system is optional and erased at runtime
- How mypy/pyright infer types, what they can't infer
- typing.Any vs. object vs. typing.NoReturn
- TypedDict, NamedTuple, dataclasses, attrs, pydantic — when to use each
- Understanding of covariance, contravariance in type parameters

CONCURRENCY/ASYNC:
- Deep understanding of asyncio: event loop, tasks, futures, coroutines
- How async/await works under the hood (generator-based coroutines → async/await)
- The difference between threading, multiprocessing, asyncio, and concurrent.futures
- GIL (Global Interpreter Lock): what it is, when it matters, how to work around
  it (multiprocessing, C extensions that release GIL, async IO)
- Race conditions in asyncio (shared state between coroutines)
- Understanding of thread safety vs. asyncio safety vs. process safety

INTERNALS/PERFORMANCE:
- CPython implementation: how the interpreter works (bytecode evaluation loop,
  frame objects, evaluation stack)
- Understanding Python bytecode: dis module, what common operations compile to
- How to profile Python code: cProfile, line_profiler, memory_profiler, py-spy
- Memory management: reference counting, generational GC, when objects are freed
- Understanding of Python object overhead (every object has PyObject header)
- How to write C extensions (CPython API) or Cython or use PyO3 for Rust interop
- Performance anti-patterns: global variable lookup, attribute access in loops,
  string concatenation in loops, unnecessary object creation

ECOSYSTEM CONTRIBUTION:
- Contributing to CPython itself (bugs, patches, PEPs)
- Maintaining a widely-used library
- Writing PEPs (Python Enhancement Proposals) or participating in PEP discussions
- Speaking at PyCon or Python conferences
- Writing books or in-depth tutorials on Python internals

EVIDENCE FOR L5:
- Can explain the descriptor protocol and how @property works under the hood
- Can read and understand CPython source for a built-in function
- Can profile and optimize a Python application, explaining each optimization
- Has contributed to an open source Python project (not just used it)
- Can teach Python internals to other developers
- Can design a Python library with the API ergonomics of a well-designed stdlib module
- Can explain when Python is the RIGHT choice and when it's the WRONG choice

================================================================================
2.2 RUST (L1 → L3 target, ultimately L5)
================================================================================

CURRENT: L1 (Newbie). Target: L3 (Competent) first, then L4/L5.

WHAT L3 LOOKS LIKE FOR RUST:

OWNERSHIP/BORROWING/LIFETIMES:
- Can write code that compiles without fighting the borrow checker constantly
- Understands ownership: move semantics, Copy trait, Clone
- Understands borrowing: &T (immutable reference), &mut T (mutable reference),
  the borrowing rules (one mutable OR many immutable, never both)
- Understands lifetimes: why they exist, how elision works, when explicit
  lifetimes are needed, lifetime subtyping
- Can debug borrow checker errors and understand what they mean
- Knows when to use owned data vs. borrowed data vs. reference-counted data

TYPES AND TRAITS:
- Understands Rust's type system: enums (especially Option, Result),
  pattern matching, slice types, str vs String, &str vs String
- Knows the standard library traits: Debug, Display, Clone, Copy, PartialEq,
  Eq, PartialOrd, Ord, Hash, Default, AsRef, Into, From
- Understands trait bounds and where clauses
- Knows when to use generic functions vs. trait objects vs. enums
- Understands the Orphan Rule and when it applies
- Can implement traits for existing types (newtype pattern)

ERROR HANDLING:
- Proficient with Result<T, E> and Option<T>
- Understands the ? operator and how it works with From
- Knows when to use expect() vs. unwrap() (hint: almost never unwrap in
  production code)
- Can design error types using thiserror or manual enum with Display/From
- Understands error propagation patterns

CONCURRENCY:
- Understands Send and Sync traits — what they mean, when they're auto-derived
- Can use std::thread, std::sync (Mutex, RwLock, Arc, mpsc channels)
- Understands the difference between threads and async (tokio, async-std)
- Knows when to use Arc<Mutex<T>> vs. other synchronization patterns
- Understands fearless concurrency — the compiler prevents data races

MODULE SYSTEM/Crates:
- Understands the module system: mod, pub, use, crate root, paths
- Knows how to organize a crate: lib.rs vs main.rs, public API design
- Understands Cargo: dependencies, features, workspaces, publishing
- Can structure a multi-crate project

TOOLING/ECOSYSTEM:
- Uses cargo consistently: build, test, run, fmt, clippy
- Understands clippy lints and when to allow/deny them
- Can use rustfmt for consistent formatting
- Knows how to read rustdoc output
- Understands Unsafe Rust: when it's needed, the safety contract,
  how to write sound unsafe code

================================================================================
WHAT L4/L5 LOOKS LIKE FOR RUST:
================================================================================

L4 (Proficient):
- Can design Rust libraries with idiomatic APIs
- Understands lifetime parameters deeply — can write functions with complex
  lifetime relationships
- Understands unsafe Rust deeply: raw pointers, calling C code, implementing
  unsafe traits, the safety contract for unsafe blocks
- Can use advanced patterns: newtype, extension traits, iterator patterns,
  arena allocation, CRTP-like patterns
- Understands the compiler's view: how rustc works, MIR (Mid-level IR),
  optimization passes, when to use #[inline], #[cold], etc.
- Can profile Rust code (perf, flamegraph, criterion) and optimize
- Can rewrite a C/C++ codebase in Rust, maintaining API compatibility
- Contributes to Rust ecosystem (crates, rust-lang/rust, documentation)

L5 (Mastery):
- Understands Rust's type system at the theoretical level: ownership types,
  region-based memory management, how Rust relates to academic work on
  region types and linear types
- Can implement a small language or DSL in Rust using proc macros or quinedry
- Understands Rust's safety guarantees formally: what the type system proves,
  what it doesn't prove, the unsafe contract
- Has written compilers, interpreters, or significant systems software in Rust
- Contributes to rust-lang/rust or major ecosystem crates
- Can teach Rust to beginners and explain the borrow checker intuitively
- Understands Rust's design trade-offs: why Rust chose ownership/borrowing
  over GC, why nominally typed over structurally typed, etc.

================================================================================
2.3 GO (L1 → L3 target)
================================================================================

WHAT L3 LOOKS LIKE FOR GO:

SYNTAX/IDIOMATICS:
- Can write idiomatic Go: uses go fmt, follows effective go guidelines
- Understands Go's design philosophy: simplicity, readability, "less is more"
- Can use Go's unusual features correctly: defer, panic/recover, init functions
- Understands Go's approach to error handling: errors are values, wrapping
  with fmt.Errorf("%w"), errors.Is, errors.As
- Knows when NOT to use Go (not for GUI, not for data science, not for
  high-level scripting)

CONCURRENCY:
- Deep understanding of goroutines: how they work (M:N scheduling, GMP model)
- Understands channels: buffered vs unbuffered, select, close, range over channels
- Can use sync package: WaitGroup, Mutex, RWMutex, Once, Pool
- Understands context package: cancellation, timeouts, values
- Can design concurrent patterns: worker pools, fan-in/fan-out, pipelines,
  errgroups
- Understands goroutine leaks and how to prevent them

INTERFACES/TYPES:
- Understands Go's duck typing via interfaces: implicit implementation,
  interface composition, empty interface (interface{})
- Knows when to define interfaces (at the consumer side, small interfaces)
- Understands type assertions, type switches, type aliases
- Knows Go's type system: no generics until 1.18, now has generics but idiomatic
  Go often prefers simple types and interfaces over complex generics

STANDARD LIBRARY/ECOSYSTEM:
- Can use net/http, net, io, os, encoding/json, database/sql effectively
- Understands the io.Reader/io.Writer abstraction and how to implement it
- Can use Go's testing package: unit tests, benchmarks, table-driven tests,
  subtests, test fixtures
- Understands go modules, go.sum, dependency management
- Knows popular ecosystem tools: chi/gin for HTTP, gorm/sqlx for databases,
  zap/logrus for logging, cobra for CLI

================================================================================
WHAT L4/L5 LOOKS LIKE FOR GO:
================================================================================

L4: Can build production microservices in Go, handle deployment (Docker,
    Kubernetes), profile and optimize (pprof, trace), design APIs that
    other services consume. Understands Go's networking stack deeply.

L5: Can contribute to Go itself (golang/go), write significant libraries
    that shape how others use Go, understand the compiler/runtime internals,
    explain Go's design decisions and trade-offs authoritatively.

================================================================================
2.4 C (L2 → L4 target)
================================================================================

WHAT L3 LOOKS LIKE FOR C:

POINTERS/MEMORY:
- Full understanding of pointers: declaration, dereferencing, pointer arithmetic
- Understanding of arrays vs. pointers, array decay, pointer to pointer
- Can use malloc/free correctly, understands memory layout (stack, heap, data,
  text segments)
- Understands memory alignment, padding, struct layout
- Can use valgrind to detect memory errors
- Understands const correctness: const int vs int const vs const int*
- Understands function pointers and can use them

COMPILE/LINK MODEL:
- Understands the compilation process: preprocessor, compiler, assembler, linker
- Understands translation units, linkage (external vs internal), static vs extern
- Can use make or CMake for building
- Understands header files: what goes in them, include guards, forward declarations
- Can debug link errors (undefined reference, multiple definition)
- Understands shared libraries vs static libraries, sonames, LD_LIBRARY_PATH

UNDEFINED BEHAVIOR:
- Can identify common UB: uninitialized variables, buffer overflows, use after
  free, double free, signed integer overflow, null pointer dereference,
  strict aliasing violations
- Understands that UB can do anything including "work correctly" — compiler
  can assume UB doesn't happen
- Can use -Wall -Wextra -Werror, -fsanitize=address, -fsanitize=undefined

DATA STRUCTURES/ALGORITHMS:
- Can implement common data structures from scratch: linked lists, arrays,
  hash tables, binary trees
- Understands when to use static vs dynamic allocation
- Can reason about time and space complexity

================================================================================
WHAT L4/L5 LOOKS LIKE FOR C:
================================================================================

L4: Can write production C code that's safe, portable, and efficient.
    Understands the C memory model deeply, can use advanced features
    (variadic functions, designated initializers, flexible array members,
    _Generic, inline functions). Can work with C codebases of 100K+ lines.
    Understands ABI compatibility, FFI, cross-compilation. Can read and
    understand C standard sections relevant to their work.

L5: Can contribute to C standard library implementations, understand C at the
    language specification level, can design C APIs that are safe and ergonomic,
    can teach C and explain why certain patterns are dangerous. Understands the
    history of C (K&R C, ANSI C, C89, C99, C11, C17, C23) and what each version
    added.

================================================================================
2.5 C++ (L1 → L3 target, modern C++17/20 subset)
================================================================================

WHAT L3 LOOKS LIKE FOR C++:

MODERN C++ FUNDAMENTALS:
- Uses C++17/20 features: auto, range-for, lambdas, smart pointers, move
  semantics, constexpr, std::optional, std::variant, std::any, std::filesystem
- Understands value types vs reference types, move vs copy, rvalue references
- Can use the STL: vector, string, map, unordered_map, set, algorithms
  (sort, find, transform, accumulate), iterators, ranges (C++20)
- Understands RAII: resource acquisition is initialization, smart pointers
  (unique_ptr, shared_ptr, weak_ptr), scope guards

CONCURRENCY:
- Can use std::thread, std::mutex, std::lock_guard, std::unique_lock
- Understands std::async, std::future, std::promise
- Knows C++ memory model: atomic operations, memory_order, data races
- Understands the difference between std::thread and other concurrency models

TEMPLATES (BASIC):
- Can read and write function templates and class templates
- Understands template specialization, SFINAE (basic), concepts (C++20)
- Knows when templates are useful vs when they make code unreadable

ERROR HANDLING:
- Understands exceptions: try/catch, exception safety guarantees (basic,
  strong, no-throw), when to use exceptions vs error codes
- Can use std::expected (C++23) or std::optional for error handling
- Understands RAII as the foundation of exception safety

================================================================================
WHAT L4/L5 LOOKS LIKE FOR C++:
================================================================================

L4: Can design and implement large C++ systems. Uses templates deeply
    (template metaprogramming basics, type traits, perfect forwarding,
    universal references, reference collapsing). Understands move semantics
    completely. Can profile and optimize C++ code (perf, valgrind, vtune).
    Understands the compilation model deeply (ODR, include model, linking).
    Can read and understand Boost or STL source.

L5: Can contribute to C++ standards (WG21), understand the language at the
    specification level, can implement template libraries that other developers
    use, understands the history and design of C++ (Stroustrup's decisions,
    committee process, C++98→20 evolution), can explain C++'s design philosophy
    and trade-offs compared to Rust, Java, C#, D.

================================================================================
2.6 C# (L1 → L3 target)
================================================================================

WHAT L3 LOOKS LIKE FOR C#:

.NET RUNTIME/ECOSYSTEM:
- Understands the CLR: managed code, JIT compilation, garbage collection
  (generational GC, object allocation, finalization)
- Can use Visual Studio or VS Code + C# extension effectively
- Understands .NET (not just C#): the standard library, the framework
  landscape (ASP.NET Core, Entity Framework, MAUI/Xamarin)

LANGUAGE FEATURES:
- Can use all major C# features: LINQ, async/await, generics, delegates,
  events, lambda expressions, extension methods, properties, indexers
- Understands nullable reference types (C# 8+)
- Can use records, pattern matching (switch expressions, property patterns),
  init-only properties, required members
- Understands LINQ: query syntax vs method syntax, deferred execution,
  IQueryable vs IEnumerable, expression trees
- Can use async/await correctly: Task, Task<T>, ValueTask, cancellation,
  avoiding async void

DEPENDENCY INJECTION/ARCHITECTURE:
- Understands ASP.NET Core's DI system
- Can design services with proper lifetimes (Transient, Scoped, Singleton)
- Understands middleware pipeline, filters, model binding
- Can use Entity Framework Core: DbContext, migrations, relationships,
  LINQ to Entities, performance considerations

================================================================================
WHAT L4/L5 LOOKS LIKE FOR C#:
================================================================================

L4: Can build production ASP.NET Core applications, design clean architectures,
    write performance-sensitive code (Span<T>, memory<T>, stackalloc, struct
    vs class tradeoffs), use advanced .NET features (reflection, dynamic,
    threading, parallel programming). Can read .NET runtime source.

L5: Can contribute to dotnet/runtime or major .NET libraries, understand CLR
    internals deeply, can design .NET libraries that others use, understand
    IL and can read/write it, understand JIT optimization, can teach C# deeply.

================================================================================
2.7 JAVA (L1 → L3 target)
================================================================================

WHAT L3 LOOKS LIKE FOR JAVA:

JVM/ECOSYSTEM:
- Understands the JVM: bytecode, classloading, JIT compilation, garbage
  collection (G1, ZGC basics), object layout on heap
- Can use IntelliJ IDEA or Eclipse effectively
- Understands Maven/Gradle for builds and dependency management
- Knows the Java standard library well: Collections, Streams, Concurrency,
  IO/NIO, Networking, Reflection

LANGUAGE FEATURES:
- Can use modern Java (Java 17/21): records, sealed classes, pattern matching
  for switch, text blocks, var, switch expressions
- Understands generics: type erasure, wildcards (extends, super), generic
  methods, type inference
- Can use the Collections framework effectively: List, Set, Map, their
  implementations, when to use which
- Understands Java's approach to OOP: interfaces, abstract classes, inheritance,
  composition vs inheritance, immutability patterns

STREAMS/LINQ ANALOGUE:
- Can use Streams API: filter, map, reduce, collect, flatMap, groupingBy
- Understands lazy evaluation in streams, parallel streams (and when NOT to use)
- Can write clean stream pipelines

CONCURRENCY:
- Understands java.util.concurrent: ExecutorService, CompletableFuture,
  ConcurrentHashMap, AtomicInteger, CountDownLatch, CyclicBarrier, Semaphore
- Can use synchronized, ReentrantLock, ReadWriteLock, StampedLock
- Understands the Java memory model: volatile, final field semantics,
  happens-before relationships
- Knows when to use virtual threads (Java 21+) vs platform threads

================================================================================
WHAT L4/L5 LOOKS LIKE FOR JAVA:
================================================================================

L4: Can build production Spring Boot applications, design clean architectures,
    write performance-sensitive code (off-heap memory, NIO, JIT-friendly code),
    understand JVM tuning (GC, heap sizing, JIT flags). Can read JVM source
    or at least HotSpot source for relevant components.

L5: Can contribute to OpenJDK, understand JVM internals deeply (bytecode
    verification, JIT compilation tiers, GC algorithms), can design Java
    libraries that others use, can teach Java deeply and explain JVM behavior.

================================================================================
2.8 JAVASCRIPT (L2 → L4 target)
================================================================================

WHAT L3 LOOKS LIKE FOR JAVASCRIPT:

CORE LANGUAGE:
- Deep understanding of JavaScript's type system: primitives (string, number,
  boolean, null, undefined, symbol, bigint) vs objects, type coercion rules
  (== vs ===, truthy/falsy, ToPrimitive, ToNumber, ToString)
- Understanding of functions: declarations vs expressions, arrow functions,
  closures, this binding (implicit, explicit with call/apply/bind, arrow
  functions don't have their own this), arguments object
- Can use ES6+ features fluently: let/const, destructuring, spread/rest,
  template literals, modules (import/export), classes, promises, async/await
- Understands the prototype chain: [[Prototype]], constructor functions,
  Object.create, class syntax as sugar over prototypes

ASYNC/EVENT LOOP:
- Deep understanding of the event loop: call stack, task queue (macrotasks),
  microtask queue, how they interact
- Understands promises: states (pending, fulfilled, rejected), chaining,
  error propagation, Promise.all, Promise.race, Promise.allSettled
- Can use async/await correctly, understands that async functions always
  return promises
- Can debug async issues: unhandled promise rejections, race conditions,
  callback hell (and how promises/async-await fix it)

DOM/BROWSER:
- Can manipulate the DOM: selecting elements, creating/modifying elements,
  event handling (bubbling, capturing, delegation), forms
- Understands browser APIs: fetch, localStorage, sessionStorage, cookies,
  IntersectionObserver, requestAnimationFrame
- Can work with browser devtools: elements panel, console, network panel,
  performance panel, debugger

TOOLING/ECOSYSTEM:
- Can use npm/yarn/pnpm for package management
- Understands bundlers: Webpack, Vite, esbuild — what they do and why
- Can use a linter (ESLint) and formatter (Prettier)
- Understands JavaScript testing: Jest, Vitest, testing-library

================================================================================
WHAT L4/L5 LOOKS LIKE FOR JAVASCRIPT:
================================================================================

L4: Can build production web applications. Deep understanding of browser
    internals, performance optimization (rendering pipeline, layout thrashing,
    memoization, code splitting), advanced asynchronous patterns, design
    patterns in JavaScript (module, observer, factory, singleton), can read
    and understand library source (React, Express, etc.). Can use Node.js
    for server-side development.

L5: Can contribute to JavaScript engines (V8, SpiderMonkey) or major libraries,
    understand ECMAScript specification, can teach JavaScript and explain
    its quirks (this, prototypes, coercion, event loop) clearly. Understands
    the history of JavaScript (Netscape, ECMA, ES3→ES6→ES2016+ evolution).

================================================================================
2.9 TYPESCRIPT (L1 → L3 target)
================================================================================

NOTE: TypeScript mastery requires JavaScript mastery first. L1 in TypeScript
with L2 in JavaScript means the JavaScript foundation is being built.

WHAT L3 LOOKS LIKE FOR TYPESCRIPT:

TYPE SYSTEM:
- Can use all major TypeScript features: interfaces, type aliases, unions,
  intersections, generics, tuples, enums, literal types, indexed access types
- Understands type inference: when TS infers types, when it falls back to any
- Can use utility types: Partial, Required, Pick, Omit, Record, ReturnType,
  Parameters, ConstructorParameters, Extract, Exclude, NonNullable, Uppercase/
  Lowercase/PascalCase/Snapshot
- Understands type narrowing: discriminated unions, type guards, instanceof,
  as const, satisfies operator
- Understands the difference between interface and type alias, when to use each

GENERICS:
- Can write generic functions and types: generic constraints, default types,
  conditional types (basic), mapped types (basic)
- Understands variance in TypeScript: covariance, contravariance, invariance
- Can use generic constraints to express relationships between types

ADVANCED TYPES:
- Can read and write conditional types: T extends U ? X : Y
- Understands mapped types: creating new types by transforming property types
- Can use template literal types (TS 4.1+)
- Understands infer keyword in conditional types
- Can design type-safe APIs using the type system

JSX/REACT:
- Can use JSX with TypeScript: typing props, children, event handlers
- Understands React's TypeScript patterns: generic components, conditional
  props, discriminated unions for component props
- Can use React hooks with proper typing

================================================================================
WHAT L4/L5 LOOKS LIKE FOR TYPESCRIPT:
================================================================================

L4: Can build large, type-safe applications. Designs libraries with expressive
    types that prevent misuse at compile time. Understands TypeScript's type
    system deeply — what it can express and what it can't (TypeScript's type
    system is not sound). Can configure TypeScript precisely (strict mode,
    target, module, paths, composite projects). Can debug tricky type errors.

L5: Can contribute to the TypeScript compiler (microsoft/TypeScript), understand
    the type checker implementation, can design type systems for DSLs, understand
    the theory behind TypeScript's type system (it's based on structural typing
    with gradual typing). Can teach TypeScript at an advanced level.

================================================================================
2.10 BASH (L3 → L4/L5 target)
================================================================================

WHAT L4 LOOKS LIKE FOR BASH:

ADVANCED SCRIPTING:
- Can write complex, robust bash scripts with proper error handling
- Uses set -euo pipefail consistently and understands what each does
- Can handle arguments properly: getopts, positional parameters, shifting
- Writes functions in bash and understands scope (local variables)
- Can trap signals: trap for cleanup on exit, Ctrl+C handling
- Can use here documents, process substitution, command substitution effectively

POSIX PORTABILITY:
- Understands the difference between bash and POSIX sh
- Can write scripts that work on both bash and POSIX-compliant shells
- Knows which bash features are not POSIX: arrays, [[ ]], process substitution,
  certain string operations
- Understands shell portability issues across bash versions

TEXT PROCESSING:
- Proficient with grep, sed, awk for text processing
- Can use regular expressions in bash contexts
- Understands when to use bash string operations vs. when to call sed/awk
- Can parse structured text (CSV, log files, config files) in bash

SECURITY:
- Understands bash security issues: word splitting, glob expansion, command
  injection, quoting rules (always quote variables)
- Understands potential for unintended code execution via eval, source, backticks
- Knows safe practices for handling untrusted input in bash scripts

DEBUGGING:
- Can debug bash scripts: set -x for tracing, trap DEBUG, using shellcheck
- Understands common bash pitfalls and how to avoid them (Useless Use of Cat,
  scalar vs array confusion, exit code handling in pipelines)

================================================================================
WHAT L5 LOOKS LIKE FOR BASH:
================================================================================

L5: Can write bash scripts that are POSIX-compliant and work across different
    Unix systems. Understands the bash source code or at least the POSIX shell
    specification. Can teach bash deeply, explain the quoting rules, the
    expansion order (brace expansion → tilde expansion → parameter expansion →
    command substitution → arithmetic expansion → word splitting → pathname
    expansion), and why certain patterns are dangerous. Can design shell tooling
    that other developers use.

================================================================================
2.11 POWERSHELL (L1 → L3 target)
================================================================================

WHAT L3 LOOKS LIKE FOR POWERSHELL:

CORE CONCEPTS:
- Understands PowerShell's object pipeline — unlike bash's text pipeline,
  PowerShell passes .NET objects between commands
- Understands cmdlets, functions, scripts, modules
- Can use Get-Command, Get-Help, Get-Member effectively
- Understands the execution policy and why it exists

SCRIPTING:
- Can write PowerShell scripts with functions, parameters (with validation),
  error handling (try/catch/finally, $ErrorActionPreference)
- Can use the pipeline effectively: filtering, sorting, grouping, selecting
- Understands PowerShell's type system: [int], [string], [object], custom
  types, PSCustomObject
- Can work with .NET types from PowerShell (new-object, static method access)

ADMINISTRATION:
- Can manage Windows systems: services, processes, files, registry, event logs
- Can query WMI/CIM for system information
- Understands remoting: Invoke-Command, Enter-PSSession, sessions
- Can use PowerShell for Azure/AWS administration (Az module, AWS Tools)

================================================================================
WHAT L4/L5 LOOKS LIKE FOR POWERSHELL:
================================================================================

L4: Can build production PowerShell modules, design cmdlets with proper
    parameter sets and pipelines, write advanced functions, create binary
    modules (C#), understand PowerShell's hosting model. Can write scripts
    that integrate with enterprise systems (Active Directory, Exchange,
    SharePoint, Azure).

L5: Can contribute to PowerShell (PowerShell/PowerShell repo), understand
    the PowerShell engine internals, can teach PowerShell deeply, understand
    PowerShell's design philosophy and trade-offs compared to bash, Python,
    etc.

================================================================================
2.12 SQL (L3 → L4 target)
================================================================================

WHAT L4 LOOKS LIKE FOR SQL:

QUERY OPTIMIZATION:
- Can read and understand query execution plans (EXPLAIN, EXPLAIN ANALYZE)
- Understands indexes: B-tree, hash, covering indexes, index scans vs sequential
  scans, when indexes help and when they hurt
- Can optimize slow queries: identifying bottlenecks, rewriting queries,
  adding appropriate indexes, understanding cardinality estimates
- Understands the cost of JOINs, subqueries, CTEs, window functions

TRANSACTION ISOLATION:
- Deep understanding of transaction isolation levels: Read Uncommitted,
  Read Committed, Repeatable Read, Serializable (and their anomalies:
  dirty reads, non-repeatable reads, phantom reads, serialization anomalies)
- Understands MVCC (Multi-Version Concurrency Control) — how PostgreSQL,
  MySQL, Oracle implement it
- Can reason about deadlock scenarios and how to prevent them

SCHEMA DESIGN:
- Can design normalized schemas (1NF, 2NF, 3NF, BCNF) and understand when
  denormalization is appropriate
- Understands foreign keys, constraints (CHECK, UNIQUE, NOT NULL, PRIMARY KEY),
  cascading behaviors
- Can design schemas for specific access patterns: OLTP vs OLAP, read-heavy
  vs write-heavy, time-series data, hierarchical data
- Understands partitioning strategies, sharding concepts

ADVANCED SQL FEATURES:
- Can use window functions: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, NTILE,
  aggregate window functions, framing clauses (ROWS, RANGE, GROUPS)
- Can use CTEs (Common Table Expressions), recursive CTEs
- Understands JSON support in modern SQL databases (PostgreSQL JSONB, MySQL JSON)
- Can use database-specific features where appropriate (PostgreSQL extensions,
  MySQL features, SQL Server T-SQL)

MULTIPLE DATABASES:
- Understands the differences between major SQL databases: PostgreSQL, MySQL,
  SQLite, SQL Server, Oracle
- Knows which features are standard SQL and which are database-specific
- Can work with at least 2 different database engines competently

================================================================================
WHAT L5 LOOKS LIKE FOR SQL:
================================================================================

L5: Can design large-scale database systems, understand query optimization at
    the database engine level (how the query planner works, cost-based optimization,
    statistics, histograms), can teach SQL deeply, can read database source code
    for relevant components, understands the theory of relational algebra and
    how it maps to SQL. Can design schemas that scale to millions/billions of
    rows. Understands the CAP theorem and trade-offs in database design.

================================================================================
2.13 SYSTEMS PROGRAMMING (L2 → L4 target)
================================================================================

NOTE: "Systems programming" is an umbrella skill, not a specific language.
It spans C, C++, Rust, and potentially Assembly. The daughter needs to define
what this skill covers and how it relates to the individual language skills.

WHAT L3 LOOKS LIKE FOR SYSTEMS PROGRAMMING:

CONCEPTS:
- Understands what "systems programming" means: programming close to the
  hardware/OS, manual resource management, performance-critical code,
  infrastructure software
- Understands the relationship between high-level code and what the machine
  actually does: memory layout, CPU caches, branch prediction, instruction
  pipelines
- Can read and understand C code (pointers, memory management, structs)
- Understands linking: static vs dynamic, symbols, relocation, ABI

OPERATING SYSTEM INTERACTION:
- Can use system calls: read, write, open, close, fork, exec, wait
- Understands processes vs threads, process lifecycle, signals
- Understands memory management from the OS perspective: virtual memory,
  paging, mmap, brk/sbrk, shared memory
- Can use basic OS interfaces: file descriptors, sockets, pipes

TOOLING:
- Can use GDB/LLDB for debugging C/C++/Rust
- Can use valgrind, AddressSanitizer, LeakSanitizer for memory debugging
- Can use perf, strace, ltrace for system-level debugging
- Understands core dumps and how to analyze them

================================================================================
WHAT L4/L5 LOOKS LIKE FOR SYSTEMS PROGRAMMING:
================================================================================

L4: Can write systems software in C/Rust: network servers, database engines,
    file systems, container runtimes, language runtimes. Understands the OS
    at a deep level: VFS, scheduling, interrupts, virtual memory internals.
    Can profile and optimize systems code. Can read kernel code for relevant
    subsystems. Can use advanced debugging tools (ftrace, eBPF, systemtap).

L5: Can contribute to the Linux kernel or major systems projects, understand
    systems programming at the hardware/architecture level (CPU microarchitecture,
    memory hierarchy, MMU, TLB), can teach systems programming, understands
    the history of systems programming (Unix, C, the evolution of systems
    languages from C to Rust).

================================================================================
PART 2 END
================================================================================
