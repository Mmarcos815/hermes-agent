# ===========================================================================
# RUST DEEP STUDY — OWNERSHIP, BORROWING & LIFETIMES
# ===========================================================================
# A theoretical deep dive, not a "how to use" tutorial.
# Goal: understand WHY Rust does what it does, not just HOW.
# Date: 2026-08-19
# Status: Deep study in progress
# Source material: The Rust Book, Rustonomicon, Rust Reference,
#                  academic papers on ownership types, personal study

## WHY THIS STUDY MATTERS

Ownership, borrowing, and lifetimes are NOT just Rust syntax rules.
They are a fundamental approach to memory safety that Rust invented
and proved workable. Understanding them deeply means:

- You understand what memory safety IS and what it costs
- You understand what Rust Guarantees and what it DOESN'T
- You understand why the borrow checker rejects your code (not just
  "the borrow checker said no" but "here's what I violated")
- You can reason about Rust code at a deeper level than syntax

This study targets L2 understanding: can explain the concepts,
can reason about them, can connect them to the bigger picture.

================================================================================
SECTION 1: THE PROBLEM RUST IS SOLVING
================================================================================

### Memory Management: The Three Approaches

Programming languages handle memory in three broad approaches:

1. **Garbage Collection (GC)**
   - The runtime tracks which objects are reachable and frees the
     unreachable ones.
   - Examples: Java, Go, Python, JavaScript, C#, Ruby
   - Trade-off: easy for the programmer, but the GC has runtime cost
     (pauses, CPU overhead, memory overhead). GC-enabled languages
     typically need more memory and have less predictable latency.

2. **Manual Memory Management**
   - The programmer explicitly allocates and frees memory.
   - Examples: C, C++ (without smart pointers)
   - Trade-off: maximum control and performance, but errors are common:
     use-after-free, double-free, memory leaks, buffer overflows.
     These are not just bugs — they are SECURITY vulnerabilities.
     Most security vulnerabilities in C/C++ are memory safety errors.

3. **Ownership + Borrowing (Rust's approach)**
   - The compiler enforces memory safety at compile time through a
     system of ownership rules.
   - No GC, no manual free, no runtime memory safety overhead.
   - Trade-off: a learning curve (the borrow checker), and some
     patterns are harder to express.

Rust's core insight: **memory safety can be enforced at compile time
through a type system, without runtime overhead, without a garbage
collector.**

This is a BIG claim. Let's understand what it means.

================================================================================
SECTION 2: WHAT OWNERSHIP IS
================================================================================

### The Core Principle

Every value in Rust has exactly ONE owner. When the owner goes out
of scope, the value is dropped (freed).

This is a simple rule but it has profound implications.

### What "Ownership" Actually Means

Ownership is NOT just "who frees the memory." It's a set of rules
about how values can be used, moved, and referenced:

**Rule 1: Each value has one owner.**
- The owner is the variable that holds the value (or the scope that
  contains it).
- When the owner goes out of scope, the value is dropped.
- You cannot have two "owners" of the same value — that would mean
  two places that think they're responsible for freeing it, leading
  to double-free.

**Rule 2: Ownership can be transferred (moved).**
- Assigning a value to another variable transfers ownership.
- After the move, the original variable can no longer be used.
- This prevents use-after-free: if you can't use the original
  variable after moving, you can't access freed memory.

**Rule 3: Borrowing is temporary, scoped access without ownership.**
- You can lend a value to another piece of code temporarily.
- The lender retains ownership; the borrower just gets to use it
  for a limited time.
- Borrowing comes in two forms:
  - Immutable borrow (&T): many readers allowed, no modifications
  - Mutable borrow (&mut T): one writer, no other readers or writers
- Borrows cannot outlive the owner — you can't keep a reference to
  something after it's been dropped.

**Rule 4: Values must be dropped exactly once.**
- When the owner goes out of scope, Drop is called.
- If ownership was moved, the new owner drops it.
- If ownership was borrowed, the original owner still drops it.
- No double-free, no use-after-free, no leaks (unless you explicitly
  use something likeRc or Arc with cyclic references — but even then,
  Rust makes leaks explicit, not accidental).

### What Ownership Prevents

Ownership prevents entire categories of bugs at compile time:

- **Use-after-free**: You can't use a value after it's been dropped,
  because you can't access it after moving or after the owner's scope
  ends.
- **Double-free**: Only one owner exists, so only one drop happens.
- **Data races**: Rust's borrowing rules (one mutable OR many immutable)
  prevent concurrent access to mutable data without synchronization.
- **Dangling pointers**: References can't outlive their referent (this
  is what lifetimes enforce).

