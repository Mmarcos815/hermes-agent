# ===========================================================================
# C DEEP STUDY — POINTERS, MEMORY & THE COMPILATION MODEL
# ===========================================================================
# Date: 2026-08-19
# Status: Deep study in progress
# Prerequisites: None (this is the foundation for everything else)

## WHY THIS STUDY MATTERS

C is the language that everything else is built on. Understanding C
deeply means understanding what's happening under the hood of every
other language. Pointers, memory layout, and the compilation model
are the foundation of systems programming.

This targets L2 understanding: can explain pointers fluently, can
reason about memory, can understand the compilation pipeline and
linkage.

================================================================================
SECTION 1: WHAT C IS — AND WHY IT MATTERS
================================================================================

C was created by Dennis Ritchie at Bell Labs in the early 1970s for
writing Unix. It was designed to be:
- **Close to the hardware**: C gives you direct access to memory,
  addresses, and machine-level operations.
- **Portable**: C code can be compiled on different machines with
  minimal changes (in theory — in practice, this varies).
- **Efficient**: C code compiles to efficient machine code with
  minimal runtime overhead.
- **Simple**: C has a small language spec. No OOP, no generics, no
  exceptions, no GC. Just types, functions, and memory.

C is THE systems programming language. Operating systems, embedded
systems, compilers, databases, network stacks — all written in C
(or C++). If you want to understand how computers work, C is the
language to learn.

================================================================================
SECTION 2: POINTERS — THE FOUNDATION OF C
================================================================================

### What a Pointer Is

A pointer is a variable that holds a memory address. The address
points to (hence "pointer") another variable.

    int x = 42;
    int *p = &x;   // p holds the address of x

    printf("%d\n", x);   // 42 — the value
    printf("%p\n", p);   // 0x7fff... — the address of x
    printf("%d\n", *p);  // 42 — the value at that address (dereferencing)

The & operator gives you the address of a variable. The * operator
(dereferencing) gives you the value at that address.

### Pointer Declaration and Syntax

    int *p;         // p is a pointer to int
    char *c;        // c is a pointer to char
    void *v;        // v is a pointer to anything (void pointer)

The * in the declaration means "this is a pointer." It's part of
the type, not part of the variable name. So `int *p` means "p is
of type pointer-to-int."

You can also declare multiple pointers at once, but it's confusing:

    int *p1, p2;    // p1 is a pointer to int, p2 is just an int
    int *p1, *p2;   // both are pointers to int

The rule: the * binds to the variable name, not the type. So in
`int *p1, p2`, only p1 gets the *. This is why many style guides
recommend writing `int* p` or always putting the * next to the type.

### Dereferencing — Accessing the Value

Dereferencing a pointer means accessing the value at the address
the pointer holds.

    int x = 42;
    int *p = &x;
    *p = 100;      // sets x to 100 (through the pointer)
    printf("%d\n", x);  // 100

You can use a pointer to READ or WRITE the value it points to. Both
use the * operator.

### The Arrow Operator — Struct Pointers

When you have a pointer to a struct, you use the -> operator to
access fields:

    struct Point { int x; int y; };
    struct Point p = {1, 2};
    struct Point *ptr = &p;

    ptr->x = 10;   // equivalent to (*ptr).x = 10
    ptr->y = 20;

The -> operator is sugar for "dereference, then access field." It's
cleaner than writing (*ptr).x.

### Pointer Arithmetic — Moving Through Memory

You can do arithmetic on pointers. Adding 1 to a pointer moves it
to the next element of the pointed-to type.

    int arr[5] = {10, 20, 30, 40, 50};
    int *p = arr;     // points to arr[0] (arrays decay to pointers)

    printf("%d\n", *p);     // 10 — arr[0]
    printf("%d\n", *(p+1)); // 20 — arr[1]
    printf("%d\n", p[2]);   // 30 — arr[2] (pointer indexing)

    p++;  // now points to arr[1]
    printf("%d\n", *p);  // 20

Pointer arithmetic is scaled by the size of the pointed-to type.
Adding 1 to an int* moves by sizeof(int) bytes (typically 4).
Adding 1 to a char* moves by 1 byte.

This is how arrays work in C: an array is just a block of memory,
and array indexing arr[i] is sugar for *(arr + i).

