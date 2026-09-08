# ===========================================================================
# TYPESCRIPT LEARNING PATH — L1 → L3
# ===========================================================================
# From: programming_lang_self_audit.md (TypeScript: L1 → Target L3)
# Date: 2026-08-19
# Status: Active learning plan

## CRITICAL NOTE

TypeScript mastery REQUIRES JavaScript mastery first. L1 in TypeScript
with L2 in JavaScript means the JavaScript foundation is being built.
You CANNOT reach TypeScript L3 without JavaScript L3.

If JavaScript is still L2, focus there FIRST. TypeScript builds on
JavaScript — the type system is layered on top.

## CURRENT STATE (HONEST)

- Can read TypeScript code and understand it
- Use basic types: interfaces, type aliases, unions, generics (basic)
- Understand the relationship between TypeScript and JavaScript
- CANNOT use advanced TypeScript features fluently (conditional types,
  mapped types, template literal types, infer)
- CANNOT design type-safe APIs using the type system
- CANNOT configure TypeScript precisely for large projects
- CANNOT debug complex type errors

## TARGET: L3 (Competent)

Can use all major TypeScript features, understand the type system
deeply, write generic functions and types, use utility types,
use type narrowing effectively, use TypeScript with React, configure
TypeScript for projects.

================================================================================
PHASE 1: L1 → L2 (Weeks 1-3, building the type system foundation)
================================================================================

### GOAL
Go from "can read TS" to "can write TS fluently with basic types,
understand the fundamental type system concepts, can use TypeScript
with Node.js and basic React."

### WHAT TO LEARN

1. **TypeScript Setup and Configuration**
   - tsconfig.json: compiler options, target, module, strict,
     esModuleInterop, skipLibCheck
   - tsc: the TypeScript compiler, what it does (type checking + transpilation)
   - ts-node / tsx: running TS directly
   - Integrating with Node.js: tsconfig for Node, module resolution
   - Integrating with React/CRA/Vite: TS configuration in the frontend
     ecosystem

2. **Basic Types — BUILDING BLOCKS**
   - Primitives: string, number, boolean, null, undefined, symbol, bigint
   - Arrays: string[], Array<string>, readonly string[]
   - Tuples: [string, number], readonly [string, number],
     labeled tuples (TS 4.0+)
   - Enum: numeric enums, string enums, const enums (and the caveats)
   - Union types: string | number, "a" | "b" | "c" (literal unions)
   - Intersection types: A & B (combine types)
   - Type aliases vs interfaces: when to use each
   - Any vs unknown vs never: the type hierarchy of "nothingness"
   - void, undefined, null in function returns

3. **Type Inference**
   - When TypeScript infers types: variable declarations, function return
     types, generic arguments
   - When it falls back to any (noImplicitAny, strict mode)
   - Best common type inference: union of types from an array
   - Contextual typing: function parameters, return types in assignments

