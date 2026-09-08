# ===========================================================================
# TYPESCRIPT DEEP STUDY — TYPE SYSTEM FUNDAMENTALS
# ===========================================================================
# Date: 2026-08-19
# Status: Deep study in progress
# Prerequisites: JavaScript fundamentals (typed this study as L1→L2,
#                building on JS L2 knowledge)

## WHY THIS STUDY MATTERS

TypeScript is JavaScript with a type system layered on top. The type
system is what makes TypeScript valuable: it catches errors at compile
time, provides documentation through types, enables better tooling
(autocomplete, refactoring), and makes code more maintainable.

But TypeScript's type system is also complex. It has many features
(union types, intersection types, generics, conditional types, mapped
types, template literal types, etc.). Understanding the fundamentals
deeply means you can use the type system effectively and understand
what the compiler is doing.

This targets L2 understanding: can explain the core type system
concepts, use basic types fluently, understand type inference, and
read TypeScript error messages.

================================================================================
SECTION 1: WHAT TYPESCRIPT IS — AND WHY IT EXISTS
================================================================================

TypeScript is a superset of JavaScript created by Microsoft (led by
Anders Hejlsberg, who also created C#, Turbo Pascal, Delphi). It
adds a static type system to JavaScript.

The core idea: JavaScript is dynamic and flexible, which makes it
easy to write but hard to maintain at scale. TypeScript adds types
to catch errors early, document code, and enable better tooling.

Key facts:
- TypeScript compiles to JavaScript (any JavaScript runtime can run
  the output).
- TypeScript's type system is OPTIONAL — you can use TypeScript
  without types everywhere (though that defeats the purpose).
- TypeScript's type system is ERASED at compile time — the runtime
  JavaScript has no type information.
- TypeScript is not sound — the type system can't guarantee that
  all type errors are caught (there are escape hatches like `any`
  and type assertions).

TypeScript was designed for large-scale JavaScript development. The
types help manage complexity in large codebases.

================================================================================
SECTION 2: THE TYPE SYSTEM — CORE CONCEPTS
================================================================================

### Static Typing vs Dynamic Typing

JavaScript is dynamically typed: types are associated with values,
not variables. A variable can hold any type at any time.

    let x = 42;      // x is a number
    x = "hello";     // now x is a string — no error in JavaScript

TypeScript is statically typed (with inference): types are checked
at compile time. The compiler knows the type of every expression.

    let x = 42;      // x is inferred as number
    x = "hello";     // ERROR — Type 'string' is not assignable to type 'number'

The compiler catches the error before the code runs.

### Type Inference — The Compiler Figures Out Types

TypeScript infers types from context. You don't always need to write
type annotations.

    // Inference from initialization
    let x = 42;              // x: number
    let name = "Alice";      // name: string
    let items = [1, 2, 3];   // items: number[]

    // Inference from function return
    function add(a: number, b: number) {
        return a + b;        // return type inferred as number
    }

    // Inference from assignment
    let x: number;
    x = 42;   // OK
    x = "hello";  // ERROR

Type inference is powerful — in many TypeScript projects, you rarely
need to write type annotations. The compiler figures out the types
from the code.

But inference has limits. You need annotations when:
- The type can't be inferred from context (function parameters without
  default values, public class fields).
- You want to be explicit about the type (for documentation or to
  catch errors).
- The inferred type is too broad (e.g., inferring `any` when you
  want a specific type).

### The any Type — The Escape Hatch

`any` is a special type that disables type checking. A value of type
`any` can be used as any type.

    let x: any = 42;
    x = "hello";     // OK — any can be anything
    x = true;        // OK
    x.toFixed();     // OK — compiler doesn't check

    let y: any = "hello";
    y.toFixed();     // OK — no error at compile time
    // But at runtime: y.toFixed is not a function — TypeError

`any` is useful when:
- You're migrating JavaScript to TypeScript and don't know the types yet.
- You're working with a library that has no type definitions.
- You genuinely don't know the type and need to defers type checking.

But `any` should be used SPARINGLY. Every `any` is a place where the
type system is disabled — errors can slip through. The goal of
TypeScript is to minimize `any`.

### The unknown Type — The Safe any

`unknown` is the type-safe counterpart to `any`. A value of type
`unknown` can be anything, but you MUST narrow it to a specific type
before you can use it.

    let x: unknown = 42;
    x = "hello";     // OK — unknown can hold anything
    x.toFixed();     // ERROR — Object is of type 'unknown'

    // Must narrow first:
    if (typeof x === "number") {
        x.toFixed();   // OK — x is narrowed to number in this block
    }

