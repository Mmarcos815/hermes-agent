# ===========================================================================
# GO DEEP STUDY — CONCURRENCY: GOROUTINES, CHANNELS & CONTEXT
# ===========================================================================
# Date: 2026-08-19
# Status: Deep study in progress
# Prerequisites: go_interfaces_errors_tooling_deep_study.md

## WHY THIS STUDY MATTERS

Concurrency is Go's defining feature. Go was designed for concurrent
programming from the start. Understanding goroutines, channels, and
context deeply means understanding what makes Go different from
other languages and how to write concurrent Go that's correct,
efficient, and idiomatic.

This targets L2 understanding: can explain the concepts, the GMP
model, channel semantics, context propagation, and common concurrency
patterns.

================================================================================
SECTION 1: GOROUTINES — LIGHTWEIGHT CONCURRENT EXECUTION
================================================================================

### What a Goroutine Is

A goroutine is a lightweight thread managed by the Go runtime. You
start one with the `go` keyword:

    go func() {
        fmt.Println("running concurrently")
    }()

This starts a new goroutine that runs the function concurrently with
the caller. The caller doesn't wait for it to finish — execution
continues immediately.

Goroutines are:
- **Lightweight**: they use very little memory (starting at ~2KB stack,
  grow as needed). You can run thousands or millions of goroutines
  on a single machine.
- **Fast to create and destroy**: the Go runtime is optimized for
  goroutine lifecycle.
- **Scheduled by the Go runtime**: the runtime decides which goroutine
  runs on which OS thread, when to switch, etc.

### The GMP Model — How Goroutines Are Scheduled

The Go runtime uses a scheduler with three components:

- **G (Goroutine)**: a goroutine. Each goroutine has its own stack,
  program counter, and state.
- **M (Machine)**: an OS thread. M represents a real thread that
  executes Go code.
- **P (Processor)**: a logical processor (a context for scheduling).
  Each P has a queue of Gs to run. The number of Ps is set by
  GOMAXPROCS (default: number of CPU cores). Ps are the key to
  Go's scalability — they limit how many goroutines run truly
  concurrently.

The scheduler works like this:

- Each P has a local queue of Gs (goroutines ready to run).
- When a P runs out of local Gs, it steals from other Ps' queues
  (work-stealing).
- When a G makes a blocking syscall, the M running it can hand off
  the P to another M (so other goroutines can keep running).
- When a G blocks on a channel operation or mutex, it yields the P
  so another G can run on that P.

This is the GMP model. The key insight: Go achieves high concurrency
by multiplexing many Gs onto fewer Ms onto available CPUs. A G doesn't
own an M permanently — it runs on an M when scheduled, then yields.

### Comparing Goroutines to OS Threads

| Aspect | Goroutine | OS Thread |
|--------|-----------|-----------|
| Memory | ~2KB stack (grows as needed) | ~1-2MB stack (fixed) |
| Creation cost | Very low (runtime-managed) | High (syscall) |
| Scheduling | Go runtime scheduler (user-space) | OS scheduler (kernel-space) |
| Switching cost | Low (user-space context switch) | Higher (kernel context switch) |
| Concurrency model | M:N (many goroutines on few threads) | 1:1 (one thread per task) |

This is why you can run 100,000 goroutines but only a few thousand
OS threads. Goroutines are cheap.

### Starting and Waiting for Goroutines

    // Start a goroutine
    go doSomething()

    // Wait for goroutines to finish — use a WaitGroup
    var wg sync.WaitGroup
    wg.Add(2)

    go func() {
        defer wg.Done()
        doSomething()
    }()

    go func() {
        defer wg.Done()
        doSomethingElse()
    }()

    wg.Wait()  // blocks until both goroutines call Done()

sync.WaitGroup is the standard way to wait for a group of goroutines
to finish. Add increments the counter, Done decrements it, Wait
blocks until the counter reaches zero.

### Goroutine Lif lifecycle

A goroutine's lifecycle:
1. Created when `go` statement executes.
2. Scheduled onto an M via a P.
3. Runs until it: returns, panics, blocks (channel, mutex, syscall),
   or is stopped by the runtime (e.g., program exit).
4. Resources are cleaned up (stack freed, etc.).