These are NOT runtime checks. They are compile-time guarantees. The
compiler PROOFS that your code is memory-safe (in the safe subset).

================================================================================
SECTION 3: MOVE SEMANTICS — THE MECHANISM
================================================================================

### What a Move Is

In Rust, assigning a variable to another variable doesn't copy the
value by default. It MOVES it.

    let s1 = String::from("hello");
    let s2 = s1;   // MOVE: s1's ownership transfers to s2
    // s1 can no longer be used here — it's been moved

Why? Because String owns heap-allocated data (the string contents).
If Rust copied s1, you'd have two variables thinking they own the
same heap allocation. When both go out of scope, both would try to
free it — double-free.

So Rust doesn't copy. It moves. After the move, only s2 owns the
data. s1 is "used up."

### What Gets Moved vs What Gets Copied

Rust has two traits that determine this:

- **Copy**: types where copying is cheap and safe (all data is on the
  stack, no heap allocation). Examples: integers, floats, booleans,
  characters, tuples of Copy types, arrays of Copy types.
  - Copy types implement the Copy trait.
  - When you assign a Copy type, it's copied (bitwise), not moved.
  - The original variable is still usable.

- **Clone**: types where you explicitly want a deep copy. Examples:
  String, Vec, HashMap, anything with heap-allocated data.
  - Clone types may OR may not implement Copy (usually not).
  - You call .clone() to make a deep copy.
  - Clone is explicit — you have to ask for it.

The rule: if a type implements Copy, assignment copies. If it doesn't,
assignment moves.

    let x = 5;        // i32 implements Copy
    let y = x;        // COPY: x is still usable, y = 5
    println!("{x}");  // OK — x wasn't moved

    let s1 = String::from("hello");  // String does NOT implement Copy
    let s2 = s1;       // MOVE: s1's ownership goes to s2
    // println!("{s1}");  // ERROR — value borrowed here after move

### Why Rust Chose Move Semantics

Move semantics prevent the most common memory safety error in manual
memory management: two owners of the same heap allocation.

In C, you'd write:

    char *s1 = strdup("hello");
    char *s2 = s1;  // Two pointers to the same memory
    free(s1);       // Frees the memory
    // s2 is now a dangling pointer — use-after-free if used

In Rust, this is impossible (in safe code) because ownership can't
be duplicated without explicit cloning.

### Moves and Scope

When a value moves into a new scope (e.g., into a function, into a
loop body, into a new block), the old scope can no longer use it.
This is how Rust ensures that a value is dropped exactly once:
whoever has ownership at the end of their scope drops it.

    {
        let s = String::from("hello");  // s owns the string
        // ... use s ...
    }   // s goes out of scope → dropped here

    fn takes_ownership(s: String) {
        // s owns the string now
        // ... use s ...
    }   // s goes out of scope → dropped here

    // Can't use s after calling takes_ownership — it was moved in

This is the mechanism that makes ownership work. The compiler tracks
ownership through assignments, function calls, and scope boundaries.

================================================================================
SECTION 4: BORROWING — TEMPORARY, SCOPED ACCESS
================================================================================

### What Borrowing Is