`unknown` forces you to do type narrowing before using the value.
This catches errors that `any` would let slip through.

Use `unknown` when you genuinely don't know the type and want to
force type checking when you use the value. Use `any` only when you
need to completely disable type checking for a value.

### The void Type — "No Meaningful Return Value"

    function log(message: string): void {
        console.log(message);
        // returns undefined implicitly
    }

`void` means "this function returns nothing meaningful." The function
might return `undefined` (JavaScript default), but the caller should
ignore the return value.

`void` is different from `undefined`:
- `undefined` is a specific value — the function returns the value
  `undefined`.
- `void` means the return value is not useful. A function returning
  `void` might actually return `undefined`, or it might return
  something that the caller should ignore.

In practice, `void` is used for functions with side effects (logging,
writing to a file, updating state) that don't return a meaningful
value.

### The never Type — Impossible Values

`never` represents a value that can never occur. It's used for:

1. **Functions that never return** (infinite loops, always throwing):
   function infiniteLoop(): never {
       while (true) { }
   }

   function alwaysThrows(): never {
       throw new Error("always");
   }

2. **Exhaustive type checking** (the "make the compiler check that
   all cases are handled" pattern):
   function assertNever(value: never): never {
       throw new Error("unexpected value: " + value);
   }

   type Shape = Circle | Square | Triangle;
   function area(shape: Shape) {
       switch (shape.kind) {
           case "circle": return ...;
           case "square": return ...;
           case "triangle": return ...;
           default: assertNever(shape);  // ERROR if a new shape is added
                                         // but not handled in the switch
       }
   }

If a new shape type is added but not handled in the switch, the
default case passes a Shape to assertNever, but the shape is not
`never` (it's the new shape type). The compiler errors because
`assertNever` expects `never` but got the new shape.

`never` is a powerful tool for exhaustive checking. It's also used
internally in advanced type system patterns.

================================================================================
SECTION 3: BASIC TYPES — BUILDING BLOCKS
================================================================================

### Primitives

    let x: number = 42;        // number — all numbers are floating point (f64)
    let y: string = "hello";   // string — Unicode strings
    let z: boolean = true;     // boolean — true or false
    let n: null = null;        // null — intentional absence of value
    let u: undefined = undefined;  // undefined — uninitialized or absent
    let sym: symbol = Symbol("id");  // symbol — unique identifiers
    let b: bigint = 123n;      // bigint — arbitrary-precision integers

All of these are JavaScript primitives. TypeScript just adds types
for them.

### Numbers

JavaScript has only one number type: number (IEEE 754 64-bit float).
There's no int, float, double, etc. — just number.

    let x: number = 42;
    let y: number = 3.14;
    let z: number = Infinity;
    let w: number = NaN;

TypeScript doesn't distinguish between integers and floats. All are
`number`. This can lead to subtle issues (e.g., `0.1 + 0.2 !== 0.3`
in JavaScript).

### Strings

Strings are UTF-16 encoded (JavaScript's string encoding). Template
literals use backticks and can interpolate expressions:

    let name = "Alice";
    let greeting = `Hello, ${name}!`;  // "Hello, Alice!"

TypeScript doesn't add anything special to strings — the types are
the same as JavaScript.

### Union Types — "This OR That"

A union type represents a value that can be one of several types.

    let id: string | number;   // id can be string OR number
    id = "abc123";   // OK
    id = 42;         // OK
    id = true;       // ERROR — boolean is not string or number

Union types are one of the most powerful features in TypeScript.
They let you model values that have different shapes in different
contexts.

    function format(value: string | number) {
        if (typeof value === "string") {
            return value.toUpperCase();  // value is string here
        } else {
            return value.toFixed(2);     // value is number here
        }
    }

TypeScript narrows the type based on the check (typeof, instanceof,
property checks, etc.). In the `if` branch, `value` is narrowed to
`string`. In the `else` branch, it's narrowed to `number`.

### Intersection Types — "This AND That"

An intersection type combines multiple types into one. The resulting
type has all the properties of all the combined types.

    interface Person {
        name: string;
        age: number;
    }

    interface Employee {
        employeeId: string;
        department: string;
    }

    type EmployeePerson = Person & Employee;

    let e: EmployeePerson = {
        name: "Alice",
        age: 30,
        employeeId: "E123",
        department: "Engineering",
    };

Intersection types are used for:
- Combining interfaces (mixing in behavior).
- Adding properties to existing types.
- Creating complex types from simpler ones.

But be careful: intersections of incompatible types can create
impossible types (e.g., `string & number` is `never` because
nothing can be both a string and a number).

### Literal Types — Specific Values as Types

TypeScript can use specific values as types. These are called literal
types.

    let x: 42 = 42;           // x can only be 42
    let y: "hello" = "hello"; // y can only be "hello"
    let z: true = true;       // z can only be true

Literal types are most useful in unions:

    function direction(dir: "north" | "south" | "east" | "west") {
        // ...
    }

    direction("north");   // OK
    direction("up");      // ERROR — "up" is not "north" | "south" | "east" | "west"

This is how TypeScript provides type-safe APIs with specific string
or number values.

### Enum — Named Constants

Enums in TypeScript are a way to define a set of named constants.

    enum Direction {
        North,
        South,
        East,
        West,
    }

    let d: Direction = Direction.North;

Numeric enums (the default) assign numbers starting from 0. You can
also have string enums:

    enum Direction {
        North = "NORTH",
        South = "SOUTH",
        East = "EAST",
        West = "WEST",
    }

Enums have some quirks:
- Numeric enums can be indexed by value to get the name (Direction[0] === "North").
- Enums are compiled to objects in JavaScript (they're not just types).
- Many TypeScript developers prefer union types of literals instead of
  enums, because they're simpler and don't have the runtime overhead.

The enum debate is a known thing in the TypeScript community. Both
approaches are valid — choose based on your needs.

### Arrays and Tuples

**Arrays**: a collection of elements of the same type.

    let numbers: number[] = [1, 2, 3];
    let names: Array<string> = ["Alice", "Bob"];

Both syntaxes are equivalent: `number[]` is sugar for `Array<number>`.

**Tuples**: an array with a fixed number of elements, each with a
specific type.

    let point: [number, number] = [10, 20];
    // point[0] is number, point[1] is number
    point[0] = "hello";  // ERROR — cannot assign string to number

Tuples are useful for representing fixed-length collections with
specific types at each position. They're commonly used for:
- Pairs of values (coordinates, key-value pairs).
- Return values from functions that return multiple values.
- React useState hook: `const [count, setCount] = useState(0)` —
  the return type is `[number, Dispatch<SetStateAction<number>>]`.

Tuples with labels (TypeScript 4.0+):

    type Point = [x: number, y: number];
    let p: Point = [10, 20];
    // p[0] is labeled as x, p[1] as y in tooling

### Objects and Interfaces

An interface defines the shape of an object — the properties it has
and their types.

    interface Person {
        name: string;
        age: number;
        email?: string;      // optional property
        readonly id: number; // can't be modified after creation
    }

    let alice: Person = {
        name: "Alice",
        age: 30,
        id: 1,
    };

    alice.name = "Alice Smith";   // OK
    alice.id = 2;                 // ERROR — id is readonly

Interfaces are one of the core TypeScript features. They define the
shape of objects and can be implemented by classes, used as function
parameters and return types, and extended by other interfaces.

### Type Aliases vs Interfaces

Both can describe the shape of an object:

    // Type alias
    type Person = {
        name: string;
        age: number;
    };

    // Interface
    interface Person {
        name: string;
        age: number;
    };

Key differences:

1. **Interfaces can be extended** (merged, inherited):
   interface Person { name: string; }
   interface Person { age: number; }   // Person now has both name AND age
   // This is "declaration merging" — unique to interfaces

2. **Type aliases can represent unions, intersections, primitives**:
   type ID = string | number;        // unions
   type Employee = Person & { id: string; };  // intersections
   type MaybeString = string | null;  // can't do this with interface

3. **Interfaces are open, type aliases are closed**:
   You can add to an interface later (declaration merging). A type
   alias is fixed once defined.

4. **Performance**: interfaces are faster for the compiler to check
   (they're structural and can be compared by name in some cases).
   Complex type aliases can slow down type checking.

In practice, use interfaces for object shapes (especially if you
might extend them) and type aliases for unions, intersections, and
complex type transformations.

================================================================================
SECTION 4: FUNCTIONS IN TYPESCRIPT
================================================================================

### Function Types

A function has a type that describes its parameters and return type.

    // Function declaration with types
    function add(a: number, b: number): number {
        return a + b;
    }

    // The type of `add` is: (a: number, b: number) => number

    // Function expression with explicit type
    const multiply: (a: number, b: number) => number = function(a, b) {
        return a * b;
    };

    // Arrow function with inferred type
    const divide = (a: number, b: number): number => a / b;

### Function Type Syntax

The function type syntax is: `(param1: type1, param2: type2, ...) => returnType`

    type MathFn = (a: number, b: number) => number;

    let op: MathFn = add;
    op = multiply;
    op = divide;

### Optional and Default Parameters

    function greet(name: string, greeting?: string): string {
        if (greeting) {
            return `${greeting}, ${name}!`;
        }
        return `Hello, ${name}!`;
    }

    greet("Alice");              // "Hello, Alice!"
    greet("Alice", "Hi");        // "Hi, Alice!"

Optional parameters are marked with `?`. They can be omitted when
calling the function.

    function greetWithDefault(name: string, greeting: string = "Hello"): string {
        return `${greeting}, ${name}!`;
    }

    greetWithDefault("Alice");           // "Hello, Alice!" — uses default
    greetWithDefault("Alice", "Hi");     // "Hi, Alice!"

Default parameters provide a value when the argument is omitted.

### Rest Parameters

    function sum(...numbers: number[]): number {
        let total = 0;
        for (const n of numbers) {
            total += n;
        }
        return total;
    }

    sum(1, 2, 3);   // 6
    sum(1, 2, 3, 4, 5);  // 15

Rest parameters collect all remaining arguments into an array. The
type is always an array type.

### Function Overloads

TypeScript supports function overloads — multiple function signatures
for the same function.

    function format(value: string): string;
    function format(value: number): string;
    function format(value: string | number): string {
        if (typeof value === "string") {
            return value.trim();
        } else {
            return value.toFixed(2);
        }
    }

    format(" hello ");   // OK — string overload
    format(3.14159);     // OK — number overload
    format(true);        // ERROR — no overload for boolean

The overloads tell the compiler which types are accepted. The
implementation signature (string | number) must be compatible with
all overload signatures.

Overloads are used for:
- Functions that accept different types and handle them differently.
- Functions that return different types based on input.
- API design where you want to be precise about what's accepted.

But overuse of overloads can make code harder to read. Often, union
types with type narrowing are simpler.

================================================================================
SECTION 5: TYPE NARROWING — REFINING TYPES IN SCOPE
================================================================================

Type narrowing is how TypeScript narrows a union type to a specific
type based on checks in the code.

### typeof Narrowing

    function process(value: string | number) {
        if (typeof value === "string") {
            // value is string here
            return value.toUpperCase();
        } else {
            // value is number here
            return value.toFixed(2);
        }
    }

`typeof` checks narrow to the type. TypeScript knows that if
`typeof value === "string"`, then `value` is a string in that branch.

### instanceof Narrowing

    class Dog { bark() { return "woof"; } }
    class Cat { meow() { return "meow"; } }

    function speak(pet: Dog | Cat) {
        if (pet instanceof Dog) {
            return pet.bark();   // pet is Dog here
        } else {
            return pet.meow();   // pet is Cat here
        }
    }

`instanceof` checks narrow to the class type. Works with classes
(but not with interfaces — interfaces have no runtime representation).

### Property Checks (Discriminated Unions)

When a union has a common property with different literal types,
TypeScript can narrow based on that property.

    interface Circle {
        kind: "circle";
        radius: number;
    }

    interface Square {
        kind: "square";
        side: number;
    }

    interface Triangle {
        kind: "triangle";
        base: number;
        height: number;
    }

    type Shape = Circle | Square | Triangle;

    function area(shape: Shape) {
        switch (shape.kind) {
            case "circle":
                return Math.PI * shape.radius ** 2;  // shape is Circle
            case "square":
                return shape.side ** 2;              // shape is Square
            case "triangle":
                return 0.5 * shape.base * shape.height;  // shape is Triangle
        }
    }

This is the discriminated union pattern. The `kind` property is the
discriminant. TypeScript narrows `shape` to the specific interface
based on the `kind` value.

This pattern is one of the most useful in TypeScript. It's used for:
- State machines (state is the discriminant).
- API responses (status is the discriminant).
- Event types (event type is the discriminant).
- Any situation where you have a union of types with a common property.

### Truthiness and Equality Narrowing

    function process(value: string | null) {
        if (value) {
            // value is string here (null is falsy, so excluded)
            return value.toUpperCase();
        }
        // value is null | "" here (empty string is falsy too)
    }

Truthiness checks narrow based on whether the value is truthy or
falsy. This is common for checking against null, undefined, or empty
strings.

Equality checks also narrow:

    function process(value: string | number) {
        if (value === "hello") {
            // value is string here (and specifically "hello")
            return value.toUpperCase();
        }
    }

### Control Flow Analysis

TypeScript analyzes the control flow of your code to narrow types.
This includes:
- If/else branches.
- Switch statements.
- Loops (for, while, do-while).
- Truthy/falsy checks.
- Early returns.

    function findUser(id: number): User | null {
        // ...
    }

    function getUserName(id: number): string {
        const user = findUser(id);
        if (!user) {
            return "unknown";
        }
        // user is User here (null was excluded by the early return)
        return user.name;
    }

TypeScript tracks the type of `user` through the function. After the
`if (!user)` block, `user` can't be null (because we returned in
that case). So `user` is narrowed to `User` for the rest of the
function.

================================================================================
SECTION 6: CLASSES IN TYPESCRIPT
================================================================================

### Class Syntax with Types

    class Person {
        name: string;        // public field — must be initialized or
                              // have a type annotation
        private age: number; // private — only accessible within the class
        readonly id: number; // can't be modified after initialization

        constructor(name: string, age: number, id: number) {
            this.name = name;
            this.age = age;
            this.id = id;
        }

        greet(): string {
            return `Hello, I'm ${this.name}`;
        }

        getAge(): number {
            return this.age;  // private field, but accessible within class
        }
    }

    let alice = new Person("Alice", 30, 1);
    alice.greet();      // "Hello, I'm Alice"
    alice.name;         // "Alice" — public field
    alice.age;          // ERROR — age is private
    alice.id = 2;       // ERROR — id is readonly

### Access Modifiers

- **public** (default): accessible everywhere.
- **private**: only accessible within the class.
- **protected**: accessible within the class and its subclasses.
- **readonly**: can only be set in the constructor (or at declaration).

TypeScript's access modifiers are compile-time only. They're erased
at runtime — JavaScript doesn't have private fields in the same way
(ES2022 added actual private fields with #, but TypeScript's private
is different).

### Parameter Properties — Shorthand

    class Person {
        constructor(
            public name: string,     // declares and initializes name
            private age: number,     // declares and initializes age
            readonly id: number      // declares and initializes id
        ) {}

        greet(): string {
            return `Hello, I'm ${this.name}`;
        }
    }

Parameter properties declare a field AND initialize it from the
constructor parameter in one step. This is idiomatic TypeScript and
reduces boilerplate.

### Abstract Classes

    abstract class Animal {
        abstract makeSound(): string;  // must be implemented by subclasses

        move(): string {
            return "moving...";  // concrete method — inherited by subclasses
        }
    }

    class Dog extends Animal {
        makeSound(): string {
            return "woof";
        }
    }

    // let animal = new Animal();  // ERROR — can't instantiate abstract class
    let dog = new Dog();
    dog.makeSound();   // "woof"
    dog.move();        // "moving..." — inherited

Abstract classes are base classes that can't be instantiated directly.
They define a common interface and may provide some implementation.
Subclasses must implement the abstract methods.

This is TypeScript's approach to inheritance. Note: TypeScript uses
structural typing (not nominal), so a class doesn't need to explicitly
extend an abstract class to satisfy its interface — it just needs to
have the right shape.

================================================================================
SECTION 7: MODULE SYSTEM
================================================================================

### ES Modules in TypeScript

TypeScript uses ES modules (import/export) for organizing code.

    // math.ts
    export function add(a: number, b: number): number {
        return a + b;
    }

    export const PI = 3.14159;

    export default function multiply(a: number, b: number): number {
        return a * b;
    }

    // main.ts
    import { add, PI } from "./math";
    import multiply from "./math";  // default import

    console.log(add(2, 3));        // 5
    console.log(PI);               // 3.14159
    console.log(multiply(2, 3));   // 6

Export styles:
- `export function ...` — named export.
- `export const ...` — named export.
- `export default ...` — default export (one per module).
- `export { ... }` — re-export.

Import styles:
- `import { ... } from ...` — named imports.
- `import ... from ...` — default import.
- `import * as name from ...` — namespace import (all exports as properties).
- `import ... from ...` with `export default` — default import.

### TypeScript's Module Resolution

When you import a module, TypeScript needs to find the corresponding
file. The module resolution strategy determines how this works.

Common strategies:
- **Node.js resolution** (most common): looks for .ts, .tsx, .d.ts,
  .js files in node_modules and relative paths.
- **Classic resolution**: older strategy, still supported.

The tsconfig.json `moduleResolution` option controls this.

### Type-only Imports and Exports

When you're importing types (not values), you can use `import type`:

    import type { Person } from "./types";
    import { Person } from "./types";   // also works — imported as value AND type

`import type` is used when you only need the type (not the value).
This is useful for:
- Avoiding runtime imports of types (types are erased at compile time).
- Making it clear that an import is only for types.
- Supporting environments where types and values are separate.

### Declaration Files (.d.ts)

Declaration files provide type information for JavaScript code. They
contain only types (no runtime code).

    // moment.d.ts (simplified)
    declare module "moment" {
        export function format(date: Date): string;
        export function parse(input: string): Date;
        // ...
    }

Declaration files are used for:
- Libraries written in JavaScript (providing types for them).
- Ambient declarations (types for things that exist at runtime but
  are not in your TypeScript code).
- Distributing types for a library (many npm packages ship with
  their own .d.ts files or have @types packages).

The `declare` keyword is used for ambient declarations — things
that exist at runtime but are declared in TypeScript for type checking.

================================================================================
SECTION 8: EVIDENCE CHECKLIST — TYPESCRIPT TYPE SYSTEM FUNDAMENTALS (L2)
================================================================================

Can you:

- [ ] Explain what TypeScript is and how it relates to JavaScript
- [ ] Explain type inference and when annotations are needed
- [ ] Explain the difference between `any` and `unknown` and when to
      use each
- [ ] Explain `void` and `never` types and when they're used
- [ ] Use primitive types: number, string, boolean, null, undefined,
      symbol, bigint
- [ ] Use union types and explain when they're useful
- [ ] Use intersection types and explain the use cases
- [ ] Use literal types and discriminated unions
- [ ] Use arrays and tuples (including labeled tuples)
- [ ] Define and use interfaces
- [ ] Explain when to use interface vs type alias
- [ ] Define and use type aliases for unions, intersections, primitives
- [ ] Write typed functions: parameters, return types, optional params,
      default params, rest params
- [ ] Use function overloads and explain when they're appropriate
- [ ] Use type narrowing: typeof, instanceof, property checks,
      truthiness, control flow analysis
- [ ] Explain discriminated unions and why they're powerful
- [ ] Use classes with access modifiers (public, private, protected,
      readonly)
- [ ] Use parameter properties in constructors
- [ ] Explain abstract classes and when to use them
- [ ] Use ES modules in TypeScript: import/export, named/default imports
- [ ] Use import type for type-only imports
- [ ] Explain declaration files (.d.ts) and when they're needed
- [ ] Use the `declare` keyword for ambient declarations
- [ ] Read and understand TypeScript error messages
- [ ] Configure tsconfig.json for a project (basic options: target,
      module, strict, outDir, rootDir)

================================================================================
SECTION 9: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand TypeScript's type system fundamentals (primitives,
union/intersection types, interfaces, functions, classes, modules), the
next topics in the TypeScript L1→L2 progression are:

1. **Generics** — generic functions, generic types, generic constraints,
   default types, variance, the relationship between generics and the
   type system.

2. **Utility Types** — Partial, Required, Pick, Omit, Record, ReturnType,
   Parameters, Extract, Exclude, NonNullable, and when to use each.

3. **Type Narrowing Deep Dive** — type predicates (custom type guards),
   discriminated unions in depth, exhaustiveness checking with never,
   narrowing in complex control flow.

4. **Advanced Types** — conditional types, mapped types, template literal
   types (basic introduction — full mastery is L3+).

5. **React + TypeScript** — typing props, state, hooks, events, generic
   components, conditional props.

6. **Module System Deep Dive** — module resolution, declaration files,
   ambient declarations, DefinitelyTyped, writing .d.ts files.

Each builds on the fundamentals. You can't use generics effectively
without understanding the type system. You can't use advanced types
without understanding conditional types and mapped types (which build
on generics and utility types).

================================================================================
END OF TYPESCRIPT FUNDAMENTALS DEEP STUDY
================================================================================