A goroutine that never returns and never blocks is a **goroutine
leak**. It consumes memory forever. This is one of the main bugs
in concurrent Go — goroutines that are started but never finish
because they're waiting on something that never happens.

================================================================================
SECTION 2: CHANNELS — COMMUNICATION BETWEEN GOROUTINES
================================================================================

### What a Channel Is

A channel is a typed conduit for sending and receiving values between
goroutines. It's Go's primary mechanism for communication and
synchronization.

    // Create an unbuffered channel of int
    ch := make(chan int)

    // Send: ch <- value
    ch <- 42

    // Receive: value := <-ch
    value := <-ch

    // Close: close(ch)
    close(ch)

Channels are typed: a channel of int (chan int) can only send and
receive int values. Trying to send the wrong type is a compile error.

### Unbuffered vs Buffered Channels

**Unbuffered channel**: `make(chan T)`
- Has no capacity. Sending blocks until a receiver is ready.
- Sending and receiving are SYNCHRONOUS — the sender and receiver
  meet at the channel.
- This is the default and most common kind.

    ch := make(chan int)
    go func() {
        ch <- 42    // blocks until someone receives
    }()
    value := <-ch  // receives 42 — unblocks the sender

**Buffered channel**: `make(chan T, capacity)`
- Has a buffer of the given capacity. Sending blocks only when the
  buffer is full. Receiving blocks only when the buffer is empty.
- Sending and receiving are ASYNCHRONOUS (up to buffer capacity).

    ch := make(chan int, 3)
    ch <- 1    // OK — buffer has room
    ch <- 2    // OK — buffer has room
    ch <- 3    // OK — buffer is now full
    // ch <- 4  // would block — buffer full
    value := <-ch  // receives 1 — buffer now has room

Buffered channels are useful for:
- Decoupling sender and receiver (when they operate at different rates).
- Producer-consumer patterns (producer fills buffer, consumer drains it).
- Limiting concurrency (buffered channel as a semaphore).

But they should be used intentionally — a buffer that's too large can
hide synchronization issues and make the program harder to reason about.

### Sending and Receiving Semantics

- **Send**: `ch <- value`
  - If the channel is unbuffered or the buffer is full, the sender
    blocks until a receiver takes the value.
  - If the channel is closed, sending panics.

- **Receive**: `value := <-ch`
  - If the channel has a value available, receive returns it.
  - If the channel is empty and not closed, the receiver blocks until
    a value is sent.
  - If the channel is closed and empty, receive returns the zero value
    of the type immediately.

- **Receive with check**: `value, ok := <-ch`
  - ok is true if the value was received (channel not closed or still
    has values).
  - ok is false if the channel is closed and empty (value is the zero
    value).

### Closing Channels

Closing a channel indicates "no more values will be sent." It's done
with the `close` builtin: `close(ch)`.

Important rules:
- **Only the sender should close a channel.** A receiver closing a
  channel can cause a panic if the sender tries to send after close.
- **Don't close a channel twice.** Closing an already-closed channel
  panics.
- **Don't close a nil channel.** Closing a nil channel panics.

Receiving from a closed channel:
- If the channel still has values buffered, receive returns them.
- Once all buffered values are consumed, receive returns the zero
  value and ok=false.
- A range loop over a channel exits when the channel is closed and
  empty.

    for value := range ch {
        // processes values until ch is closed
    }
    // loop exits when ch is closed and empty

### Channel Patterns

**Producer-Consumer**:

    func producer(ch chan<- int) {
        for i := 0; i < 10; i++ {
            ch <- i
        }
        close(ch)
    }

    func consumer(ch <-chan int) {
        for value := range ch {
            fmt.Println(value)
        }
    }

    ch := make(chan int)
    go producer(ch)
    consumer(ch)

The producer sends values and closes the channel when done. The
consumer uses range to receive until closed. This is the canonical
Go concurrency pattern.

**Worker Pool**:

    func worker(id int, jobs <-chan Job, results chan<- Result) {
        for job := range jobs {
            results <- process(job)
        }
    }

    jobs := make(chan Job, 100)
    results := make(chan Result, 100)

    // Start workers
    for w := 0; w < 5; w++ {
        go worker(w, jobs, results)
    }

    // Send jobs
    for j := 0; j < 1000; j++ {
        jobs <- Job{...}
    }
    close(jobs)  // signal no more jobs

    // Collect results
    for r := 0; r < 1000; r++ {
        result := <-results
        // ...
    }