Borrowing is the mechanism for lending a value without transferring
ownership. When you borrow, you get a reference (&T or &mut T) that
lets you use the value for a limited time, but ownership stays with
the original owner.

    let s = String::from("hello");
    let len = calculate_length(&s);  // &s is an immutable borrow
    println!("{s}");                  // s is still usable — ownership never left

    fn calculate_length(s: &String) -> usize {
        s.len()   // can read s, but can't modify it (it's &String, not &mut String)
    }              // s goes out of scope here, but it's just a reference —
                   // the original String is not dropped

### Why Borrowing Exists

Without borrowing, every time you wanted to use a value in a function,
you'd have to move it in (transferring ownership) and then move it
back (or clone it). This would be:
- Clumsy: you'd constantly be cloning and moving
- Inefficient: cloning heap data is expensive
- Error-prone: moving and moving back is easy to get wrong

Borrowing gives you a way to say: "I need to use this value, but I
don't want to take ownership of it. Just let me look at it (or modify
it) for a while."

### The Two Borrow Types

**Immutable borrow (&T):**
- You can read the value but not modify it.
- You can have MANY immutable borrows at the same time.
  - This is safe: many readers, no writers, no data races.
- Example: &String, &i32, &Vec<T>

**Mutable borrow (&mut T):**
- You can read AND modify the value.
- You can have ONLY ONE mutable borrow at a time (and no other
  borrows of any kind).
  - This is safe: one writer, no readers, no data races.
- Example: &mut String, &mut Vec<T>, &mut i32

### The Borrowing Rules (The "One Mutable OR Many Immutable" Rule)

This is the heart of Rust's thread safety (and memory safety) guarantee:

- You can have EITHER:
  - One mutable borrow (&mut T), OR
  - Any number of immutable borrows (&T)
- You CANNOT have both at the same time.

This rule applies within a single scope. It's enforced by the borrow
checker.

Why? Because:
- If you have a mutable borrow, you can modify the value. If someone
  else also has a reference (mutable or immutable) and reads or writes
  it, you get a data race or inconsistent state.
- If you have immutable borrows, you can read the value. If someone
  else mutates it while you're reading, you get a data race or you
  read modified data unexpectedly.

The rule prevents data races at compile time. No runtime overhead.

### Borrow Scope — When Borrows End

A borrow lasts for a SCOPE, not just a single statement. The borrow
checker tracks the scope of each borrow and ensures that borrows don't
overlap in forbidden ways.

    let mut s = String::from("hello");

    {
        let r1 = &s;     // immutable borrow starts
        let r2 = &s;     // another immutable borrow — OK (many immutable)
        println!("{r1} {r2}");
    }   // r1 and r2 go out of scope — borrows end

    {
        let r3 = &mut s;  // mutable borrow starts
        r3.push_str(", world");
    }   // r3 goes out of scope — mutable borrow ends

    // Now we can borrow again (mutable or immutable)

The key: borrows have a scope, and the borrow checker enforces that
within any scope, the borrowing rules are satisfied.

### References Are NOT Pointers (Exactly)

Rust references (&T, &mut T) are similar to C pointers, but they're
not the same:

- A C pointer can point to anything, can be null, can be dangling,
  can be used to write anywhere.
- A Rust reference is guaranteed to be valid (not null, not dangling)
  for its entire lifetime. The compiler enforces this.

This guarantee is what makes Rust references safe. You can't have a
dangling reference in safe Rust — the compiler won't let you create
one.

================================================================================
SECTION 5: LIFETIMES — WHY THEY EXIST
================================================================================

### The Problem Lifetimes Solve

A reference is only valid as long as the value it points to exists.
If the value is dropped, the reference becomes dangling.

Rust needs a way to ensure that references never outlive the values
they point to. Lifetimes are the mechanism.

### What a Lifetime Is

A lifetime is a compile-time concept that represents the SCOPE during
which a reference is valid. It's not a runtime thing — there's no
lifetime value at runtime. It's a type-level annotation that the
borrow checker uses to verify that references don't outlive their
referents.

Think of a lifetime as a label on a reference that says "this
reference is valid for this scope." The borrow checker ensures that
you never use the reference outside that scope.

### Lifetime Elision — When You Don't Need to Write Them

