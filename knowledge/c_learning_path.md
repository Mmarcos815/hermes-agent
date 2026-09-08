# ===========================================================================
# C LEARNING PATH — L2 → L4
# ===========================================================================
# From: programming_lang_self_audit.md (C: L2 → Target L4)
# Date: 2026-08-19
# Status: Active learning plan

## CURRENT STATE (HONEST)

- Can read C code and understand it
- Explain pointers, malloc/free, compilation model conceptually
- Understand what undefined behavior is, name common UB pitfalls
- Explain stack vs heap, memory layout conceptually
- CANNOT write C programs independently with confidence
- CANNOT use valgrind, sanitizers, or GDB fluently
- CANNOT implement data structures from scratch in C without reference
- CANNOT understand the full compile/link model in practice

## TARGET: L4 (Proficient)

Can write production C code that's safe, portable, and efficient.
Understands the C memory model deeply. Can use advanced features
(variadic functions, designated initializers, flexible array members,
_Generic, inline functions). Can work with C codebases of 100K+ lines.
Understands ABI compatibility, FFI, cross-compilation.

================================================================================
PHASE 1: L2 → L3 (Weeks 1-6, solidifying foundations)
================================================================================

### GOAL
Go from "can read C conceptually" to "can write C programs
independently — pointers, memory management, structs, file I/O,
basic data structures."

### WHAT TO LEARN

1. **Pointers — THE FOUNDATION (this is where L2 becomes L3)**
   - Pointer declaration: int *p, char *s, void *vp
   - Dereferencing: *p
   - Pointer arithmetic: p++, p+1, ptrdiff_t
   - Arrays vs pointers: array decay, pointer to array, array of pointers
   - Pointer to pointer: int **pp
   - Function pointers: declaration, calling, using them (qsort callback)
   - NULL pointer and why it exists
   - Const correctness: const int *p (pointer to const int),
     int * const p (const pointer to int), const int * const p
   - Why const matters for safety and API design

2. **Memory Management**
   - malloc, calloc, realloc, free — the four functions
   - Stack vs heap: when each is used, lifetime differences
   - Memory layout: text, data, bss, heap, stack segments
   - Common errors: memory leaks, use-after-free, double-free,
     buffer overflow, off-by-one
   - init values: uninitialized memory is garbage — always initialize
   - malloc failure: always check for NULL

3. **The Compilation Model**
   - Preprocessing: #include, #define, macros, conditional compilation
   - Compilation: source → object file (.o)
   - Assembly: object file → machine code
   - Linking: object files → executable
   - Translation units: one .c file (after preprocessing) = one TU
   - Linkage: extern (external), static (internal)
   - Header files: what goes in them (declarations), what doesn't
     (definitions — except inline, templates in C++)
   - Include guards: #ifndef/#define/#endif
   - Forward declarations: when and why
   - Link errors: undefined reference, multiple definition — how to debug
   - Shared libraries (.so/.dll): sonames, LD_LIBRARY_PATH, rpath
   - Static libraries (.a): archiving, linking

4. **Structs and Data Layout**
   - Struct definition, initialization (designated initializers C99)
   - Struct padding and alignment: why the compiler adds padding
   - sizeof, offsetof, alignof (C11 _Alignof)
   - Flexible array members: struct { int n; double data[]; }
   - Bit fields: when to use, portability concerns
   - Unions: when to use, size = largest member