### Arrays vs Pointers — The Confusion

Arrays and pointers are NOT the same, but they're closely related:

    int arr[5] = {1, 2, 3, 4, 5};
    int *p = arr;   // array decays to pointer to first element

    printf("%d\n", arr[2]);  // 3 — array indexing
    printf("%d\n", p[2]);    // 3 — pointer indexing (same result)

    // But:
    sizeof(arr);   // 5 * sizeof(int) = 20 (on 32-bit) — the FULL array size
    sizeof(p);     // sizeof(int*) = 4 or 8 — just the pointer size

    // And:
    arr++;   // ERROR — arr is an array, not a pointer. Can't increment.
    p++;     // OK — p is a pointer, can increment.

The key insight: in most contexts, an array "decays" to a pointer to
its first element. But sizeof and & are exceptions — they treat the
array as a whole.

### Pointers to Pointers

You can have pointers to pointers (and pointers to pointers to
pointers...). This is useful for:

    int x = 42;
    int *p = &x;      // p points to x
    int **pp = &p;    // pp points to p

    printf("%d\n", **pp);  // 42 — dereference twice to get to x

The classic use case: functions that modify a pointer:

    void allocate(int **ptr) {
        *ptr = malloc(sizeof(int));
        **ptr = 42;
    }

    int *p = NULL;
    allocate(&p);
    printf("%d\n", *p);  // 42
    free(p);

The function takes a pointer to a pointer, so it can modify the
caller's pointer variable. This is how C simulates "pass by reference"
for pointers.

### Void Pointers — Pointers to Anything

    void *v;

A void pointer can point to any type. It's used for generic
programming (like malloc, which returns void*):

    void *malloc(size_t size);   // returns void*

    int *p = malloc(sizeof(int) * 10);  // void* implicitly converts to int*
    // use p...
    free(p);

The trade-off: you can't dereference a void pointer directly — you
need to cast it to the correct type first. This loses type safety.

    void *v = &x;
    // printf("%d\n", *v);  // ERROR — can't dereference void*
    printf("%d\n", *(int*)v);  // OK — cast to int* first

### Const Correctness — When to Use const

const in pointer declarations can be confusing. There are four patterns:

    const int *p1;    // pointer to const int — can't modify *p1
    int * const p2;   // const pointer to int — can't modify p2 (the pointer itself)
    const int * const p3;  // const pointer to const int — can't modify either
    int const * p4;   // same as const int *p1 (const before type)

The rule: const applies to WHAT'S ON ITS LEFT (or the type if const
is first).

- `const int *p`: *p is const. You can change p (point it elsewhere),
  but you can't change the value it points to.
- `int * const p`: p is const. You can change *p (the value), but
  you can't change p (can't point it elsewhere).
- `const int * const p`: both are const. Nothing can change.

WHY THIS MATTERS: const tells the compiler (and other programmers)
what you intend to do with a pointer. It prevents accidental
modification and makes the API clearer.

================================================================================
SECTION 3: MEMORY — THE STACK, THE HEAP, AND BEYOND
================================================================================

### Memory Segments

A C program's memory is divided into segments:

1. **Text segment**: the compiled code (instructions). Read-only.
   Shared between processes running the same program.

2. **Data segment**: initialized global and static variables.
   - Initialized data: `int global = 42;` goes here.
   - Read-write (unless const).

3. **BSS segment**: uninitialized global and static variables.
   - `int global;` (no initializer) goes here.
   - Automatically zeroed by the OS.
   - BSS = "Block Started by Symbol" (historical name).

4. **Stack**: local variables, function call frames.
   - Grows downward (typically).
   - Each function call pushes a new frame.
   - Local variables live here.
   - Automatic storage: variables are created when the function is
     called and destroyed when it returns.

5. **Heap**: dynamically allocated memory (malloc, calloc, realloc).
   - Grows upward (typically).
   - You explicitly allocate and free.
   - Manual memory management.

### The Stack — Automatic Storage

Local variables live on the stack. They're created when the function
is called and destroyed when it returns. This is "automatic storage"
— the compiler handles it.

    void foo() {
        int x = 42;      // x is on the stack
        int *p = &x;     // p is also on the stack (but points to x, which is also on the stack)
    }   // x and p are destroyed when foo returns