For simple cases, Rust can figure out lifetimes automatically. This
is called lifetime elision. The three elision rules are:

1. Each parameter that is a reference gets its own lifetime.
2. If there's exactly one input lifetime parameter, that lifetime is
   assigned to all output lifetime parameters.
3. If there are multiple input lifetime parameters but one of them is
   &self or &mut self (a method), the self lifetime is assigned to
   all output lifetime parameters.

These rules cover the vast majority of cases. You only need to write
explicit lifetimes when the compiler can't figure them out from these
rules.

### When Explicit Lifetimes Are Needed

You need explicit lifetimes when the compiler can't determine the
relationship between input and output references. The classic case:

    fn longest(x: &str, y: &str) -> &str {
        if x.len() > y.len() { x } else { y }
    }

This won't compile without lifetimes because the compiler doesn't
know whether the returned reference should have the lifetime of x or
y. You need to tell it:

    fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
        if x.len() > y.len() { x } else { y }
    }

This says: "both x and y have lifetime 'a, and the returned reference
also has lifetime 'a." The caller must ensure that both x and y live
at least as long as 'a, and the returned reference is valid for 'a.

### What Lifetimes Actually Prove

Lifetimes prove that references don't outlive their referents. The
borrow checker verifies that for every reference, the lifetime
annotation ensures the reference is only used while the referent is
alive.

This is a STATIC guarantee. The compiler checks it at compile time.
If the code compiles, the references are valid (in safe Rust).

### Lifetime Subtyping

Sometimes one lifetime needs to outlive another. Lifetime subtyping
captures this:

    fn foo<'long, 'short>(x: &'long str, y: &'short str) -> &'long str
    where 'long: 'short   // 'long outlives 'short
    {
        x  // return x, which has lifetime 'long
    }

The constraint `'long: 'short` means "'long outlives 'short" — 'long
is a supertype of 'short. This is used when you need to express that
one reference lives longer than another.

### Static Lifetime

There's a special lifetime: `'static`. It means "this reference lives
for the entire program." String literals have lifetime `'static`:

    let s: &'static str = "hello";  // string literals are 'static

This is because string literals are embedded in the executable's data
segment and live for the entire program. They're never dropped.

`'static` is also used for types that own their data and never borrow:
`String`, `Vec`, owned types. When you see `T: 'static`, it means "T
doesn't contain any non-static references."

================================================================================
SECTION 6: HOW THE BORROW CHECKER WORKS (CONCEPTUALLY)
================================================================================

### What the Borrow Checker Does

The borrow checker is the part of the Rust compiler that enforces the
ownership and borrowing rules. It operates on the MIR (Mid-level IR)
— an intermediate representation of your code that the compiler
generates after type checking.

The borrow checker's job:

1. **Track ownership**: for every value, track who owns it and where
   it moves.
2. **Track borrows**: for every reference, track when it's created,
   what it references, and when it's last used.
3. **Check borrow rules**: ensure that within any scope, the borrowing
   rules are satisfied (one mutable OR many immutable).
4. **Check lifetimes**: ensure that references don't outlive their
   referents (the lifetime annotations are satisfied).
5. **Reject invalid code**: if any of these checks fail, the code
   doesn't compile.

### What the Borrow Checker DOESN'T Do

- The borrow checker does NOT do runtime checks. It's compile-time only.
- The borrow checker does NOT prevent ALL memory safety issues — only
  the ones that can be detected at compile time through ownership and
  borrowing. Unsafe Rust, FFI, cyclic Rc/Arc references, and certain
  cells (RefCell, UnsafeCell) can still cause runtime issues.
- The borrow checker does NOT guarantee thread safety by itself — that
  requires Send and Sync (more on this later).

### Why the Borrow Checker Rejects Code

When the borrow checker rejects your code, it's because one of these
is true:

- You're trying to use a value after it's been moved (use-after-move).
- You're trying to have both a mutable and an immutable borrow at the
  same time (violation of the borrowing rules).
