# ===========================================================================
# RUST DEEP STUDY — TYPES, TRAITS & THE TYPE SYSTEM
# ===========================================================================
# Date: 2026-08-19
# Status: Deep study in progress
# Companion: rust_ownership_deep_study.md (prerequisite — must understand
#            ownership before this)

## WHY THIS STUDY MATTERS

Rust's type system is what makes ownership work. Traits are Rust's
answer to abstraction: shared behavior, generic programming, and
the mechanism that ties the type system together. Understanding traits
deeply means you understand how Rust achieves polymorphism without
inheritance, how generic code works, and what the compiler knows
about your types.

This is L2 understanding: can explain the concepts, reason about
the type system, understand what the compiler can and can't infer.

================================================================================
SECTION 1: RUST'S TYPE SYSTEM — THE OVERVIEW
================================================================================

Rust's type system has these key characteristics:

1. **Static, strong typing**: every expression has a type known at
   compile time. No implicit type conversions (except a few specific
   cases like integer literals).

2. **Nominal typing with structural elements**: types are primarily
   nominal (named types — structs, enums, traits), but there's structural
   typing in certain places (traits are structural in what they require,
   and some inference uses structural reasoning).

3. **Ownership-aware**: the type system knows about ownership. Types
   like `&T`, `&mut T`, `Box<T>`, `Rc<T>` carry ownership information
   in their types.

4. **Trait-based polymorphism**: Rust uses traits for abstraction,
   not inheritance. There are no class hierarchies. Instead, you
   define traits (shared behavior) and implement them for types.

5. **Generics with monomorphization**: generic code is compiled into
   specialized versions for each concrete type (monomorphization).
   This gives zero-cost abstraction — generic code has no runtime
   overhead compared to hand-written specialized code.

6. **No subtyping (except lifetimes)**: Rust types don't have
   subtyping relationships (a Cat is not a subtype of Animal in the
   OOP sense). The exception is lifetimes: 'long is a subtype of
   'short (longer lifetimes can be used where shorter are expected).

7. **Inference**: Rust infers types aggressively. You rarely need
   to write type annotations. The compiler infers types from context.

================================================================================
SECTION 2: SCALAR AND COMPOUND TYPES
================================================================================

### Scalar Types

- **Integers**: i8, i16, i32, i64, i128, isize (signed);
            u8, u16, u32, u64, u128, usize (unsigned)
            isize/usize are pointer-sized (32-bit or 64-bit depending on platform)

- **Floats**: f32, f64 (IEEE 754)

- **Boolean**: bool (true/false)

- **Character**: char (Unicode scalar value, 4 bytes, NOT a byte)

- **Unit**: () — the empty type, analogous to void in C but it IS a type

### Compound Types

- **Arrays**: [T; N] — fixed-size array of N elements of type T.
  Arrays are Copy if T is Copy. Arrays are stack-allocated.
  Example: let arr: [i32; 5] = [1, 2, 3, 4, 5];

- **Tuples**: (T1, T2, ..., Tn) — fixed-size collection of heterogeneous types.
  Tuples are Copy if all elements are Copy.
  Example: let t: (i32, &str) = (42, "hello");
  Access: t.0, t.1

- **Slice**: &[T] — a reference to a contiguous sequence of T.
  Slices are NOT owned — they borrow from an underlying array or Vec.
  A slice is a fat pointer: (pointer, length). This is why slices are
  not Copy (they're references, and references are not Copy by default
  unless the reference itself is Copy, which &T is).

### The String Types — Critical Distinction

- **String**: owned, heap-allocated, Growable string.
  - String implements Drop (frees heap memory when dropped).
  - String is NOT Copy (it owns heap data).
  - String can be created from &str via .to_string() or String::from().

- **&str**: string slice — a reference to a string's contents.
  - &str is a fat pointer: (pointer to UTF-8 bytes, length).
  - &str borrows from a String or a string literal.
  - &str is Copy (it's just a pointer+length).
  - String literals have type &'static str (they live for the entire
    program and are embedded in the binary).