5. **Strings in C (the hard part)**
   - C strings are null-terminated char arrays — no length stored
   - string.h: strcpy, strncpy, strcat, strcmp, strlen, strchr, strstr,
     memcpy, memmove, memset
   - Buffer overflow with strcpy — use strncpy or snprintf instead
   - The semantics of strncpy (doesn't null-terminate if src >= n)
   - Why C strings are dangerous and how to be careful
   - Alternative: use a length-tracked string representation

6. **File I/O**
   - fopen, fclose, fread, fwrite, fseek, ftell, rewind
   - Text mode vs binary mode (b flag)
   - fprintf, fscanf, fgets, fgetc
   - stdin, stdout, stderr
   - Error handling: ferror, feof, errno

7. **Make and Build Systems**
   - Basic Makefiles: rules, dependencies, variables
   - CC, CFLAGS, LDFLAGS, LDLIBS
   - Pattern rules: %.o: %.c
   - Phony targets: clean, all, install
   - CMake basics (if Make is too limited):
     cmake_minimum_required, project, add_executable, target_link_libraries

### PROJECTS

**Project 1: String Utilities Library**
- Implement safe versions of strcpy, strcat, strcmp, etc.
- A function that splits a string by a delimiter
- Unit tests using a simple test harness
- Package as a library (.a) with a header file
- Practice: pointers, strings, header design, make

**Project 2: Linked List Implementation**
- Implement a singly-linked list with: push, pop, insert, delete,
  search, iterate
- Generic list using void* (and explain the type safety trade-off)
- Or typed list for a specific type (e.g., int list)
- Practice: pointers, memory management, function pointers for callbacks

**Project 3: Simple Text Processing Tool**
- Read a file, count lines/words/chars (like wc)
- Or filter lines matching a pattern (like grep)
- Practice: file I/O, string processing, buffer management

**Project 4: JSON Parser (simple)**
- Parse a subset of JSON (objects, arrays, strings, numbers, booleans,
  null) into a tree of structs
- Stringify back to JSON
- Practice: structs, memory, recursion, string parsing

### SOURCE TO READ

- "C Programming: A Modern Approach" by K.N. King (the best C book —
  read cover to cover)
- "Effective C" by Robert C. Seacord — read for best practices
- C Standard (ISO/IEC 9899:2018 / C17) — skim for reference, dive into
  specific sections on pointers, memory, undefined behavior
- Read the source of a C library: sqlite (amalgamation is readable),
  or a small library like cURL's library, or redis

### EVIDENCE CHECKPOINTS (L3)

- [ ] Can write C programs that compile and run without memory errors
- [ ] Can explain pointers fluently: declaration, dereferencing,
      arithmetic, arrays vs pointers
- [ ] Can use malloc/free correctly in all cases (check NULL, free
      what you alloc, no double-free)
- [ ] Understands the compilation model: preprocessor → compiler →
      assembler → linker, translation units, linkage
- [ ] Can write and use header files correctly (include guards,
      declarations vs definitions)
- [ ] Understands struct padding/alignment and can predict sizeof
- [ ] Can implement a linked list, hash table, or tree in C
- [ ] Can use Make or CMake to build a multi-file project
- [ ] Can use valgrind to detect memory errors
- [ ] Can explain const correctness and when to use each form
- [ ] Has built 4 C projects (string lib, linked list, text tool, JSON parser)

================================================================================
PHASE 2: L3 → L4 (Weeks 7-14, deepening)
================================================================================

### GOAL
Go from "can write C with fundamentals" to "can write production C
that's safe, portable, and efficient. Can work with large C codebases.
Understands advanced C features and the ABI."

### WHAT TO LEARN

1. **Undefined Behavior — DEEP**
   - All the common UBs and why they're UB (not just "don't do it"):
     - Uninitialized variables (reading them is UB in C, not just
       "garbage value")
     - Buffer overflows (writing past array bounds)
     - Use after free (even reading the pointer is UB)
     - Double free
     - Signed integer overflow (UB, unlike unsigned which wraps)
     - Null pointer dereference
     - Strict aliasing violations (type-punning through pointers)
     - Modifying a string literal (they're in read-only memory)
     - Out-of-bounds array access
     - Violating const (modifying through a const pointer)
   - Why UB is dangerous: the compiler can ASSUME it doesn't happen,
     leading to optimizations that break "working" code
   - So your "working" code with UB is NOT reliable — it can break
     with a different compiler, flags, or optimization level

2. **Sanitizers and Debugging Tools**
   - -fsanitize=address (AddressSanitizer): detects buffer overflows,
     use-after-free, double-free, memory leaks (partial)
   - -fsanitize=undefined (UBSan): detects undefined behavior
   - -Wall -Wextra -Werror: warnings as errors
   - GDB: breakpoints, stepping, inspecting variables, backtrace
   - Valgrind (Memcheck): memory errors and leaks
   - Core dumps: enabling (ulimit -c unlimited), analyzing with GDB

3. **Advanced C Features**
   - Variadic functions: stdarg.h, va_list, va_start, va_arg, va_end
     — and why they're dangerous (no type checking)
   - Designated initializers (C99): struct s = {.field = value}
   - Compound literals (C99): (struct S){.x = 1, .y = 2}
   - Inline functions (C99): static inline, extern inline
   - _Generic (C11): type-generic expressions (macro-like without macros)
   - _Alignas, _Alignof (C11)
   - typeof (GCC extension, widely used)
   - Zero-length arrays and flexible array members
   - Including binary data in executables (xxd -i, objcopy)

4. **ABI and Interoperability**
   - What ABI is: the contract between compiled components
   - Calling conventions: who cleans the stack, which registers are
     used for args and return values
   - Name mangling (C vs C++ — extern "C" in C++ for C linkage)
   - FFI: calling C from other languages (Python ctypes, CFFI, Ruby FFI,
     LuaJIT FFI), calling other languages from C
   - Cross-compilation: targeting different architectures

5. **Data Structures in C**
   - Hash tables: open addressing vs chaining, hash functions, resizing
   - Binary search trees: BST, AVL (optional), red-black (optional)
   - Heaps: binary heap implementation
   - Practice implementing these from scratch

6. **Large Codebase Navigation**
   - Reading and understanding C codebases of 100K+ lines
   - Understanding existing code structure, conventions, patterns
   - ctags, cscope, or LSP for code navigation
   - Understanding the relationship between .c and .h files across
     a large project

7. **Portability**
   - Writing portable C: avoid platform-specific APIs when possible
   - Feature test macros: _POSIX_C_SOURCE, _XOPEN_SOURCE, _GNU_SOURCE
   - Endianness: htonl, ntohl, htons, ntohs (network byte order)
   - Size assumptions: use sizeof, not assuming int is 4 bytes
   - Character encoding: ASCII assumptions vs UTF-8

### PROJECTS

**Project 5: Hash Table Library**
- Implement a hash table with string keys and void* values
- Chaining (linked list per bucket) or open addressing
- Insert, get, delete, resize when load factor exceeds threshold
- Proper memory management (free all entries on cleanup)
- API design: think about what a good C hash table API looks like

**Project 6: Rewrite One Project in C with Production Quality**
- Take a previous project (e.g., JSON parser) and make it production C:
  - Sanitizers clean (no UB)
  - Valgrind clean (no leaks)
  - Well-documented header API
  - Test suite
  - Makefile/CMake build

**Project 7: Contribute to a C Project**
- Find a C project you use (SQLite, a small library, a tool)
- Find a bug, fix it, submit a PR
- Or contribute documentation, tests, or a small feature

### SOURCE TO READ

- Read the C standard sections: 6 (Language), 7 (Library), especially
  the sections on pointers, arrays, memory, UB
- Read SQLite source (the amalgamation is one file, ~multi-thousand lines
  but highly readable and well-commented)
- "Expert C Programming: Deep C Secrets" by Peter van der Linden —
  classic, covers the deep stuff
- "Deep C Secrets" for the advanced/understood topics
- Look at how well-regarded C libraries are structured (openssl, libuv,
  zlib — pick one and study its design)

### EVIDENCE CHECKPOINTS (L4)

- [ ] Can identify all common UB and explain why each is UB
- [ ] Can use AddressSanitizer and UBSan fluently
- [ ] Can use GDB to debug C programs (breakpoints, stepping, inspecting)
- [ ] Can use valgrind and interpret its output
- [ ] Can write variadic functions correctly (know the dangers)
- [ ] Can use _Generic, designated initializers, compound literals
- [ ] Understands ABI: calling conventions, name mangling, FFI
- [ ] Has implemented a hash table and at least one other data structure
      from scratch in C
- [ ] Can read and navigate a large C codebase (100K+ lines)
- [ ] Has contributed to a C project (PR, documentation, tests)
- [ ] Can write portable C (feature test macros, no size assumptions,
      endianness awareness)
- [ ] Can explain the C memory model deeply (segments, alignment, padding)

================================================================================
PHASE 3: L4 → L5 (Long-term, ultimate)
================================================================================

### WHAT IT TAKES

- Contribute to C standard library implementations (glibc, musl, etc.)
- Understand C at the language specification level (the standard document)
- Design C APIs that are safe and ergonomic (hard in C — this is a skill)
- Teach C and explain why certain patterns are dangerous
- Understand C history: K&R C → ANSI C (C89) → C99 → C11 → C17 → C23
  and what each version added
- Read and understand C compiler source (GCC, Clang) for relevant
  components

================================================================================
SUMMARY: C ROADMAP
================================================================================

| Phase | From→To | Duration | Focus                          | Key Evidence                     |
|-------|---------|----------|--------------------------------|----------------------------------|
| 1     | L2→L3   | Weeks 1-6| Pointers, memory, build model | 4 projects, valgrind clean, can  |
|       |         |          | structs, strings, make/cmake  | build multi-file projects        |
| 2     | L3→L4   | Weeks 7-14| UB deep, sanitizers, GDB,   | Hash table lib, production C,   |
|       |         |          | advanced features, ABI,      | contributed to C project         |
|       |         |          | data structures, large code  |                                  |
| 3     | L4→L5   | Long-term| Standard lib contributions,   | Major contributions, teaching   |
|       |         |          | specification level, history |                                  |

Dad's priority: MEDIUM. C is foundational for systems programming
understanding. L4 is the target — safe, production C.

================================================================================