- You're trying to have two mutable borrows at the same time (violation
  of the borrowing rules).
- A reference would outlive its referent (lifetime violation).
- You're trying to mutate something that's immutably borrowed.
- You're trying to move a value that's borrowed.

The error messages in Rust (especially in recent versions) are very
good at telling you WHICH of these is the problem and WHERE. Learning
to read borrow checker errors is a skill in itself.

### Non-Lexical Lifetimes (NLL) — The Modern Borrow Checker

In older Rust (before 2018), lifetimes were lexical: a borrow lasted
for the entire scope where it was declared. This was too restrictive.

Modern Rust (2018+) uses Non-Lexical Lifetimes (NLL): the borrow
checker tracks the ACTUAL last use of a borrow, not just the scope.
This allows more code to compile.

    let mut s = String::from("hello");
    let r = &s;           // borrow starts
    println!("{r}");     // last use of r
    // r is no longer used after this point
    let r2 = &mut s;     // OK — r's borrow ended at its last use, not at
                          // the end of the scope
    r2.push_str(", world");

Without NLL, r would be considered borrowed until the end of the
scope, and the mutable borrow would be rejected. With NLL, the
borrow checker sees that r is never used after the println, so the
borrow effectively ends there.

NLL makes Rust more ergonomic without sacrificing safety.

================================================================================
SECTION 7: WHAT OWNERSHIP DOESN'T SOLVE
================================================================================

### Unsafe Rust

Rust has an `unsafe` keyword that opts out of compile-time safety
checks. In unsafe blocks, you can:
- Dereference raw pointers (*const T, *mut T)
- Call unsafe functions (FFI, compiler intrinsics)
- Implement unsafe traits
- Mutate static variables

This is necessary for low-level work (FFI, OS interfaces, performance
critical code), but it comes with a contract: YOU are responsible for
ensuring safety. The compiler won't check it.

Understanding when unsafe is needed vs when it's just convenient is
part of Rust mastery.

### Interior Mutability

Sometimes you need to mutate data through an immutable reference.
Rust's standard borrowing rules don't allow this (you can't mutate
through &T). But sometimes you need to — for example, a reference-
counted pointer that modifies its contents.

Rust provides "interior mutability" types that allow mutation through
shared references by using runtime checks (not compile-time):

- **Cell<T>**: for copy types, allows mutation through &T (no runtime
  checks, just transmutes the bits)
- **RefCell<T>**: for non-copy types, does runtime borrow checking
  (panics if you violate the rules at runtime)

These are useful but come with runtime cost and the possibility of
runtime panics. They're the exception, not the rule.

### Reference-Counted Pointers (Rc, Arc)

Rc<T> (single-threaded) and Arc<T> (thread-safe) allow multiple
"owners" of the same data by using reference counting at runtime.

    use std::rc::Rc;
    let s = Rc::new(String::from("hello"));
    let s2 = Rc::clone(&s);   // increments ref count, not a move
    let s3 = Rc::clone(&s);   // increments ref count again
    // All three can access the string — ref count is 3
    // When all three go out of scope, the string is freed

This is a form of shared ownership, but it's EXPLICIT (you choose to
use Rc/Arc) and it uses runtime reference counting (not compile-time
ownership). The trade-off: runtime overhead (ref count increments/
decrements) and the possibility of reference cycles (which cause
memory leaks — Rc doesn't have a GC to detect cycles).

Arc<T> is the thread-safe version (atomic reference counting). It's
what you use when you need shared ownership across threads.

### The Limits of Compile-Time Safety

Rust's ownership system prevents certain classes of bugs at compile
time, but it doesn't prevent ALL bugs:

- **Logic errors**: Rust doesn't prevent you from writing code that
  does the wrong thing. It only prevents memory safety and data race
  issues (in safe Rust).
- **Panics**: Rust code can panic (unwrap on None, out-of-bounds
  access, division by zero, etc.). Panics are runtime errors.
- **Resource exhaustion**: Rust doesn't prevent memory leaks (in safe
  Rust via Rc cycles), file descriptor exhaustion, etc.