WHY THIS MATTERS: Every Rust programmer goes through the &str vs String
confusion. The key insight: String owns the data, &str borrows it.
Functions should take &str when they just need to read, and return
String when they create new strings.

================================================================================
SECTION 3: ENUMS — RUST'S POWERHOUSE TYPE
================================================================================

Rust enums are NOT like C enums (which are just named integers).
Rust enums are algebraic data types — they can carry data, and they
can represent "one of several variants," each with different data.

    enum Message {
        Quit,                              // no data
        Move { x: i32, y: i32 },          // struct-like variant
        Write(String),                    // tuple-like variant
        ChangeColor(i32, i32, i32),       // tuple-like variant with 3 fields
    }

This is powerful because you can model complex domain concepts with
types. A Message is ONE OF: Quit, Move, Write, or ChangeColor. The
compiler knows which variants exist, and pattern matching forces you
to handle all of them.

### Option<T> — The Nullable Type That Isn't

    enum Option<T> {
        Some(T),
        None,
    }

Option<T> is Rust's answer to the billion-dollar mistake (null). Instead
of allowing any reference to be null, Rust says: "if a value might not
exist, wrap it in Option<T>." Then the compiler FORCES you to handle
both cases (Some and None) before you can use the value.

This eliminates null pointer dereferences at compile time.

    fn find_user(id: u32) -> Option<User> {
        if id == 42 {
            Some(User { name: "Alice".to_string() })
        } else {
            None
        }
    }

    // Must handle both cases:
    match find_user(42) {
        Some(user) => println!("found: {}", user.name),
        None => println!("not found"),
    }

Or use combinators: .unwrap_or(), .map(), .and_then(), etc.

### Result<T, E> — The Error Type

    enum Result<T, E> {
        Ok(T),
        Err(E),
    }

Result<T, E> is Rust's answer to exceptions. Instead of throwing
exceptions, Rust functions return Result. The caller must handle
both Ok and Err cases. This eliminates unhandled exceptions at
compile time.

================================================================================
SECTION 4: PATTERN MATCHING — THE CONTROL FLOW TOOL
================================================================================

Pattern matching is how you consume enums (and other types) in Rust.
It's exhaustive — the compiler ensures you handle all cases.

    match message {
        Message::Quit => println!("quitting"),
        Message::Move { x, y } => println!("moving to ({x}, {y})"),
        Message::Write(text) => println!("writing: {text}"),
        Message::ChangeColor(r, g, b) => println!("color: ({r}, {g}, {b})"),
    }

Patterns can be:
- **Literal patterns**: match x { 1 => ..., 2 => ... }
- **Variable patterns**: match x { n => ... } (binds x to n)
- **Wildcard**: _ => ... (catch-all)
- **Reference patterns**: &val => ... (dereferences and binds)
- **Struct patterns**: Message::Move { x, y } => ... (destructuring)
- **Tuple patterns**: (a, b) => ... (destructuring tuples)
- **Slice patterns**: [first, second, rest...] => ... (Rust 1.26+)
- **Range patterns**: 1..=10 => ... (Rust 1.26+)
- **Match guards**: match x { n if n > 0 => ... }

### if let and while let — Convenience Patterns

    if let Message::Write(text) = message {
        println!("writing: {text}");
    }

This is sugar for "match on this one variant, and do something if
it matches." Useful when you only care about one variant.

    while let Some(value) = iterator.next() {
        println!("{value}");
    }

 반복(iteration)에서 "다음 값이 있는 동안 계속" 패턴.

================================================================================
SECTION 5: TRAITS — SHARED BEHAVIOR (NOT INHERITANCE)
================================================================================

### What a Trait Is

A trait defines shared behavior — a set of methods that a type can
implement. It's like an interface in Java or Go, but more powerful
(because of associated types, generic methods, default implementations,
and trait bounds).

    trait Summary {
        fn summarize(&self) -> String;

        // Default implementation — types can override it
        fn highlight(&self) -> String {
            String::from("---")
        }
    }

    // Implementing a trait for a type
    struct Article {
        title: String,
        author: String,
        content: String,
    }

    impl Summary for Article {
        fn summarize(&self) -> String {
            format!("{} by {}", self.title, self.author)
        }
        // highlight uses the default implementation
    }