Multiple workers read from the same jobs channel and send to the
same results channel. The jobs channel is closed after all jobs are
sent, so workers exit when they've processed all jobs.

**Fan-Out / Fan-In**:

    // Fan-out: multiple goroutines read from one channel
    func fanOut(in <-chan int, n int) []<-chan int {
        outs := make([]chan int, n)
        for i := 0; i < n; i++ {
            outs[i] = make(chan int)
            go func(out chan<- int) {
                for v := range in {
                    out <- v
                }
            }(outs[i])
        }
        return outs
    }

    // Fan-in: one goroutine reads from multiple channels
    func fanIn(outs ...<-chan int) <-chan int {
        out := make(chan int)
        var wg sync.WaitGroup
        for _, c := range outs {
            wg.Add(1)
            go func(c <-chan int) {
                defer wg.Done()
                for v := range c {
                    out <- v
                }
            }(c)
        }
        go func() {
            wg.Wait()
            close(out)
        }()
        return out
    }

Fan-out distributes work across multiple goroutines. Fan-in collects
results from multiple goroutines into one channel. These are common
patterns in concurrent Go.

**Channel as a semaphore**:

    sem := make(chan struct{}, 10)  // semaphore with capacity 10

    for i := 0; i < 100; i++ {
        sem <- struct{}{}  // acquire — blocks if 10 already acquired
        go func(i int) {
            defer func() { <-sem }()  // release
            doWork(i)
        }(i)
    }

A buffered channel can act as a semaphore to limit concurrency.
Send to acquire, receive to release.

### Select — Multiplexing Channel Operations

`select` lets a goroutine wait on multiple channel operations:

    select {
    case msg1 := <-ch1:
        fmt.Println("received", msg1)
    case msg2 := <-ch2:
        fmt.Println("received", msg2)
    case ch3 <- "hello":
        fmt.Println("sent to ch3")
    case <-time.After(5 * time.Second):
        fmt.Println("timeout")
    }

Select blocks until one of its cases can proceed. If multiple cases
are ready, one is chosen at random (this avoids starvation and
ensures fairness).

select is the primary way to handle multiple channels in Go. It's
used for:
- Reading from multiple sources.
- Writing to multiple destinations.
- Implementing timeouts (with time.After or time.NewTimer).
- Implementing cancellation (with a done channel).

### Common Channel Pitfalls

1. **Sending to a closed channel panics**:
   Always ensure the sender doesn't send after close. Use a done
   channel or a flag if the sender might outlive the receiver.

2. **Goroutine leaks from blocked sends/receives**:
   If a goroutine is blocked on a channel operation that never
   completes, the goroutine leaks. Use select with a timeout or
   cancellation channel to avoid this.

3. **Closing a channel twice**:
   Use a sync.Once or ensure close is called exactly once, typically
   by the sender after all sends are done.

4. **Forgetting to close channels (with range)**:
   A range loop over a channel never exits unless the channel is
   closed. Forgetting to close the channel means the range loop
   blocks forever — a goroutine leak.

5. **Using a buffered channel as a queue without understanding
   synchronization**:
   Buffered channels are synchronized data structures with built-in
   blocking. Using them as a simple queue without understanding the
   blocking semantics can lead to deadlocks or unexpected blocking.

================================================================================
SECTION 3: CONTEXT — CANCELLATION, TIMEOUTS, AND REQUEST SCOPES
================================================================================

### What Context Is

The context package (context) provides a way to carry deadlines,
cancellation signals, and request-scoped values across API boundaries
and between goroutines.

    ctx := context.Background()              // empty context — root
    ctx, cancel := context.WithCancel(ctx)   // cancellable context
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)  // with timeout
    ctx, cancel := context.WithDeadline(ctx, time.Now().Add(10*time.Second))
    ctx = context.WithValue(ctx, key, value)  // with a value

Context is designed to be passed through the call chain. Functions
that do I/O, network calls, or long-running work should accept a
context as their first parameter.

    func DoWork(ctx context.Context) error {
        // Use ctx for cancellation, timeout, values
    }

### Why Context Exists