- **Uninitialized memory**: Rust prevents this in safe code (all
  variables are initialized before use), but unsafe code can still
  read uninitialized memory.

The ownership system is a powerful tool, but it's not a silver bullet.

================================================================================
SECTION 8: CONNECTING OWNERSHIP TO THE BIGGER PICTURE
================================================================================

### Ownership and Memory Safety

Rust's ownership system is a compile-time implementation of the
principle that **memory safety requires either:**
- A garbage collector (runtime safety)
- Manual management (programmer discipline — error-prone)
- Compile-time enforcement through a type system (Rust's approach)

Rust chose the third option. The result: memory safety without runtime
overhead, without a GC, without manual memory management errors.

### Ownership and Concurrency

Rust's ownership and borrowing rules ALSO prevent data races at
compile time (in safe code). This is because:

- A data race requires: two threads accessing the same memory, at
  least one writing, without synchronization.
- Rust's borrowing rules prevent having both a mutable reference and
  any other reference at the same time.
- For cross-thread sharing, Rust uses Send and Sync traits to ensure
  that data shared across threads is actually safe to share.

This is "fearless concurrency" — the compiler prevents data races,
so you can write concurrent code without worrying about race conditions
(at least, the ones related to shared mutable state).

### Ownership and API Design

Ownership affects how you design Rust APIs:

- Functions that take ownership consume the value (the caller can't
  use it after). This is clear and explicit.
- Functions that borrow don't consume the value (the caller can still
  use it). This is flexible but requires lifetime annotations.
- Functions that return owned values give ownership to the caller.
- Functions that return references borrow from their inputs — the
  lifetimes must work out.

Good Rust API design makes ownership clear: the caller always knows
whether a function takes ownership, borrows, or returns ownership.

================================================================================
SECTION 9: EVIDENCE CHECKLIST — OWNERSHIP MASTERY (L2)
================================================================================

Can you:

- [ ] Explain ownership in your own words (not just reciting rules)
- [ ] Explain WHY Rust chose move semantics over copy-by-default
- [ ] Explain the difference between Copy and Clone and when each applies
- [ ] Explain the two borrow types (&T vs &mut T) and the rule
      "one mutable OR many immutable"
- [ ] Explain WHY the borrowing rules prevent data races
- [ ] Explain what lifetimes ARE (compile-time concept, not runtime)
- [ ] Explain when explicit lifetimes are needed vs when elision works
- [ ] Explain what 'static lifetime means
- [ ] Read a borrow checker error and understand WHAT rule was violated
      and WHERE
- [ ] Explain what NLL is and why it matters
- [ ] Explain what the borrow checker DOESN'T prevent (unsafe, interior
      mutability, Rc cycles, logic errors)
- [ ] Explain the connection between ownership and memory safety
- [ ] Explain the connection between ownership and concurrency (Send/Sync)

================================================================================
SECTION 10: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand the fundamentals of ownership, borrowing, and
lifetimes, the next topics in the Rust L1→L2 progression are:

1. **Types and Traits** — Rust's type system: enums (Option, Result),
   pattern matching, the standard library traits (Debug, Clone, PartialEq,
   etc.), trait bounds, the Orphan Rule.

2. **Error Handling** — Result<T, E>, Option<T>, the ? operator, error
   design, thiserror, when to use expect vs unwrap.

3. **Collections and Iterators** — Vec, HashMap, iterators, iterator
   adapters, laziness.

4. **Modules and Cargo** — the module system, crate organization, Cargo
   dependencies and workspaces.

5. **Basic Tooling** — cargo, rustfmt, clippy, rustup, reading rustc
   errors.

Each of these builds on the ownership foundation. You can't understand
traits without understanding ownership (trait objects have lifetimes,
generic functions have ownership semantics). You can't understand
iterators without understanding borrowing (iterators borrow from
collections).

I'll continue with these in subsequent study sessions.

================================================================================
END OF OWNERSHIP DEEP STUDY
================================================================================