### Trait Bounds — Constraining Generics

When you write generic code, you often need to say "this type must
have certain behavior." That's what trait bounds do:

    fn print_summary<T: Summary>(item: T) {
        println!("{}", item.summarize());
    }

This says: "T must implement Summary." If you try to call print_summary
with a type that doesn't implement Summary, it doesn't compile.

You can have multiple trait bounds:

    fn process<T: Summary + Clone>(item: T) { ... }

Or use where clauses (cleaner for many bounds):

    fn process<T>(item: T)
    where
        T: Summary + Clone + std::fmt::Debug,
    {
        ...
    }

### The Standard Library Traits (Know These)

These are the traits you'll see everywhere. Memorize what they mean:

- **Debug**: fmt::Debug — can be formatted with {:?}. Almost all
  types should implement this (derive works).
- **Display**: fmt::Display — can be formatted with {}. User-facing
  output. More constrained than Debug.
- **Clone**: can be explicitly cloned (deep copy). Not the same as
  Copy (which is implicit bitwise copy).
- **Copy**: can be copied by assignment (bitwise, implicitly).
  Only for types where a bitwise copy is safe and correct.
- **PartialEq**: partial equality (==). For types where equality
  is defined but not all values are comparable (e.g., floats
  have NaN which is not equal to anything).
- **Eq**: total equality (==). For types where equality is reflexive,
  symmetric, transitive — no NaN-like values.
- **PartialOrd**: partial ordering (<, >, <=, >=). For types where
  comparison is defined but not all pairs are comparable.
- **Ord**: total ordering. For types where all pairs are comparable.
- **Hash**: can be hashed (for HashMap keys). Must be consistent with
  Eq (if a == b, then hash(a) == hash(b)).
- **Default**: has a default value (Default::default()).
- **AsRef<T>**: can be converted to a reference to T. Used for
  generic acceptance of different types (e.g., AsRef<Path> for
  file paths — accepts String, &str, Path, PathBuf).
- **Into<T> / From<U>**: conversion traits. Into is the reciprocal
  of From. Implementing From is preferred (Into is automatically
  implemented for types that implement From).
- **Iterator**: the iterator trait — defines the iteration protocol.
  More on this in the Collections section.

### Derive — Automatic Trait Implementation

For common traits, Rust can automatically implement them for your
types using derive:

    #[derive(Debug, Clone, PartialEq, Eq, Hash)]
    struct Point {
        x: i32,
        y: i32,
    }

Derive generates the implementation automatically. Not all traits
can be derived (only those where the implementation is straightforward
and follows a standard pattern).

### The Orphan Rule — The Key Constraint

The Orphan Rule: you can only implement a trait for a type if EITHER
the trait OR the type is defined in your crate.

This means:
- You CAN implement your own trait for your own type (both in your crate).
- You CAN implement a foreign trait for your own type (trait from another
  crate, type from your crate).
- You CAN implement your own trait for a foreign type (trait from your
  crate, type from another crate).
- You CANNOT implement a foreign trait for a foreign type (both from
  other crates).

This rule prevents two crates from implementing the same trait for the
same type in conflicting ways (which would cause ambiguity).

Workaround: the **newtype pattern**. Wrap the foreign type in a new
struct and implement the trait for the wrapper:

    // Can't do this (Orphan Rule):
    // impl serde::Serialize for some_crate::MyType { ... }

    // Do this instead:
    struct MyTypeWrapper(some_crate::MyType);
    impl serde::Serialize for MyTypeWrapper { ... }

================================================================================
SECTION 6: GENERIC FUNCTIONS AND STRUCTS
================================================================================

### Generic Functions

    fn largest<T>(list: &[T]) -> &T
    where
        T: std::cmp::PartialOrd,
    {
        let mut largest = &list[0];
        for item in list {
            if item > largest {
                largest = item;
            }
        }
        largest
    }

