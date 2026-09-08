# ===========================================================================
# RUST DEEP STUDY — ERROR HANDLING, COLLECTIONS & ITERATORS
# ===========================================================================
# Date: 2026-08-19
# Status: Deep study in progress
# Prerequisites: rust_ownership_deep_study.md, rust_types_traits_deep_study.md

## WHY THIS STUDY MATTERS

Error handling in Rust is entirely based on the type system: Result
and Option are enums, and the compiler forces you to handle them.
This is different from exception-based error handling (Java, Python)
or error-code-based handling (C). Understanding Rust's approach means
understanding how the type system drives error handling.

Collections and iterators are the bread and butter of Rust programming.
Rust's iterators are zero-cost abstractions (they're compiled away),
and they're the primary way you process sequences of data. Understanding
iterators deeply means writing idiomatic Rust that's both expressive
and fast.

================================================================================
SECTION 1: THE ERROR HANDLING PHILOSOPHY
================================================================================

Rust doesn't have exceptions. There's no try/catch, no throwing,
no exception hierarchy. Instead, Rust uses two enums to represent
the possibility of failure:

- **Option<T>**: a value that might not exist.
- **Result<T, E>**: an operation that might fail, returning either
  a success value or an error.

This is the Rust philosophy: errors are values, and the type system
makes you handle them. There's no hiding from errors — if a function
can fail, it returns Result, and the compiler forces you to deal with
it.

This is different from exception-based systems where you can ignore
the possibility of an exception. In Rust, you MUST handle the error
(or explicitly propagate it with ?).

================================================================================
SECTION 2: OPTION<T> — A VALUE THAT MIGHT NOT EXIST
================================================================================

    enum Option<T> {
        Some(T),
        None,
    }

Option<T> is Rust's replacement for null. Instead of allowing any
reference to be null (which leads to null pointer dereferences),
Rust says: "if a value might not exist, the type must be Option<T>."

This means the compiler can CHECK that you handle the "not found"
case. If you try to use an Option<T> as if it's always Some, the
compiler will reject your code (unless you explicitly unwrap, which
is a conscious choice).

### Common Patterns with Option

**Match on Option**:

    fn find_user(id: u32) -> Option<User> { ... }

    match find_user(42) {
        Some(user) => println!("found: {}", user.name),
        None => println!("not found"),
    }

**unwrap_or and unwrap_or_else**:

    // Provide a default value if None
    let name = find_user(42).map(|u| u.name).unwrap_or("unknown".to_string());

    // Or compute a default lazily (only if needed)
    let config = load_config().unwrap_or_else(|| default_config());

**map and and_then**:

    // Transform the inner value if Some
    let email: Option<String> = find_user(42).map(|u| u.email);

    // Chain operations that also return Option
    let address: Option<Address> = find_user(42)
        .and_then(|u| u.profile)
        .and_then(|p| p.address);

**ok_or and ok_or_else** (convert Option to Result):

    // Convert Option to Result with a custom error
    fn get_user(id: u32) -> Result<User, Error> {
        find_user(id).ok_or(Error::NotFound(id))
    }

**if let and while let** (convenience for single-variant handling):

    if let Some(user) = find_user(42) {
        println!("found: {}", user.name);
    }

    while let Some(line) = reader.next() {
        process(line);
    }

### When to Use Option

Use Option<T> when a value might not exist. Common cases:
- Looking up something in a collection that might not be there.
- A field that's optional (e.g., a user might not have a phone number).
- A function that might not find what it's looking for.

DON'T use Option for errors. Use Result for errors. Option is for
"this value might not exist" — Result is for "this operation might
fail."

================================================================================
SECTION 3: RESULT<T, E> — AN OPERATION THAT MIGHT FAIL
================================================================================

    enum Result<T, E> {
        Ok(T),
        Err(E),
    }

Result<T, E> represents an operation that either succeeds (Ok with
a value) or fails (Err with an error). This is Rust's primary error
handling mechanism.

### The Error Trait

The E in Result<T, E> must implement the error trait:

    trait Error: Debug + Display {
        fn source(&self) -> Option<&dyn Error> { ... }
        fn description(&self) -> &str { ... }  // deprecated
        fn cause(&self) -> Option<&dyn Error> { ... }  // deprecated
    }