Context was introduced to solve the problem of cancellation and
request scope propagation in Go servers. Before context, there was
no standard way to:
- Cancel a long-running operation when a client disconnects.
- Propagate a timeout through multiple layers of function calls.
- Associate request-scoped data (like a request ID or user info)
  with a request.

The context package provides a standard mechanism for all of these.

### Cancellation

A context can be cancelled:

    ctx, cancel := context.WithCancel(context.Background())

    go func() {
        time.Sleep(2 * time.Second)
        cancel()  // signal cancellation
    }()

    select {
    case <-ctx.Done():
        fmt.Println("cancelled")
    case <-time.After(10 * time.Second):
        fmt.Println("completed")
    }

When cancel() is called, all goroutines using ctx.Done() receive the
signal. ctx.Done() returns a channel that's closed when the context
is cancelled.

### Timeout and Deadline

WithTimeout creates a context that's automatically cancelled after
a duration:

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()  // must call cancel to release resources

    select {
    case <-doWork(ctx):
        fmt.Println("work completed")
    case <-ctx.Done():
        fmt.Println("work cancelled or timed out")
    }

WithDeadline is similar but with an absolute time:

    ctx, cancel := context.WithDeadline(context.Background(),
        time.Now().Add(10*time.Second))

The key: you MUST call cancel() when you're done with a context
created by WithCancel, WithTimeout, or WithDeadline. This releases
the resources associated with the context (goroutines, channels,
timers). Failing to call cancel leaks resources.

Using defer cancel() is the standard pattern.

### Context Values — Request Scope

Context can carry arbitrary values:

    type contextKey string
    const requestIDKey contextKey = "requestID"

    ctx = context.WithValue(parentCtx, requestIDKey, "abc123")

    // Retrieve the value:
    if rid := ctx.Value(requestIDKey); rid != nil {
        fmt.Println("request ID:", rid)
    }

Context values should be used SPARINGLY — only for request-scoped
data that truly needs to be passed through multiple layers (like a
request ID for logging). They're NOT for passing optional parameters
or replacing function arguments.

The type of the key should be a custom type (not string) to avoid
collisions between different packages using the same key name.

### Context Propagation Rules

1. **Pass context as the first parameter** to functions that do I/O
   or long-running work.
2. **Don't store context in a struct.** Context has a scope — storing
   it in a struct can cause the context to live longer than intended.
3. **Don't pass a nil context.** Use context.Background() or
   context.TODO() if you don't have a context.
4. **Derived contexts inherit cancellation.** If a parent context is
   cancelled, all derived contexts are cancelled too. This is how
   cancellation propagates through the call chain.