This function works for any type T that can be partially ordered.
The compiler monomorphizes this: for each concrete type you call it
with, it generates a specialized version.

### Generic Structs

    struct Pair<T> {
        first: T,
        second: T,
    }

    impl<T> Pair<T> {
        fn new(first: T, second: T) -> Self {
            Self { first, second }
        }
    }

    impl<T: std::fmt::Display> Pair<T> {
        fn display(&self) {
            println!("({}, {})", self.first, self.second);
        }
    }

Note: you can have multiple impl blocks for the same generic type,
with different trait bounds. The second impl only applies when T
implements Display.

### Monomorphization — Zero-Cost Abstraction

When you call a generic function with a concrete type, the compiler
generates a specialized version of that function for that type. This
is monomorphization. The result: generic code has NO runtime overhead
compared to hand-written specialized code. The compiler generates the
same code it would if you wrote it by hand.

This is why Rust's generics are zero-cost: you get abstraction
without runtime cost.

The trade-off: code bloat. If you use a generic function with many
different types, the compiler generates a version for each, which can
increase binary size. This is usually fine (the specialized code is
often small), but worth knowing.

================================================================================
SECTION 7: TRAIT OBJECTS — DYNAMIC DISPATCH
================================================================================

Sometimes you need runtime polymorphism — where the concrete type
isn't known at compile time. That's what trait objects do.

    fn print_summary(item: &dyn Summary) {
        println!("{}", item.summarize());
    }

`dyn Summary` is a trait object — a type that implements Summary,
but the concrete type is erased at runtime. The compiler generates a
vtable (virtual method table) for the trait and calls methods through
it (dynamic dispatch).

Dynamic dispatch has a runtime cost (vtable lookup) compared to
static dispatch (monomorphization). Use trait objects when you need
heterogeneous collections (a Vec of different types that all implement
the same trait) or when you need runtime polymorphism.

Static dispatch (generics) is preferred when you can use it —
it's faster and the compiler can optimize better.

### Object Safe Traits

Not all traits can be used as trait objects. A trait must be "object
safe" to be used as `dyn Trait`. The rules:

- The trait must not have generic methods.
- The trait must not have Self in method signatures (except as the
  receiver, &self or &mut self).
- The trait must not require Self: Sized (or other sizing constraints).

Why? Because a trait object erases the concrete type. If a method
takes Self or returns Self, the compiler doesn't know what concrete
type to use at runtime. Object safety ensures that trait objects can
work without knowing the concrete type.

================================================================================
SECTION 8: ASSOCIATED TYPES VS GENERIC TYPE PARAMETERS
================================================================================

Traits can have two kinds of type parameters:

1. **Generic type parameters** (like functions):
   trait Container<T> {
       fn get(&self) -> T;
   }
   // Implementing: impl Container<i32> for MyType { ... }

2. **Associated types** (a type that's part of the trait):
   trait Container {
       type Item;
       fn get(&self) -> Self::Item;
   }
   // Implementing: impl Container for MyType {
       type Item = i32;
       fn get(&self) -> i32 { ... }
   }

Associated types are used when a trait has ONE natural type parameter
that's determined by the implementing type. Iterator is the classic
example:

    trait Iterator {
        type Item;
        fn next(&mut self) -> Option<Self::Item>;
        // ... other methods with default implementations ...
    }

Each iterator type has ONE Item type (the type it produces). Using
an associated type makes it clear that there's only one Item per
iterator implementation. If Iterator used a generic parameter, each
iterator could implement Iterator multiple times with different Item
types, which doesn't make sense.

================================================================================
SECTION 9: COMMON TRAIT PATTERNS
================================================================================

### The Newtype Pattern (for Orphan Rule)

As described in Section 5 — wrap a foreign type in a new struct to
implement foreign traits for it.

### Extension Traits — Adding Methods to Existing Types