4. **Functions in TypeScript**
   - Function types: (x: number) => string
   - Optional parameters: (x?: number) = string | undefined
   - Default parameters
   - Rest parameters: ...args: string[]
   - Overloads: function foo(x: string): string; function foo(x: number): number;
     (TS function overloading — it's declaration merging, not real overloading)
   - this typing in functions

5. **Objects and Interfaces**
   - Interface: interface Point { x: number; y: number; }
   - Optional properties: x?: number
   - Readonly properties: readonly x: number
   - Extending interfaces: interface Point3D extends Point { z: number; }
   - Index signatures: [key: string]: number
   - Call signatures: interface Counter { (start: number): number; }
   - Constructor signatures: new (x: number): Foo

6. **Classes in TypeScript**
   - Class syntax (same as ES6 classes) with type annotations
   - Access modifiers: public, private, protected, readonly
   - Parameter properties: constructor(public name: string) {}
   - Abstract classes and methods
   - Implementing interfaces
   - Class expressions with types
   - This types in classes

### PROJECTS

**Project 1: Typed Node.js CLI**
- A Node.js CLI tool using TypeScript
- Practice: tsconfig, running TS, types for process.argv, file I/O
- Add types for everything

**Project 2: Typed API Client**
- A TypeScript client for a REST API (use fetch or axios)
- Define interfaces for the API responses and requests
- Practice: interfaces, generics (generic response types), union types
- Type-safe API methods

**Project 3: React Component Library (small)**
- A few React components written in TypeScript
- Practice: JSX with TypeScript, typing props, children, event handlers
- Use React's built-in types (React.FC, React.ReactNode, etc.)

### SOURCE TO READ

- TypeScript Handbook (https://www.typescriptlang.org/docs/handbook/
  introduction.html) — read cover to cover
- TypeScript Deep Dive (https://basarat.gitbook.io/typescript/) —
  excellent resource, read the type system sections
- TypeScript RFCs and release notes for recent versions (TS 4.x, 5.x)
  — understand new features

### EVIDENCE CHECKPOINTS (L2)

- [ ] Can configure TypeScript for Node.js and React projects
- [ ] Can use all basic types: primitives, arrays, tuples, enums,
      unions, intersections, type aliases, interfaces
- [ ] Understands type inference and when it falls back to any
- [ ] Can write typed functions with proper parameter and return types
- [ ] Uses any sparingly (only when truly necessary)
- [ ] Can use TypeScript with React: typing props, children, events
- [ ] Has built 3 TypeScript projects (CLI, API client, React components)
- [ ] Can explain the difference between interface and type alias
- [ ] Can read and understand TypeScript error messages

================================================================================
PHASE 2: L2 → L3 (Weeks 4-10, deepening into the type system)
================================================================================

### GOAL
Go from "can use basic TS types" to "can use the full type system:
generics, utility types, type narrowing, advanced types, design
type-safe APIs."

### WHAT TO LEARN

1. **Generics — THE HEART OF TS ABSTRACTION**
   - Generic functions: function identity<T>(x: T): T { return x; }
   - Generic types: interface Box<T> { value: T; }
   - Generic constraints: function max<T extends Comparable>(a: T, b: T): T
   - Default types for generics: function foo<T = string>(x: T)
   - Generic classes: class Pair<T, U> { first: T; second: U; }
   - Type inference for generics: TypeScript infers T from arguments
   - Multiple type parameters
   - Variance in TypeScript: covariance, contravariance, invariance
     — TypeScript uses structural typing with invariance for mutable
       properties. Understand what this means for assignability.
   - Generic constraints to express relationships: function merge<T extends
     U, U>(obj1: T, obj2: U): T & U

2. **Utility Types — THE STANDARD LIBRARY OF TYPES**
   - Partial<T>: all properties optional
   - Required<T>: all properties required
   - Readonly<T>: all properties readonly
   - Pick<T, K>: pick specific keys
   - Omit<T, K>: omit specific keys
   - Record<K, V>: object type with specific key/value types
   - ReturnType<T>: extract return type of a function
   - Parameters<T>: extract parameters of a function
   - ConstructorParameters<T>: extract constructor parameters
   - Extract<T, U>: extract types from union that are assignable to U
   - Exclude<T, U>: exclude types from union that are assignable to U
   -NonNullable<T>: exclude null and undefined
   - Uppercase, Lowercase, PascalCase, Snapshot (TS 4.1+ string manipulation)
   -Awaited<T> (TS 4.5+): unwrap Promise types

3. **Type Narrowing — THE TYPE GUARD SYSTEM**
   - Type predicates: function isFish(pet: Fish | Bird): pet is Fish
   - instanceof narrowing: works with classes
   - typeof narrowing: "string", "number", "boolean", "object", "function"
   - Discriminated unions: a shared literal property that TypeScript uses
     to narrow — the most powerful pattern in TS
     interface Cat { kind: "cat"; meow(): void; }
     interface Dog { kind: "dog"; bark(): void; }
     function makeSound(pet: Cat | Dog) {
       if (pet.kind === "cat") { pet.meow(); } else { pet.bark(); }
     }
   - The never type in narrowing: exhaustiveness checking
     function assertNever(x: never): never { throw new Error(); }
   - Type guards with custom logic (user-defined type guards)
   - Narrowing with null/undefined: strictNullChecks impact

4. **Advanced Types**
   - Conditional types: T extends U ? X : Y
     — The ternary of the type system
     — Distributive conditional types: when T is a union, the condition
       distributes over each member
   - Mapped types: { [K in keyof T]: T[K] }
     — Transform property types: make all properties optional, readonly,
       or apply a transformation
     — Key remapping: { [K in keyof T as NewKey<K>]: T[K] } (TS 4.1+)
   - Template literal types (TS 4.1+): `${infer First}-${infer Rest}`
     — Type-level string manipulation
     — Extract types from strings, build new types from strings
   - infer keyword in conditional types: extract types from other types
     — type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
     — type ElementType<T> = T extends (infer E)[] ? E : never;
     — infer can appear in conditional types to "extract" a type

5. **Advanced Function Types**
   - This types in callbacks: function with explicit this parameter
   - Function overloads in depth: when to use, how they work
   - Constructor types: new () => T, abstract constructors
   - Method signatures vs function properties
   - This type in classes and interfaces

6. **Module System and Declaration Files**
   - ES modules in TypeScript: import/export with types
   - CommonJS interop: esModuleInterop, allowSyntheticDefaultImports
   - Declaration files (.d.ts): what they are, when they're needed
   - Writing declaration files for JavaScript libraries
   - DefinitelyTyped: @types packages, contributing
   - Module resolution: how TypeScript finds modules

7. **React + TypeScript (if relevant)**
   - Typing props: interface Props { name: string; }
   - Typing children: React.ReactNode, React.FC<Props>
   - Typing event handlers: React.ChangeEventHandler<HTMLInputElement>,
     React.FormEvent
   - Generic components: <T extends Item>(item: T) => JSX
   - Conditional props: discriminated unions for component props
   - useRef typing: React.RefObject<T>, useRef<T>(null)
   - useState typing: useState<T>(initial)
   - useReducer typing: Reducer<State, Action>
   - Typing context: React.Context<T>

### PROJECTS

**Project 4: Type-Safe API Layer**
- A typed wrapper around fetch or axios that uses generics for response
  types
- Type-safe endpoints: typed request bodies and response types
- Error handling with proper types
- Show how TypeScript prevents API misuse at compile time

**Project 5: Typed State Management**
- A small state management library in TypeScript
- Use generics for typed state and actions
- Type-safe dispatch: only valid actions are accepted
- Show discriminated unions for actions

**Project 6: React App with Full TypeScript**
- A non-trivial React application using TypeScript
- Proper typing throughout: components, hooks, API calls, state
- Use advanced types: discriminated unions for state, mapped types for
  derived state, generics for reusable components
- TypeScript strict mode on, no anys

### SOURCE TO READ

- TypeScript Handbook: "Generics", "Utility Types", "Conditional Types",
  "Mapped Types", "Type Guards", "Module Resolution"
- TypeScript release notes for 4.1 (template literal types), 4.5 (Awaited),
  4.9 (satisfies operator), 5.x changes
- Read the source of a TypeScript library's type definitions (e.g., React's
  types in @types/react, or a well-typed library like zustand, react-query)
- "Type Challenges" (https://github.com/type-challenges/type-challenges) —
  solve the easy/medium challenges to build type system mastery

### EVIDENCE CHECKPOINTS (L3)

- [ ] Can write generic functions and types with constraints and defaults
- [ ] Can use all major utility types: Partial, Required, Pick, Omit,
      Record, ReturnType, Parameters, Extract, Exclude, NonNullable
- [ ] Can design discriminated unions for type-safe state/actions
- [ ] Can use type narrowing: type predicates, instanceof, typeof,
      discriminated unions
- [ ] Can read and write conditional types: T extends U ? X : Y
- [ ] Can use mapped types: transform properties, remap keys
- [ ] Can use template literal types and infer (basic)
- [ ] Can configure TypeScript precisely: strict mode, target, module,
      paths, composite projects
- [ ] Can debug tricky type errors (understand why TS inferred a type,
      how to fix it)
- [ ] Has built a type-safe API layer, typed state management, and a
      full TypeScript React app
- [ ] Has solved type challenges (demonstrates type system proficiency)
- [ ] Can explain variance in TypeScript
- [ ] Can teach TypeScript basics to someone at L1

================================================================================
PHASE 3: L3 → L4 (Months 3-6, advanced mastery)
================================================================================

### GOAL
Can build large, type-safe applications. Designs libraries with
expressive types that prevent misuse at compile time. Understands
what TS can and can't express. Can debug complex type errors.
Can configure TS precisely for large projects.

### WHAT TO LEARN

- Designing type-safe library APIs: make illegal states unrepresentable
- Conditional types in depth: infer in complex positions, distributive
  conditional types, type-level programming
- Mapped types with key remapping and template literals
- Template literal types for type-level string manipulation
- Type-level programming: building types that compute at compile time
- Understanding TypeScript's type system limitations: not sound,
  can't express certain constraints
- TypeScript compiler API: writing transformers, custom diagnostics
- Integrating TypeScript with build tools: Babel, SWC, esbuild, Vite,
  webpack — how TS fits into the build pipeline
- Monorepo TypeScript: project references, composite projects,
  incremental builds

### EVIDENCE (L4)

- [ ] Can design type-safe library APIs
- [ ] Can use conditional types and infer fluently
- [ ] Can use template literal types for type-level computation
- [ ] Can debug complex type errors
- [ ] Can configure TypeScript for large projects (paths, project
      references, strict settings)
- [ ] Has built a library with expressive types that prevent misuse

================================================================================
SUMMARY: TYPESCRIPT ROADMAP
================================================================================

| Phase | From→To | Duration | Focus                          | Key Evidence                     |
|-------|---------|----------|--------------------------------|----------------------------------|
| 1     | L1→L2   | Weeks 1-3| Setup, basic types,           | 3 TS projects, can configure    |
|       |         |          | inference, functions, classes | TS, can use basic types         |
| 2     | L2→L3   | Weeks 4-10| Generics, utility types,     | Type-safe API, typed state,    |
|       |         |          | type narrowing, advanced types| React app, type challenges      |
| 3     | L3→L4   | Months 3-6| Type-level programming,     | Library with expressive types, |
|       |         |          | library design, TS compiler  | complex type debugging          |

Dad's priority: MEDIUM. TypeScript requires JavaScript L3 first.
JavaScript is currently L2 — the JS foundation must be solidified.

================================================================================