5. **Use context.Background() as the root** for top-level contexts
   (main, tests). Use context.TODO() when you're not sure which
   context to use (it's a placeholder that should be replaced later).

### Context in Servers

In HTTP servers, each request gets a context that's cancelled when
the client disconnects or the request times out:

    func handler(w http.ResponseWriter, r *http.Request) {
        ctx := r.Context()  // request's context

        // Pass ctx to downstream functions
        result, err := doWork(ctx)
        if err != nil {
            if errors.Is(err, context.DeadlineExceeded) {
                http.Error(w, "timeout", http.StatusGatewayTimeout)
                return
            }
            http.Error(w, err.Error(), http.StatusInternalServerError)
            return
        }
        fmt.Fprintf(w, "%s", result)
    }

This is the standard pattern for Go servers: the request context
provides cancellation propagation automatically.

### Common Context Patterns

**Cancellation of multiple goroutines**:

    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    go doWork1(ctx)
    go doWork2(ctx)
    go doWork3(ctx)

    // When the main function returns (or cancel is called), all
    // goroutines receive the cancellation signal through ctx.Done()

**Timeout for an operation**:

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    result, err := doWork(ctx)
    if err == context.DeadlineExceeded {
        // handle timeout
    }

**Using context in database queries**:

    // database/sql supports context
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()

    row := db.QueryRowContext(ctx, "SELECT name FROM users WHERE id = ?", id)

Many Go libraries support context — database/sql, net/http (via
request context), gRPC, etc. Using context with these libraries gives
you cancellation and timeout propagation for free.

================================================================================
SECTION 4: SYNCHRONIZATION PRIMITIVES — BEYOND CHANNELS
================================================================================

### sync.Mutex and sync.RWMutex

Channels are for communication. Mutexes are for protecting shared
state.

    var (
        mu sync.Mutex
        count int
    )

    func increment() {
        mu.Lock()
        count++
        mu.Unlock()
    }

    func readCount() int {
        mu.Lock()
        defer mu.Unlock()
        return count
    }

Use a mutex when you have shared mutable state that needs protection.
Channels are for passing data between goroutines. Mutexes are for
protecting data that multiple goroutines access.

sync.RWMutex allows multiple readers or one writer:

    var (
        mu sync.RWMutex
        data map[string]string
    )

    func read(key string) string {
        mu.RLock()
        defer mu.RUnlock()
        return data[key]
    }

    func write(key, value string) {
        mu.Lock()
        defer mu.Unlock()
        data[key] = value
    }

Use RWMutex when reads are frequent and writes are infrequent.
Using a plain Mutex for read-heavy workloads is wasteful — every
read locks the mutex.

### sync.WaitGroup

As described in the goroutine section — used to wait for a group of
goroutines to finish.

    var wg sync.WaitGroup
    wg.Add(2)
    go func() { defer wg.Done(); work() }()
    go func() { defer wg.Done(); work() }()
    wg.Wait()

### sync.Once

sync.Once ensures a function is called exactly once, even if called
from multiple goroutines.

    var once sync.Once
    var config *Config

    func loadConfig() *Config {
        once.Do(func() {
            config = readConfigFile()
        })
        return config
    }

This is thread-safe — the first goroutine to call Do() executes the
function, all others wait and then return. Once is useful for lazy
initialization, singleton initialization, and one-time setup.

### sync.Cond

sync.Cond is a condition variable — used for signaling between
goroutines.

    var (
        mu sync.Mutex
        cond = sync.NewCond(&mu)
        ready bool
    )

    func waitForReady() {
        mu.Lock()
        for !ready {
            cond.Wait()  // releases mu, waits for signal, re-acquires mu
        }
        mu.Unlock()
    }

    func signalReady() {
        mu.Lock()
        ready = true
        cond.Signal()  // wake one waiter
        // or cond.Broadcast() — wake all waiters
        mu.Unlock()
    }

Condition variables are used less than channels in idiomatic Go, but
they're useful in specific patterns (like producer-consumer where
you want to signal that data is available without sending the data
through a channel).

### sync.Pool — Object Pooling for Performance

sync.Pool is a thread-safe object pool. It's used to reduce garbage
collection pressure by reusing objects.

    var pool = sync.Pool{
        New: func() interface{} {
            return &Buffer{}
        },
    }

    func process() {
        buf := pool.Get().(*Buffer)
        defer pool.Put(buf)
        // use buf
    }

Pool is useful for frequently allocated short-lived objects (like
buffers for I/O). It's NOT a general-purpose cache — the runtime can
clear the pool at any time (e.g., during GC). Don't rely on objects
being in the pool.

================================================================================
SECTION 5: GOROUTINE LEAKS — THE #1 CONCURRENCY BUG
================================================================================

### What a Goroutine Leak Is

A goroutine leak is a goroutine that never exits. It consumes memory
(its stack) and may hold references that prevent other resources
from being freed. Unlike memory leaks in GC'd languages, goroutine
leaks are NOT automatically cleaned up — they persist until the
program exits.

### Common Causes of Goroutine Leaks

1. **Blocking on a channel that never receives**:
   A goroutine blocked on `ch <- value` when no one is receiving,
   or on `value := <-ch` when no one is sending.

   // LEAKS: goroutine blocked on send forever
   go func() {
       ch <- doWork()  // no one receives — goroutine blocks forever
   }()

2. **Range over a channel that's never closed**:
   A goroutine doing `for v := range ch` that never exits because
   the channel is never closed.

   // LEAKS: range loop never exits
   go func() {
       for v := range ch {
           process(v)
       }
   }()

3. **Waiting on a condition that never becomes true**:
   A goroutine waiting on a mutex, condition variable, or timeout
   that never happens.

4. **Infinite loop**:
   A goroutine stuck in an infinite loop (not a leak per se, but
   a bug that prevents the goroutine from exiting).

### How to Prevent Goroutine Leaks