You can define a trait with methods you want to add, and implement it
for a type. This is the extension trait pattern:

    trait StringUtils {
        fn is_palindrome(&self) -> bool;
    }

    impl StringUtils for str {
        fn is_palindrome(&self) -> bool {
            let bytes = self.as_bytes();
            bytes.iter().zip(bytes.iter().rev()).all(|(a, b)| a == b)
        }
    }

    // Now you can call "racecar".is_palindrome()

This is how the Rust standard library adds methods to types — many
methods on String, Vec, etc. are actually from traits implemented
in the standard library.

### Marker Traits — No Methods, Just semantics

Some traits have no methods — they just mark a type as having a
certain property:

- **Send**: the type can be transferred across threads safely.
- **Sync**: the type can be referenced from multiple threads safely
  (&T is Send). Auto-derived for types where all fields are Sync.
- **Sized**: the type has a known size at compile time. Most types
  are Sized. Dynamically sized types (DSTs) like [T] and str are
  !Sized (not Sized).
- **Unpin**: the type is safe to move after being pinned. Most types
  are Unpin. Pin is used for self-referential structs.

Send and Sync are the concurrency markers. They're auto-derived for
most types, but you can manually implement or suppress them.

### Default Implementation Pattern

Traits can have default method implementations. Types can override
them. This is the "template method" pattern in Rust:

    trait Logger {
        fn log(&self, message: &str) {
            // Default: just print
            println!("[LOG] {message}");
        }
    }

    struct FileLogger;
    impl Logger for FileLogger {
        fn log(&self, message: &str) {
            // Custom: write to file
            // ...
        }
    }

================================================================================
SECTION 10: EVIDENCE CHECKLIST — TYPES AND TRAITS (L2)
================================================================================

Can you:

- [ ] Explain the difference between String and &str and when to use each
- [ ] Explain what Rust enums are (algebraic data types, not C enums)
- [ ] Explain Option<T> and why it exists (no nulls in Rust)
- [ ] Explain Result<T, E> and why it exists (no exceptions in Rust)
- [ ] Use pattern matching exhaustively (match, if let, while let)
- [ ] Define a trait and implement it for a type
- [ ] Use trait bounds on generic functions
- [ ] Explain the Orphan Rule and the newtype workaround
- [ ] Explain what monomorphization is and why it gives zero-cost generics
- [ ] Explain the difference between static dispatch (generics) and
      dynamic dispatch (trait objects)
- [ ] Explain object safety — what makes a trait usable as a trait object
- [ ] Explain associated types vs generic type parameters (when to use each)
- [ ] Name and explain the key standard library traits:
      Debug, Display, Clone, Copy, PartialEq, Eq, PartialOrd, Ord,
      Hash, Default, AsRef, Into/From, Iterator, Send, Sync
- [ ] Use derive for common traits
- [ ] Explain the newtype pattern and extension traits
- [ ] Explain marker traits (Send, Sync, Sized, Unpin)

================================================================================
SECTION 11: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand types, enums, pattern matching, and traits, the
next topics in the Rust L1→L2 progression are:

1. **Error Handling** — Result<T, E>, Option<T> in practice, the ?
   operator, error design with thiserror, when to use expect vs unwrap.

2. **Collections and Iterators** — Vec, HashMap, HashSet, BTreeMap,
   iterator trait, iterator adapters (map, filter, collect, etc.),
   laziness, IntoIterator vs Iterator.

3. **Modules and Cargo** — the module system (mod, pub, use, crate
   root), crate organization (lib.rs, main.rs), Cargo dependencies,
   features, workspaces, semantic versioning.

4. **Smart Pointers and Interior Mutability** — Box<T>, Rc<T>, Arc<T>,
   RefCell<T>, Mutex<T>, when to use each.

5. **Basic Concurrency** — std::thread, Mutex, RwLock, Arc, mpsc
   channels, Send and Sync in practice.

Each builds on ownership and traits. You can't understand smart
pointers without understanding ownership and the Drop trait. You
can't understand iterators without understanding traits and borrowing.

================================================================================
END OF TYPES AND TRAITS DEEP STUDY
================================================================================