The Error trait requires Debug and Display (so errors can be printed
for logging and debugging). The source method returns the underlying
error (for error chaining).

In practice, most error types don't implement Error manually — they
use the thiserror crate (or derive Error) to generate the implementation
automatically.

### Handling Result

**Match on Result**:

    match read_file("config.txt") {
        Ok(content) => println!("content: {content}"),
        Err(e) => eprintln!("error reading file: {e}"),
    }

**unwrap and expect** (ONLY for prototyping, tests, or truly
unrecoverable situations):

    // unwrap: panics if Err — DON'T use in production code
    let content = read_file("config.txt").unwrap();

    // expect: same as unwrap but with a custom panic message
    let content = read_file("config.txt").expect("config file must exist");

These are acceptable in:
- Tests (where a failure means the test fails anyway)
- Prototypes (where you'll replace with proper error handling later)
- Cases where the error truly means the program cannot continue
  (e.g., failing to initialize a required resource at startup)

In production code, you should handle errors properly, not unwrap.

**The ? Operator — Error Propagation**:

    fn read_config() -> Result<Config, Error> {
        let content = read_file("config.txt")?;  // propagates error if Err
        let config = parse_config(&content)?;    // propagates error if Err
        Ok(config)
    }

The ? operator is sugar for "if this is Err, return the error
immediately. If it's Ok, unwrap the value." It's the primary way
you propagate errors in Rust.

    // The above is equivalent to:
    fn read_config() -> Result<Config, Error> {
        let content = match read_file("config.txt") {
            Ok(c) => c,
            Err(e) => return Err(e),
        };
        let config = match parse_config(&content) {
            Ok(c) => c,
            Err(e) => return Err(e),
        };
        Ok(config)
    }

**Error Conversion with ?**:

The ? operator also does error conversion. If the error type of the
called function doesn't match the error type of the calling function,
Rust will try to convert it using the From trait:

    fn read_config() -> Result<Config, MyError> {
        let content = read_file("config.txt")?;  // read_file returns io::Error
                                                // MyError implements From<io::Error>
                                                // so the error is converted automatically
        ...
    }

This is why you see `impl From<io::Error> for MyError` in many Rust
projects. The ? operator uses it to convert errors.

### The ? Operator and Option

The ? operator works on Option too:

    fn find_user_and_email(id: u32) -> Option<String> {
        let user = find_user(id)?;     // propagates None if find_user returns None
        let email = user.email?;       // propagates None if email is None
        Some(email)
    }

This is useful for chaining operations that all might return None.

### When to Propagate vs When to Handle

- **Propagate** (?): when the error can't be handled at this level
  and should be passed to the caller.
- **Handle**: when you can do something useful at this level (retry,
  use a default, log and continue, convert to a different error).

A good rule: handle errors at the level where you have enough context
to do something useful. If you don't have enough context, propagate
with ? and add context at a higher level.

### Designing Error Types

Good error types in Rust:

1. **Are specific**: they tell the caller what went wrong.
2. **Carry useful context**: enough information for the caller to
   handle the error or report it usefully.
3. **Implement Display and Debug**: so they can be logged and printed.
4. **Use thiserror or derive**: don't implement Error manually unless
   you have a good reason.

Example with thiserror:

    #[derive(Debug, thiserror::Error)]
    enum ConfigError {
        #[error("config file not found: {0}")]
        NotFound(String),
        #[error("invalid config: {0}")]
        ParseError(String),
        #[error("missing required field: {0}")]
        MissingField(String),
    }

This generates: Display, Debug, Error implementations, and the error
messages are defined in the attribute. Clean and concise.

================================================================================
SECTION 4: THE STANDARD COLLECTIONS
================================================================================

### Vec<T> — The Dynamic Array

    let mut v: Vec<i32> = Vec::new();
    v.push(1);
    v.push(2);
    v.push(3);

    // Or with macro:
    let v = vec![1, 2, 3];

    // Access:
    let first = &v[0];     // indexing — panics if out of bounds
    let first = v.get(0);  // get — returns Option<&T>, None if out of bounds

    // Iterate:
    for item in &v {
        println!("{item}");
    }

    // Vec is growable, heap-allocated, and owns its elements.
    // Vec<T> implements Drop (frees heap memory when dropped).

Vec is the most commonly used collection in Rust. It's a dynamic
array that grows as needed. Key things to know:
- Vec owns its elements (they're moved into the Vec).
- Vec is heap-allocated (the array data is on the heap).
- Vec is growable (push, insert, resize).
- Vec can be indexed (with [] or .get()).
- Vec can be iterated (for item in &v, for item in v.iter(), etc.).

### HashMap<K, V> — The Hash Table

    use std::collections::HashMap;

    let mut map: HashMap<String, i32> = HashMap::new();
    map.insert("apple".to_string(), 5);
    map.insert("banana".to_string(), 3);

    // Access:
    let count = map.get("apple");  // returns Option<&V>
    let count = map["apple"];      // indexing — panics if key not found

    // Check if key exists:
    if map.contains_key("apple") {
        // ...
    }

    // Iterate:
    for (key, value) in &map {
        println!("{key}: {value}");
    }

HashMap is the hash table. Key things:
- HashMap is not ordered (iteration order is arbitrary).
- HashMap requires the key to implement Hash and Eq.
- HashMap ownership: keys and values are owned by the HashMap.
- HashMap get returns Option<&V> (None if key not found).

### BTreeMap<K, V> — The Ordered Map

    use std::collections::BTreeMap;

    let mut map: BTreeMap<String, i32> = BTreeMap::new();
    map.insert("apple".to_string(), 5);
    map.insert("banana".to_string(), 3);

    // BTreeMap is ordered by key (sorted iteration)
    for (key, value) in &map {
        println!("{key}: {value}");  // keys in sorted order
    }

Use BTreeMap when you need ordered iteration or range queries (keys
in a range). BTreeMap is a balanced binary tree (B-tree), so it's
slightly slower than HashMap for insertions and lookups, but it
maintains order.

### HashSet<T> and BTreeSet<T>

Sets are collections of unique elements. HashSet is the hash-based
version, BTreeSet is the ordered version.

    use std::collections::HashSet;

    let mut set: HashSet<i32> = HashSet::new();
    set.insert(1);
    set.insert(2);
    set.insert(2);  // duplicate — ignored

    // Set operations:
    set.contains(&1);      // true
    set.remove(&2);        // removes 2
    set.len();             // 1

### When to Use Each

- **Vec**: ordered sequence, fast indexing, fast iteration. The default
  choice for most sequences.
- **HashMap**: key-value lookup, fast insertion and lookup (O(1) average).
- **BTreeMap**: key-value lookup with ordered keys, range queries.
- **HashSet/BTreeSet**: unique elements, set operations (union, intersection,
  difference).

================================================================================
SECTION 5: ITERATORS — THE PRIMARY DATA PROCESSING TOOL
================================================================================

### The Iterator Trait

    trait Iterator {
        type Item;

        fn next(&mut self) -> Option<Self::Item>;

        // Default implementations for other methods...
        fn map<B, F>(self, f: F) -> Map<Self, F>
        where
            F: FnMut(Self::Item) -> B,
        { ... }

        fn filter<P>(self, predicate: P) -> Filter<Self, P>
        where
            P: FnMut(&Self::Item) -> bool,
        { ... }

        fn collect<B>(self) -> B
        where
            B: FromIterator<Self::Item>,
        { ... }

        // ... many more methods
    }

An iterator is anything that implements the Iterator trait. The only
required method is next(), which returns the next item (or None when
done). All other methods (map, filter, collect, etc.) are provided
with default implementations.

### Creating Iterators

**From a Vec or slice**:

    let v = vec![1, 2, 3];

    v.iter()       // iterator over &T (borrows elements)
    v.iter_mut()   // iterator over &mut T (mutable borrows)
    v.into_iter()  // iterator over T (consumes the Vec, moves elements out)

**From a range**:

    0..10          // range iterator: 0, 1, 2, ..., 9
    (0..10).iter() // same, explicit

**From a collection**:

    let map = HashMap::new();
    map.iter()       // iterator over (&K, &V)

**From an infinite source**:

    std::iter::repeat(1)      // infinite iterator of 1
    std::iter::once(1)        // iterator that yields 1 once, then None
    std::iter::from_fn(|| ...) // create an iterator from a closure

### Iterator Adapters — Transforming Iterators

Iterator adapters are methods that transform an iterator into a new
iterator. They're LAZY — they don't do anything until the iterator
is consumed (by next(), collect(), for loop, etc.).

**map**: transform each element

    (1..5).iter().map(|x| x * 2).collect::<Vec<_>>()  // [2, 4, 6, 8]

**filter**: keep only elements matching a predicate

    (1..10).iter().filter(|x| x % 2 == 0).collect::<Vec<_>>()  // [2, 4, 6, 8]

**filter_map**: combine filter and map

    let strings = vec!["1", "hello", "3", "world"];
    strings.iter().filter_map(|s| s.parse::<i32>().ok()).collect::<Vec<_>>()
    // [1, 3]

**enumerate**: add indices

    let words = vec!["hello", "world"];
    for (i, word) in words.iter().enumerate() {
        println!("{i}: {word}");
    }

**zip**: combine two iterators

    let a = vec![1, 2, 3];
    let b = vec!["a", "b", "c"];
    a.iter().zip(b.iter()).collect::<Vec<_>>()
    // [(1, "a"), (2, "b"), (3, "c")]

**chain**: concatenate two iterators

    let a = vec![1, 2];
    let b = vec![3, 4];
    a.iter().chain(b.iter()).collect::<Vec<_>>()  // [1, 2, 3, 4]

**take and skip**: limit or skip elements

    (0..10).iter().take(3).collect::<Vec<_>>()   // [0, 1, 2]
    (0..10).iter().skip(3).collect::<Vec<_>>()  // [3, 4, 5, 6, 7, 8, 9]

**flat_map**: map to iterators and flatten

    let sentences = vec!["hello world", "foo bar"];
    sentences.iter()
        .flat_map(|s| s.split_whitespace())
        .collect::<Vec<_>>()
    // ["hello", "world", "foo", "bar"]

**scan**: stateful mapping (like fold, but produces an iterator)

    (1..10).iter().scan(0, |state, x| {
        *state += x;
        Some(*state)  // running sum
    }).collect::<Vec<_>>()  // [1, 3, 6, 10, 15, 21, 28, 36, 45]

**fuse**: stop after None (useful for custom iterators that might
continue returning Some after they're exhausted)

**peekable**: add the ability to peek at the next element without
consuming it

### Consuming Iterators — Turning Them Into Values

**collect**: turn the iterator into a collection

    (1..5).map(|x| x * 2).collect::<Vec<_>>()       // Vec<i32>
    (1..5).map(|x| x * 2).collect::<HashSet<_>>()   // HashSet<i32>
    (1..5).map(|x| x * 2).collect::<String>()       // String (if Item is char)

**sum and product**: sum or product of elements

    (1..6).sum::<i32>()   // 15
    (1..6).product::<i32>()  // 120

**min, max, min_by, max_by**: find min/max element

    let nums = vec![3, 1, 4, 1, 5];
    let min = nums.iter().min();  // Some(&1)
    let max = nums.iter().max();  // Some(&5)

**try_fold and try_for_each**: fold with early exit on error (like
a loop with break on error)

**for loop**: the most common way to consume an iterator

    for item in v.iter() {
        println!("{item}");
    }

The for loop is actually syntax sugar for calling into_iter() on the
expression and then calling next() repeatedly.

### Lazy Evaluation — The Key Insight

Iterator adapters are LAZY. They don't do any work until the iterator
is consumed.

    let v: Vec<i32> = (1..1000)
        .map(|x| {
            println!("mapping {x}");
            x * 2
        })
        .filter(|x| x % 3 == 0)
        .take(3)
        .collect();

    // This prints "mapping 1", "mapping 2", "mapping 3" and stops.
    // It NEVER maps 4 through 999, because take(3) stops the iteration
    // after 3 elements are collected.

This is why iterators are zero-cost: they're compiled into tight loops
that only do the work that's needed. There's no intermediate allocation
(unless you use .collect()).

### IntoIterator — The Trait That Makes For Loops Work

    trait IntoIterator {
        type Item;
        type IntoIter: Iterator<Item = Self::Item>;

        fn into_iter(self) -> Self::IntoIter;
    }

IntoIterator is implemented for:
- Vec<T>: into_iter() consumes the Vec and yields T
- &Vec<T>: into_iter() yields &T
- &mut Vec<T>: into_iter() yields &mut T
- Arrays: [T; N]: into_iter() yields T (moves elements out)
- &Arrays: into_iter() yields &T
- HashMap, HashSet, BTreeMap, BTreeSet: similar patterns

This is why `for item in v` and `for item in &v` behave differently:
v.into_iter() vs (&v).into_iter().

### Iterator Invalidation — A Common Pitfall

DON'T modify a collection while iterating over it (unless you're using
mutable iteration and know what you're doing).

    // WRONG: modifying a Vec while iterating over it
    let mut v = vec![1, 2, 3, 4, 5];
    for item in v.iter() {
        if *item % 2 == 0 {
            v.push(*item * 10);  // ERROR: cannot push while iterating
        }
    }

The reason: the iterator borrows the Vec immutably (for v.iter()),
and push() requires a mutable borrow. Rust won't let you have both.

If you need to filter or transform a collection, use a new collection
or use iterator methods that don't require holding a borrow:

    // RIGHT: collect into a new Vec
    let v = vec![1, 2, 3, 4, 5];
    let filtered: Vec<_> = v.iter().filter(|x| **x % 2 == 0).collect();

    // Or: use retain (in-place filtering)
    let mut v = vec![1, 2, 3, 4, 5];
    v.retain(|x| x % 2 == 0);  // keeps only even elements

================================================================================
SECTION 6: EVIDENCE CHECKLIST — ERROR HANDLING, COLLECTIONS, ITERATORS (L2)
================================================================================

Can you:

- [ ] Explain why Rust uses Option and Result instead of null and exceptions
- [ ] Use Option fluently: match, if let, map, and_then, unwrap_or,
      ok_or
- [ ] Use Result fluently: match, ? operator, error propagation
- [ ] Explain the ? operator and how it works (propagation and conversion)
- [ ] Explain when unwrap/expect is acceptable vs when it's not
- [ ] Design error types with thiserror (or explain why manual Error
      impl is rare)
- [ ] Use Vec fluently: creation, push, indexing, iteration, common patterns
- [ ] Use HashMap and BTreeMap: when to use each, get vs indexing
- [ ] Use HashSet and BTreeSet: set operations, unique collections
- [ ] Create iterators from slices, Vec, ranges, collections
- [ ] Use iterator adapters: map, filter, filter_map, enumerate, zip,
      chain, take, skip, flat_map, scan
- [ ] Consume iterators: collect, sum, product, min, max, for loop
- [ ] Explain lazy evaluation in iterators (why they're zero-cost)
- [ ] Explain IntoIterator and why for loops work on different types
- [ ] Explain iterator invalidation and how to avoid it (retain, collecting)
- [ ] Read and understand iterator chains (parse a complex iterator pipeline)

================================================================================
SECTION 7: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand error handling, collections, and iterators, the
next topics in the Rust L1→L2 progression are:

1. **Modules and Cargo** — the module system (mod, pub, use, crate
   root), crate organization, Cargo dependencies and workspaces.

2. **Smart Pointers and Interior Mutability** — Box<T>, Rc<T>, Arc<T>,
   RefCell<T>, Mutex<T>, when to use each.

3. **Basic Concurrency** — std::thread, Mutex, RwLock, Arc, mpsc
   channels, Send and Sync in practice.

4. **Basic Tooling** — cargo, rustfmt, clippy, rustup, reading rustc
   errors, debugging with rust-gdb or rust-lldb.

Each builds on what I've studied. You can't use modules effectively
without understanding visibility and paths. You can't use smart
pointers without understanding ownership and Drop. You can't use
concurrency without understanding Send and Sync.

================================================================================
END OF ERROR HANDLING, COLLECTIONS & ITERATORS DEEP STUDY
================================================================================