Stack memory is fast (it's just moving a pointer). But it's limited
in size (typically a few MB). Large arrays on the stack can cause
stack overflow.

    void foo() {
        int big[1000000];  // ~4MB on the stack — might overflow
    }

Use the heap for large allocations.

### The Heap — Dynamic Allocation

The heap is manually managed memory. You allocate with malloc/calloc,
use it, then free it.

    int *p = malloc(sizeof(int) * 10);  // allocate space for 10 ints
    if (p == NULL) {
        // allocation failed — handle error
    }

    for (int i = 0; i < 10; i++) {
        p[i] = i * 10;
    }

    // use p...

    free(p);   // give the memory back
    p = NULL;  // good practice — avoid dangling pointer

Key things about the heap:
- It's manually managed. You must free what you malloc.
- It's slower than the stack (allocation involves finding free space).
- It's larger than the stack (limited by available memory, not a fixed size).
- Memory on the heap persists until freed (or the program exits).

### malloc, calloc, realloc, free — The Four Functions

**malloc**: allocate a block of memory. The memory is uninitialized
(contains garbage).

    void *malloc(size_t size);

    int *p = malloc(sizeof(int) * 10);
    // p[0] through p[9] are uninitialized — don't read them before writing

**calloc**: allocate and zero-initialize.

    void *calloc(size_t count, size_t size);

    int *p = calloc(10, sizeof(int));
    // p[0] through p[9] are all zero

calloc is generally safer (no garbage values to accidentally read).

**realloc**: resize an existing allocation.

    void *realloc(void *ptr, size_t new_size);

    int *p = malloc(sizeof(int) * 10);
    // ... use p ...
    p = realloc(p, sizeof(int) * 20);  // resize to 20 ints
    if (p == NULL) {
        // realloc failed — original p is still valid (don't lose it)
    }

IMPORTANT: realloc can move the memory to a new location. Always
assign the result back to the pointer. If realloc fails, it returns
NULL but the original memory is still valid — don't overwrite the
original pointer with NULL.

**free**: give memory back.

    void free(void *ptr);

    free(p);
    p = NULL;  // avoid dangling pointer

Only free memory that was allocated with malloc/calloc/realloc.
Freeing the same memory twice is an error (double-free).
Freeing a pointer that wasn't allocated is an error.

### Stack vs Heap — When to Use Each

- **Stack**: small, fixed-size local variables. Fast allocation.
  Automatic cleanup. Limited size.
- **Heap**: large allocations, data that needs to persist beyond
  the function that created it, data with dynamic size.

Example:

    // Small, fixed — use stack
    int sum(int *arr, int n) {
        int total = 0;  // stack — small, fixed
        for (int i = 0; i < n; i++) {
            total += arr[i];
        }
        return total;
    }

    // Large, dynamic — use heap
    int *read_numbers(const char *filename, int *count) {
        FILE *f = fopen(filename, "r");
        // ... count how many numbers ...
        int *numbers = malloc(*count * sizeof(int));
        // ... read numbers into array ...
        fclose(f);
        return numbers;  // caller must free
    }

### Common Memory Errors

1. **Use-after-free**: using memory after freeing it.
   int *p = malloc(sizeof(int));
   *p = 42;
   free(p);
   *p = 100;  // ERROR — use-after-free — undefined behavior

2. **Double-free**: freeing the same memory twice.
   free(p);
   free(p);  // ERROR — double-free — undefined behavior

3. **Memory leak**: allocating memory and never freeing it.
   for (int i = 0; i < 1000; i++) {
       malloc(sizeof(int));  // leak — never freed
   }
   // Memory usage grows without bound — eventually runs out

4. **Buffer overflow**: writing past the end of an allocation.
   int *p = malloc(sizeof(int) * 10);
   p[10] = 42;  // ERROR — off-by-one — writing past the end
   // undefined behavior — might corrupt other data, crash, or appear to work

5. **Reading uninitialized memory**:
   int *p = malloc(sizeof(int) * 10);
   int x = p[0];  // ERROR — p[0] is uninitialized (malloc doesn't zero)
   // The value is garbage — undefined behavior (reading uninitialized
   // memory is UB in C, not just "garbage value")

6. **Dangling pointer**: a pointer that points to freed memory.
   int *p = malloc(sizeof(int));
   free(p);
   // p is now a dangling pointer — points to freed memory
   // DON'T use p — set it to NULL after freeing

================================================================================
SECTION 4: THE COMPILATION MODEL
================================================================================

### The Four Stages of Compilation

C code goes through four stages to become an executable:

1. **Preprocessing**: handles directives that start with #.
   - #include: insert the contents of a header file.
   - #define: create macros (text substitution).
   - #ifdef/#ifndef/#endif: conditional compilation.
   - #pragma: compiler-specific directives.

   The preprocessor takes your .c file and produces a "translation
   unit" — a single file with all #includes expanded and macros
   substituted.

   // source.c
   #include <stdio.h>
   #define PI 3.14159
   int main() { printf("PI = %f\n", PI); return 0; }

   // After preprocessing (conceptually):
   // (contents of stdio.h inserted here)
   // ...
   int main() { printf("PI = %f\n", 3.14159); return 0; }

2. **Compilation**: the translation unit is compiled to assembly.
   The compiler parses the C code, checks types, resolves symbols
   (to some extent), and generates assembly code for the target
   architecture.

   // assembly.s (simplified)
   main:
       push rbp
       mov rbp, rsp
       ; ... code to call printf ...
       mov eax, 0
       pop rbp
       ret

3. **Assembly**: the assembly is converted to machine code (object
   file). The assembler produces a .o file (or .obj on Windows) that
   contains machine code, but with some symbols unresolved (external
   references).

   // object.o — contains machine code for main, but printf is undefined

4. **Linking**: object files are combined into an executable. The
   linker resolves external references (finds the address of printf,
   for example, in the C library) and produces the final executable.

   // a.out (or program.exe) — complete executable with all symbols resolved

### Translation Units — The Fundamental Unit

A translation unit is a .c file after preprocessing (all #includes
expanded). Each .c file is compiled independently into an object file.
The linker then combines the object files.

This is important: the compiler only sees ONE translation unit at a
time. It doesn't know about other .c files. That's why you need
header files — to tell the compiler about functions and types defined
in other translation units.

    // file1.c
    int x = 42;

    // file2.c
    extern int x;  // tells the compiler: "x is defined somewhere else"
    void foo() {
        printf("%d\n", x);  // OK — x is declared as extern
    }

Without the extern declaration in file2.c, the compiler would
complain about x being undefined.

### Linkage — Internal vs External

**External linkage**: a symbol (variable or function) with external
linkage is visible to other translation units. Other files can refer
to it.

    // file1.c
    int global_var = 42;  // external linkage (default for globals)
    void foo() { ... }    // external linkage (default for functions)

**Internal linkage**: a symbol with internal linkage is only visible
within the translation unit. Other files can't see it.

    // file1.c
    static int internal_var = 42;  // internal linkage — only visible in file1.c
    static void internal_func() { ... }  // internal linkage

    // file2.c
    extern int internal_var;  // ERROR — internal_var has internal linkage,
                              // can't be referenced from file2.c

The static keyword on a global variable or function gives it internal
linkage. This is how you hide implementation details — other files
can't access static variables or functions.

**No linkage**: local variables (inside functions) have no linkage.
They're only visible within the block they're declared in.

    void foo() {
        int x = 42;  // no linkage — only visible in foo()
    }

### Header Files — What Goes In Them

Header files (.h) contain DECLARATIONS, not definitions. They tell
the compiler what exists in other translation units.

    // mylib.h
    #ifndef MYLIB_H
    #define MYLIB_H

    // Function declarations (not definitions)
    int add(int a, int b);
    void print_message(const char *msg);

    // Type definitions (OK in headers — they're not "definitions" in
    // the linkage sense)
    typedef struct {
        int x;
        int y;
    } Point;

    // Const variables — OK (they have internal linkage by default)
    extern const int MAX_SIZE;  // declaration — must be defined in a .c file

    // Inline functions — OK (they're included in every translation unit
    // that includes the header, but the linker handles duplicates)
    static inline int square(int x) {
        return x * x;
    }

    #endif

Header files are included with #include, which literally copies the
contents of the header into the including file (after preprocessing).

Include guards (#ifndef/#define/#endif) prevent the header from being
included multiple times, which would cause duplicate declarations.

### What Does NOT Go In Headers

- Function DEFINITIONS (unless they're inline or static inline).
  A function definition in a header would be compiled into every
  translation unit that includes it, causing multiple definition
  errors at link time.
- Variable DEFINITIONS (unless they're static or inline const).
  int x = 42; in a header would be defined in every .c file that
  includes it — multiple definition error.
- Implementation details that callers don't need to know.

### Link Errors — Common Problems

1. **Undefined reference**: a symbol is declared but not defined.
   // mylib.h: extern int x;
   // main.c: #include "mylib.h" and uses x
   // BUT: no mylib.c defines int x = ...
   // Link error: undefined reference to `x'

   Fix: define the variable in a .c file:
   // mylib.c: int x = 42;

2. **Multiple definition**: a symbol is defined in multiple translation
   units.
   // mylib.h: int x = 42;  // WRONG — this is a definition
   // file1.c: #include "mylib.h"
   // file2.c: #include "mylib.h"
   // Link error: multiple definition of `x'

   Fix: use extern in the header, define in one .c file:
   // mylib.h: extern int x;
   // mylib.c: int x = 42;

3. **Missing library**: linking against a library that's not specified.
   // main.c: uses functions from libfoo
   // gcc main.c -o program   // WRONG — libfoo not linked
   // Link error: undefined reference to `foo_function'

   Fix: link the library:
   // gcc main.c -lfoo -o program

### Static Libraries vs Shared Libraries

**Static library (.a on Linux, .lib on Windows)**: an archive of
object files. When you link against a static library, the linker
copies the needed object code into your executable. The library code
becomes part of your executable.

    // Create a static library
    gcc -c file1.c file2.c      # compile to object files
    ar rcs libmylib.a file1.o file2.o   # create archive

    // Link against it
    gcc main.c -L. -lmylib -o program

    // The executable now contains the code from file1.o and file2.o

**Shared library (.so on Linux, .dll on Windows)**: a separate file
that the executable loads at runtime. The executable references the
shared library, and the dynamic linker loads it when the program runs.

    // Create a shared library
    gcc -c -fPIC file1.c file2.c   # compile with position-independent code
    gcc -shared -o libmylib.so file1.o file2.o   # create shared library

    // Link against it
    gcc main.c -L. -lmylib -o program

    // At runtime, the dynamic linker needs to find libmylib.so
    // Set LD_LIBRARY_PATH or use rpath

Shared libraries save disk space and memory (multiple programs can
share the same library in memory). They also allow updating the
library without recompiling the programs that use it.

================================================================================
SECTION 5: STRUCTS AND DATA LAYOUT
================================================================================

### Struct Basics

    struct Point {
        int x;
        int y;
    };

    struct Point p = {1, 2};        // initialization
    struct Point p2 = {.x = 1, .y = 2};  // designated initializers (C99)

    p.x = 10;   // access field
    p.y = 20;

    struct Point *ptr = &p;
    ptr->x = 30;  // access through pointer

### Struct Size and Padding

Structs are padded for alignment. Each field is aligned to its natural
alignment (int is typically 4-byte aligned, double is 8-byte aligned).

    struct Example {
        char a;    // 1 byte
        // 3 bytes padding (to align int to 4-byte boundary)
        int b;     // 4 bytes
        char c;    // 1 byte
        // 3 bytes padding (to align struct to 4-byte boundary)
    };
    // sizeof(Example) = 12, not 6

The padding ensures that each field is aligned correctly in memory.
This is important for performance ( misaligned accesses can be slower
or even prohibited on some architectures).

You can control struct layout with:
- **Field order**: put larger fields first to minimize padding.
- **Pragma pack**: #pragma pack(1) removes padding (use with care —
  can cause unaligned accesses).
- **Static assertion**: _Static_assert(sizeof(struct) == expected,
  "wrong size") to verify layout.

### Flexible Array Members (C99)

    struct String {
        size_t length;
        char data[];    // flexible array member — no size specified
    };

    // Allocate with extra space for the array
    struct String *create_string(const char *s) {
        size_t len = strlen(s);
        struct String *str = malloc(sizeof(struct String) + len + 1);
        str->length = len;
        memcpy(str->data, s, len + 1);  // include null terminator
        return str;
    }

The flexible array member allows a struct to have a variable-size
tail. The struct itself has a fixed size (sizeof doesn't include the
flexible array), but you allocate extra space for the array when you
create the struct.

This is the C way to have a variable-length payload in a struct.
It's used in network packets, file formats, and similar situations.

================================================================================
SECTION 6: FUNCTION POINTERS
================================================================================

A function pointer is a pointer to a function. It allows you to
pass functions as arguments, store them in data structures, and
call them dynamically.

    int add(int a, int b) { return a + b; }
    int multiply(int a, int b) { return a * b; }

    // Declare a function pointer type
    typedef int (*math_func)(int, int);

    math_func op = add;        // point to add
    printf("%d\n", op(2, 3)); // 5 — calls add(2, 3)

    op = multiply;             // point to multiply
    printf("%d\n", op(2, 3)); // 6 — calls multiply(2, 3)

Function pointer syntax is confusing. The key parts:
- `int (*op)(int, int)`: op is a pointer to a function that takes
  two ints and returns an int.
- `op(2, 3)`: call the function through the pointer. You can also
  write `(*op)(2, 3)` but the dereference is optional.

Function pointers are used for:
- Callbacks (e.g., qsort's comparison function).
- Tables of functions (dispatch tables).
- Plugins and dynamic behavior.
- Implementing state machines (state = function pointer).

    // qsort uses a function pointer for comparison
    int compare_ints(const void *a, const void *b) {
        int ia = *(const int*)a;
        int ib = *(const int*)b;
        return ia - ib;
    }

    int arr[] = {5, 2, 8, 1, 9};
    qsort(arr, 5, sizeof(int), compare_ints);

================================================================================
SECTION 7: EVIDENCE CHECKPOINTS — C POINTERS, MEMORY, COMPILATION (L2)
================================================================================

Can you:

- [ ] Explain what a pointer is and how & and * work
- [ ] Declare and use pointers correctly (including const correctness)
- [ ] Do pointer arithmetic and explain how it's scaled by type size
- [ ] Explain arrays vs pointers (decay, sizeof difference, indexing)
- [ ] Explain pointers to pointers and when they're used
- [ ] Use void pointers and explain the type safety trade-off
- [ ] Explain the four memory segments (text, data, BSS, stack, heap)
- [ ] Use malloc, calloc, realloc, free correctly
- [ ] Check for NULL after malloc/realloc
- [ ] Explain the difference between stack and heap and when to use each
- [ ] Identify and explain common memory errors (use-after-free,
      double-free, leak, buffer overflow, uninitialized read, dangling pointer)
- [ ] Explain the compilation model: preprocessing → compilation →
      assembly → linking
- [ ] Explain translation units and why they matter (each .c file
      is compiled independently)
- [ ] Explain linkage: external, internal (static), no linkage
- [ ] Write correct header files with include guards
- [ ] Explain what goes in headers (declarations) and what doesn't
      (definitions, except inline/static)
- [ ] Debug link errors: undefined reference, multiple definition
- [ ] Create and use static libraries (.a) and shared libraries (.so)
- [ ] Explain struct padding and alignment, and how to control it
- [ ] Use flexible array members (C99)
- [ ] Use function pointers (declaration, calling, typedef)
- [ ] Read a C program and trace through the memory layout and
      compilation pipeline

================================================================================
SECTION 8: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand pointers, memory, the compilation model, and
structs, the next topics in the C L2→L3 progression are:

1. **Strings in C** — C strings are null-terminated char arrays.
   string.h functions, buffer overflow risks, safe alternatives.

2. **File I/O** — fopen, fclose, fread, fwrite, fseek, fprintf,
   fscanf, error handling with errno.

3. **Make and CMake** — building multi-file C projects, Makefiles,
   CMake basics.

4. **Undefined Behavior Deep Dive** — all the common UBs and why
   each is UB. Understanding this is critical for writing safe C.

5. **Data Structures in C** — linked lists, hash tables, binary
   trees, heaps. Implementing these from scratch is L3 evidence.

6. **Debugging Tools** — GDB, valgrind, AddressSanitizer, UBSan.

Each builds on the foundation. You can't implement data structures
without understanding pointers and memory. You can't use GDB
effectively without understanding the compilation model and stack
layout.

================================================================================
END OF C DEEP STUDY — POINTERS, MEMORY & COMPILATION
================================================================================