1. **Use context for cancellation**. Always pass a context to
   long-running goroutines and check ctx.Done() periodically.

   go func() {
       for {
           select {
           case <-ctx.Done():
               return  // exit on cancellation
           case job := <-jobs:
               process(job)
           }
       }
   }()

2. **Ensure channels are properly closed**. The sender should close
   the channel when done sending. The receiver can use range safely.

3. **Use buffered channels with care**. A buffered channel can
   still leak if the buffer fills up and no one drains it. Don't
   rely on buffer capacity to prevent blocking — ensure there's
   always a receiver.

4. **Use select with a timeout or default**. If a goroutine waits
   for a channel operation, use select with a timeout or a default
   case to avoid blocking forever.

   select {
   case value := <-ch:
       process(value)
   case <-time.After(5 * time.Second):
       return  // give up after 5 seconds
   }

5. **Test for goroutine leaks**. Use runtime.NumGoroutine() to check
   the number of goroutines before and after tests. If the number
   increases and doesn't decrease, you may have a leak.

   func TestNoLeak(t *testing.T) {
       initial := runtime.NumGoroutine()
       doSomethingThatStartsGoroutines()
       time.Sleep(100 * time.Millisecond)  // give goroutines time to finish
       final := runtime.NumGoroutine()
       if final > initial + 1 {  // allow 1 for the test goroutine
           t.Errorf("goroutine leak: expected %d, got %d", initial, final)
       }
   }

### Detecting Goroutine Leaks in Practice

- runtime.NumGoroutine() gives the current count.
- pprof goroutine profile shows all goroutines and their call stacks
  (useful for finding stuck goroutines).
- Go 1.14+ has runtime.Stack with all goroutine stacks.

================================================================================
SECTION 6: EVIDENCE CHECKLIST — GO CONCURRENCY (L2)
================================================================================

Can you:

- [ ] Explain what a goroutine is and how it differs from an OS thread
- [ ] Explain the GMP model (Goroutine, Machine, Processor) and how
      the Go scheduler works
- [ ] Start goroutines and wait for them (go keyword, WaitGroup,
      Done)
- [ ] Explain why goroutines are lightweight (small stack, runtime-
      managed scheduling)
- [ ] Create unbuffered and buffered channels and explain the difference
- [ ] Use channels for communication and synchronization (send, receive,
      close, range)
- [ ] Explain channel closing rules (only sender closes, don't close
      twice, don't close nil)
- [ ] Use select for multiplexing channel operations
- [ ] Implement producer-consumer, worker pool, fan-out/fan-in patterns
- [ ] Use channels as semaphores for limiting concurrency
- [ ] Create and use contexts: WithCancel, WithTimeout, WithDeadline,
      WithValue
- [ ] Explain why context must be propagated through the call chain
- [ ] Use ctx.Done() for cancellation checking
- [ ] Call cancel() to release context resources (and use defer)
- [ ] Use context in HTTP servers (r.Context())
- [ ] Use sync.Mutex, sync.RWMutex, sync.WaitGroup, sync.Once,
      sync.Cond
- [ ] Explain what causes goroutine leaks and how to prevent them
- [ ] Detect goroutine leaks using NumGoroutine and pprof
- [ ] Explain the difference between channels (communication) and
      mutexes (protecting shared state)

================================================================================
SECTION 7: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand Go's concurrency model (goroutines, channels,
context, synchronization), I have the tools to build concurrent Go
programs. The next topics in the Go L1→L2 progression are:

1. **Standard Library Deep Dive** — net/http, io, encoding/json,
   database/sql, time, os. The standard library is where Go shines.

2. **Project Structure and Package Design** — standard Go project
   layout, package naming, visibility, design of public APIs.

3. **Testing Deep Dive** — table-driven tests in depth, subtests,
   benchmarks, fuzz testing, mock testing with interfaces.

4. **Error Handling Patterns in Practice** — designing error types
   for specific domains, error wrapping chains, error inspection
   patterns.

5. **Generics (Go 1.18+)** — type parameters, constraints, when
   generics help vs when they make code unreadable.

Concurrency is the hardest part of Go for most people to master.
Understanding it deeply means you can write Go that's concurrent,
correct, and idiomatic.

================================================================================
END OF GO DEEP STUDY — CONCURRENCY
================================================================================
