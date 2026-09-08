# ===========================================================================
# TYPESCRIPT DEEP STUDY — GENERICS & ADVANCED TYPES
# ===========================================================================
# Date: 2026-08-19
# Status: Deep study in progress
# Prerequisites: typescript_fundamentals_deep_study.md (must understand
#                fundamentals before this)

## WHY THIS STUDY MATTERS

Generics are TypeScript's mechanism for type-parameterized code — code
that works with any type while maintaining type safety. They're the
foundation for reusable, type-safe libraries and APIs.

Advanced types (conditional types, mapped types, template literal types,
indexed access types) are the type-level programming tools that let you
transform and compute types at compile time. Mastery of these features
is what separates L2 (can use basic types) from L3 (can design type-safe
APIs and understand complex type transformations).

This targets L3 understanding: can write generic functions and types,
use all major utility types, understand conditional and mapped types,
use type narrowing effectively, use TypeScript with React, configure
TypeScript for projects.

================================================================================
SECTION 1: WHY GENERICS EXIST
================================================================================

Without generics, you have two choices when writing reusable code:

1. **Use any** — lose type safety.
   function identity(x: any): any { return x; }
   // No type information preserved — caller gets `any` back

2. **Write specific versions** — code duplication.
   function identityString(x: string): string { return x; }
   function identityNumber(x: number): number { return x; }
   function identityBoolean(x: boolean): boolean { return x; }
   // ... for every type you need

Generics solve this: write the code once, and the type is parameterized.

    function identity<T>(x: T): T { return x; }

    identity<string>("hello");   // string
    identity<number>(42);        // number
    identity("hello");           // type argument inferred: string
    identity(42);                // type argument inferred: number

The compiler generates a version of `identity` for each type you use
it with (monomorphization at the type level). The runtime code is the
same (since types are erased), but the type checking is specific to
each usage.

================================================================================
SECTION 2: GENERIC FUNCTIONS
================================================================================

### Basic Generic Function

    function first<T>(items: T[]): T | undefined {
        return items[0];
    }

    first([1, 2, 3]);           // T inferred as number → returns number | undefined
    first(["a", "b", "c"]);     // T inferred as string → returns string | undefined
    first([]);                   // T inferred as never[] → returns undefined

The type parameter `T` is inferred from the argument type. You can
also specify it explicitly: `first<string>(["a", "b"])`.

### Multiple Type Parameters

    function pair<A, B>(a: A, b: B): [A, B] {
        return [a, b];
    }

    pair(1, "hello");            // [number, string]
    pair("key", true);           // [string, boolean]

### Generic Constraints — Restricting What T Can Be

Sometimes you need T to have certain properties. Constraints express
this.

    // Without constraint — can't access .length
    function logLength<T>(item: T) {
        // console.log(item.length);  // ERROR — T might not have .length
    }

    // With constraint — T must have .length
    function logLength<T extends { length: number }>(item: T) {
        console.log(item.length);  // OK — T is known to have .length
    }

    logLength("hello");           // string has .length — OK
    logLength([1, 2, 3]);         // array has .length — OK
    logLength({ length: 5 });     // object with .length — OK
    logLength(42);                // ERROR — number doesn't have .length

The constraint `T extends { length: number }` means "T must be
assignable to a type that has a `length` property of type number."
This includes string, array, and any object with a length property.

### Constraints with Keyof

    function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
        return obj[key];
    }

    const person = { name: "Alice", age: 30, email: "alice@example.com" };
    getProperty(person, "name");   // string
    getProperty(person, "age");    // number
    getProperty(person, "email");  // string
    getProperty(person, "salary"); // ERROR — "salary" is not a key of person

`K extends keyof T` constrains K to be one of the keys of T. The
return type `T[K]` is an indexed access type — it's the type of the
property K in T. This is how you write type-safe property accessors.

### Return Type as a Generic

    function createArray<T>(length: number, value: T): T[] {
        return Array(length).fill(value);
    }

    createArray(3, "x");    // string[] — T inferred as string
    createArray(3, 0);      // number[] — T inferred as number
    createArray(3, { a: 1 });  // { a: number }[] — T inferred as object type

The return type is `T[]`, but the compiler infers T from the `value`
argument. This is a common pattern: the type parameter is inferred
from an argument, and the return type uses that type parameter.

### Generic Functions with Callbacks

    function mapArray<T, U>(arr: T[], fn: (item: T) => U): U[] {
        return arr.map(fn);
    }

    mapArray([1, 2, 3], (n) => n * 2);           // (number) => number → number[]
    mapArray(["a", "b"], (s) => s.length);       // (string) => number → number[]
    mapArray([1, 2, 3], (n) => String(n));       // (number) => string → string[]

The callback's parameter type is inferred from T, and the return type
is U. The compiler infers both T and U from the arguments.

================================================================================
SECTION 3: GENERIC TYPES
================================================================================

### Generic Interfaces

    interface Pair<T, U> {
        first: T;
        second: U;
    }

    let pair: Pair<number, string> = {
        first: 42,
        second: "hello",
    };

    // Or with type inference
    let pair2: Pair<string, boolean> = { first: "key", second: true };

### Generic Classes

    class Stack<T> {
        private items: T[] = [];

        push(item: T): void {
            this.items.push(item);
        }

        pop(): T | undefined {
            return this.items.pop();
        }

        peek(): T | undefined {
            return this.items[this.items.length - 1];
        }

        isEmpty(): boolean {
            return this.items.length === 0;
        }
    }

    let numberStack = new Stack<number>();
    numberStack.push(1);
    numberStack.push(2);
    numberStack.pop();  // number | undefined

    let stringStack = new Stack<string>();
    stringStack.push("hello");
    stringStack.push("world");

### Generic Type Aliases

    type Response<T> = {
        data: T;
        status: number;
        headers: Record<string, string>;
    };

    type UserResponse = Response<User>;
    type ProductResponse = Response<Product>;

### Default Type Parameters

Type parameters can have default values:

    function createPair<T extends string | number, U = T>(a: T, b: U): [T, U] {
        return [a, b];
    }

    createPair("hello");          // T = string, U = string (default) → [string, string]
    createPair("hello", 42);      // T = string, U = number (explicit) → [string, number]
    createPair(42);               // T = number, U = number (default) → [number, number]

Default type parameters are useful when the type parameter can be
inferred from another parameter, or when you want a sensible default.

### Generic Type Inference with Defaults

    interface ApiResponse<T = unknown> {
        data: T;
        status: number;
    }

    // Without specifying T, it defaults to unknown
    let response: ApiResponse = { data: "hello", status: 200 };
    // data is unknown — must narrow or cast to use

    // With explicit T
    let userResponse: ApiResponse<User> = { data: user, status: 200 };
    // data is User — can access User properties

The default type is used when the type parameter is not specified and
can't be inferred from context.

================================================================================
SECTION 4: VARIANCE IN TYPE PARAMETERS
================================================================================

Variance describes how subtyping relationships between types are
preserved (or not) through generic types. This is a subtle but
important concept for understanding type safety in TypeScript.

### Covariance — Preserving the Direction

A generic type is covariant in a type parameter if the subtyping
relationship is preserved:

    // If Cat extends Animal, then List<Cat> extends List<List<Animal>>?
    // NO — but for readonly collections, YES

    // ReadonlyArray is covariant in T
    let cats: readonly Cat[] = [cat1, cat2];
    let animals: readonly Animal[] = cats;  // OK — readonly array is covariant

    // Why? Because you can only READ from a readonly array. If you have
    // a readonly Cat[], you can read Cats from it. Since Cat is an Animal,
    // you can treat those reads as Animal. So readonly Cat[] is assignable
    // to readonly Animal[].

Covariance is safe for read-only types: you can treat a more specific
type as a more general type when you only read from it.

### Contravariance — Reversing the Direction

A generic type is contravariant in a type parameter if the subtyping
relationship is reversed:

    // Function parameters are contravariant
    // If Cat extends Animal, then (animal: Animal) => void is assignable
    // to (cat: Cat) => void? NO — the opposite is true.

    // A function that accepts Animal can handle Cats (because Cat is an Animal).
    // A function that accepts only Cat CANNOT handle all Animals.
    // So (animal: Animal) => void is MORE GENERAL than (cat: Cat) => void.

    // Therefore: (animal: Animal) => void is assignable to (cat: Cat) => void?
    // NO — but the other way: (cat: Cat) => void is assignable to
    // (animal: Animal) => void? NO — neither works cleanly in TypeScript
    // because TypeScript's function types are bivariant in parameters
    // (for historical reasons, though strict mode changes this).

    // In strict mode (strictFunctionTypes), function parameters are
    // contravariant:
    let dogFunc: (dog: Dog) => void = (d) => console.log(d.bark());
    let animalFunc: (animal: Animal) => void = (a) => console.log(a.toString());

    // dogFunc is NOT assignable to animalFunc (because dogFunc only handles Dogs,
    // not all Animals)
    // animalFunc IS assignable to dogFunc (because animalFunc handles all Animals,
    // including Dogs) — if strictFunctionTypes is on

In strict mode, function parameters are checked contravariantly. This
is the type-safe behavior.

### Invariance — Neither Direction

A generic type is invariant in a type parameter if neither covariance
nor contravariance holds. Mutable collections are typically invariant:

    // Mutable arrays are invariant in TypeScript
    let cats: Cat[] = [cat1, cat2];
    let animals: Animal[] = cats;  // ERROR — Cat[] is not assignable to Animal[]

    // Why? Because Cat[] is mutable. If you could assign Cat[] to Animal[],
    // you could then push a Dog into the array (thinking it's an Animal[]),
    // and then read a Dog from a Cat[] — type error!

    // Invariance prevents this: Cat[] and Animal[] are completely separate
    // types, even though Cat extends Animal.

Invariance is the safe default for mutable types. TypeScript uses
bivariance (both covariant and contravariant) for function parameters
by default (for backward compatibility), but strict mode changes this
to contravariance.

### What TypeScript Actually Does

TypeScript's variance rules (in strict mode):

- **ReadonlyArray<T>**: covariant in T
- **Array<T>**: invariant in T (mutable)
- **Function parameters**: contravariant in T (in strict mode)
- **Function return types**: covariant in T
- **Promise<T>**: covariant in T (promises are read-only — you can't
  write to a promise)
- **Map<K, V>, Set<T>**: invariant (mutable)

Understanding variance helps you design generic types that are type-safe
and flexible. If you want a generic type to be covariant, make it
read-only (use readonly modifiers). If you need mutability, accept
invariance.

================================================================================
SECTION 5: UTILITY TYPES — THE STANDARD TYPE TOOLKIT
================================================================================

TypeScript provides a set of built-in utility types that transform
existing types. These are the building blocks for type-level programming.

### Partial<T> — Make All Properties Optional

    interface Person {
        name: string;
        age: number;
        email: string;
    }

    type PartialPerson = Partial<Person>;
    // = { name?: string; age?: number; email?: string; }

    // Use case: update functions
    function updatePerson(id: number, updates: Partial<Person>) {
        // updates can have any subset of Person's properties
    }

    updatePerson(1, { name: "Alice Smith" });  // OK — only updating name
    updatePerson(1, { age: 31, email: "new@example.com" });  // OK

Partial is essential for update/patch functions where you don't need
to provide all fields.

### Required<T> — Make All Properties Required

    interface Person {
        name: string;
        age?: number;
        email?: string;
    }

    type RequiredPerson = Required<Person>;
    // = { name: string; age: number; email: string; }

Use case: when you need to ensure all fields are present (e.g., for
validation after partial updates).

### Readonly<T> — Make All Properties Readonly

    interface Person {
        name: string;
        age: number;
    }

    type ReadonlyPerson = Readonly<Person>;
    // = { readonly name: string; readonly age: number; }

    let p: ReadonlyPerson = { name: "Alice", age: 30 };
    p.name = "Bob";  // ERROR — name is readonly

Use case: representing immutable data, returning data that shouldn't
be modified by the caller.

### Pick<T, K> — Select Specific Properties

    interface Person {
        name: string;
        age: number;
        email: string;
        address: string;
    }

    type PersonNameAndAge = Pick<Person, "name" | "age">;
    // = { name: string; age: number; }

    let p: PersonNameAndAge = { name: "Alice", age: 30 };

Use case: creating types with a subset of properties. Common for API
responses where you only need certain fields.

### Omit<T, K> — Remove Specific Properties

    interface Person {
        name: string;
        age: number;
        email: string;
        password: string;  // sensitive — shouldn't be in public responses
    }

    type PublicPerson = Omit<Person, "password">;
    // = { name: string; age: number; email: string; }

    let p: PublicPerson = { name: "Alice", age: 30, email: "alice@example.com" };

Use case: removing sensitive or internal properties from types used
in public APIs.

### Record<K, V> — Object with Specific Key/Value Types

    type StringRecord = Record<string, number>;
    // = { [key: string]: number; }

    let scores: StringRecord = { Alice: 95, Bob: 87, Charlie: 92 };

    type Role = "admin" | "user" | "guest";
    type Permissions = Record<Role, boolean>;
    // = { admin: boolean; user: boolean; guest: boolean; }

    let perms: Permissions = {
        admin: true,
        user: true,
        guest: false,
    };

Use case: creating object types with specific key and value types.
Common for configuration objects, lookup tables, permission maps.

### ReturnType<T> — Extract the Return Type of a Function

    function getUser(): { id: number; name: string; email: string } {
        // ...
    }

    type User = ReturnType<typeof getUser>;
    // = { id: number; name: string; email: string; }

Use case: avoiding duplicating type definitions. When a function
returns a specific type, you can extract that type without defining
it separately.

### Parameters<T> — Extract the Parameter Types of a Function

    function createUser(name: string, age: number, email: string) {
        // ...
    }

    type CreateUserParams = Parameters<typeof createUser>;
    // = [string, number, string]

    // Use with destructuring
    function wrapCreateUser(...args: CreateUserParams) {
        // args has the same type as createUser's parameters
        return createUser(...args);
    }

Use case: wrapping functions while preserving their parameter types,
creating higher-order functions.

### ConstructorParameters<T> — Extract Constructor Parameter Types

    class Person {
        constructor(public name: string, public age: number) {}
    }

    type PersonParams = ConstructorParameters<typeof Person>;
    // = [string, number]

    function createPerson(...args: PersonParams): Person {
        return new Person(...args);
    }

Use case: factory functions that mirror a class's constructor.

### Extract<T, U> — Extract Types from a Union That Are Assignable to U

    type T = string | number | boolean;
    type StringOrNumber = Extract<T, string | number>;
    // = string | number

    type OnlyStrings = Extract<T, string>;
    // = string

Use case: filtering a union type to only include certain types.

    // With discriminated unions
    type Event = MouseEvent | KeyboardEvent | TouchEvent;
    type PointerEvents = Extract<Event, { pointerType: string }>;

Use case: extracting specific variants from a union.

### Exclude<T, U> — Exclude Types from a Union That Are Assignable to U

    type T = string | number | boolean;
    type WithoutNumber = Exclude<T, number>;
    // = string | boolean

    type OnlyStrings = Exclude<T, string | number | boolean>;
    // = never

Use case: the inverse of Extract — removing certain types from a union.

### NonNullable<T> — Exclude null and undefined

    type T = string | number | null | undefined;
    type NonNullableT = NonNullable<T>;
    // = string | number

    // Common use case with filter
    const items: (string | null | undefined)[] = ["a", null, "b", undefined, "c"];
    const filtered = items.filter((item): item is NonNullable<typeof item> => {
        return item != null;
    });
    // filtered is string[]

Use case: cleaning up unions by removing null and undefined.

### Uppercase, Lowercase, Capitalize, Uncapitalize (TS 4.1+)

    type T = "hello" | "world";
    type U = Uppercase<T>;     // = "HELLO" | "WORLD"
    type L = Lowercase<T>;     // = "hello" | "world"
    type C = Capitalize<T>;    // = "Hello" | "World"
    type Unc = Uncapitalize<T>;  // = "hello" | "world"

These transform string literal types. Use case: generating event names,
CSS class names, API endpoint names from a base set of strings.

    type EventNames = "click" | "scroll" | "hover";
    type ListenerProps = {
        [K in EventNames as `on${Capitalize<K>}`]: () => void;
    };
    // = { onClick: () => void; onScroll: () => void; onHover: () => void; }

Combining with template literal types (next section) creates powerful
patterns.

### Awaited<T> (TS 4.5+) — Unwrap Promise Types

    type T = Promise<string>;
    type Unwrapped = Awaited<T>;  // = string

    type T2 = Promise<Promise<number>>;
    type Unwrapped2 = Awaited<T2>;  // = number — recursively unwraps

    // Use with ReturnType to get the resolved type of an async function
    async function fetchUser(): Promise<User> {
        // ...
    }

    type User = Awaited<ReturnType<typeof fetchUser>>;
    // = User — the type the promise resolves to

Use case: working with async functions and extracting the resolved
type without manually unwrapping Promise.

### Satisfies Operator (TS 4.9+) — Type Checking Without Widening

The `satisfies` operator checks that a value matches a type WITHOUT
changing the inferred type of the value.

    // Without satisfies — type is widened to string
    const palette1 = {
        red: "#ff0000",
        green: "#00ff00",
        blue: "#0000ff",
    };
    // palette1.red is string — you can assign anything to it

    // With satisfies — type is the specific literal
    const palette2 = {
        red: "#ff0000",
        green: "#00ff00",
        blue: "#0000ff",
    } satisfies Record<string, string>;
    // palette2.red is "#ff0000" — the literal type is preserved

This is useful when you want to validate that a value matches a type
but keep the specific literal types for better inference downstream.

================================================================================
SECTION 6: CONDITIONAL TYPES — TYPES THAT COMPUTE
================================================================================

Conditional types are the ternary operator of the type system:

    T extends U ? X : Y

"If T is assignable to U, then the type is X. Otherwise, the type is Y."

### Basic Conditional Types

    type IsString<T> = T extends string ? "yes" : "no";

    type A = IsString<string>;   // "yes"
    type B = IsString<number>;   // "no"
    type C = IsString<string | number>;  // "yes" | "no" — distributive

### Distributive Conditional Types

When T is a union type, conditional types distribute over each member
of the union:

    type ToArray<T> = T extends any ? T[] : never;

    type A = ToArray<string>;        // string[]
    type B = ToArray<string | number>;  // string[] | number[]

    // This is distributive — it's equivalent to:
    // ToArray<string> | ToArray<number>
    // = string[] | number[]

Distributive conditional types are powerful but can be surprising.
To prevent distribution, wrap the type parameter in a tuple:

    type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;
    type B = ToArrayNonDist<string | number>;  // (string | number)[]

Now the union is not distributed — the conditional treats the whole
union as a single type.

### The infer Keyword — Extracting Types from Other Types

`infer` allows you to declare a type variable inside a conditional
type and extract it from the checked type.

    // Extract the return type of a function
    type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

    function add(a: number, b: number): number { return a + b; }
    type R = ReturnType<typeof add>;  // number

    // Extract the element type of an array
    type ElementType<T> = T extends (infer E)[] ? E : never;

    type E = ElementType<string[]>;  // string

    // Extract the resolved type of a Promise
    type Awaited<T> = T extends Promise<infer R> ? R : T;

    type A = Awaited<Promise<string>>;  // string

`infer` is used in many of TypeScript's built-in utility types. It's
the mechanism for extracting type information from complex types.

### Using infer in Practice

    // Extract the props type of a React component
    type ComponentProps<T> = T extends React.ComponentType<infer P> ? P : never;

    // Extract the element type of a React forwardRef component
    type ForwardRefProps<T> = T extends React.ForwardRefExoticComponent<
        infer P, React.Ref<any>
    > ? P : never;

    // Get the API response type from a fetch function
    type ApiResponse<T> = T extends (...args: any[]) => Promise<infer R> ? R : never;

These patterns are common in TypeScript libraries and frameworks.

### Conditional Types with Multiple Branches

You can nest conditional types for multiple branches:

    type TypeName<T> = T extends string ? "string" :
                        T extends number ? "number" :
                        T extends boolean ? "boolean" :
                        T extends undefined ? "undefined" :
                        T extends null ? "null" :
                        T extends Function ? "function" :
                        "object";

    type N = TypeName<string>;     // "string"
    type M = TypeName<number>;     // "number"
    type O = TypeName<{ a: 1 }>;   // "object"

But deeply nested conditionals can be hard to read. For complex type
logic, consider using mapped types or utility types instead.

================================================================================
SECTION 7: MAPPED TYPES — TRANSFORMING PROPERTIES
================================================================================

Mapped types create new types by transforming the properties of an
existing type.

### Basic Mapped Type

    interface Person {
        name: string;
        age: number;
        email: string;
    }

    // Make all properties optional
    type PartialPerson = {
        [K in keyof Person]?: Person[K];
    };
    // = { name?: string; age?: number; email?: string; }

    // Make all properties readonly
    type ReadonlyPerson = {
        readonly [K in keyof Person]: Person[K];
    };
    // = { readonly name: string; readonly age: number; readonly email: string; }

    // Make all properties required
    type RequiredPerson = {
        [K in keyof Person]-?: Person[K];
    };
    // = { name: string; age: number; email: string; }

The `-?` modifier removes the optional modifier. The `+` modifier
adds it (default). The `readonly` modifier adds readonly, `-readonly`
removes it.

### Key Remapping (TS 4.1+)

You can remap keys in a mapped type using `as`:

    type Person = {
        name: string;
        age: number;
    };

    // Add "get" prefix to each property, making them functions
    type Getters = {
        [K in keyof Person as `get${Capitalize<K>}`]: () => Person[K];
    };
    // = { getName: () => string; getAge: () => number; }

    // Filter out specific keys
    type WithoutEmail = {
        [K in keyof Person as Exclude<K, "email">]: Person[K];
    };
    // = { name: string; age: number; }

Key remapping combined with template literal types enables powerful
type transformations. This is how libraries generate getter/setter
types, event handler types, etc.

### Mapped Types with Template Literal Types

    type EventNames = "click" | "scroll" | "hover";

    // Create event handler types
    type EventHandlers = {
        [K in EventNames as `on${Capitalize<K>}`]: (event: K) => void;
    };
    // = {
    //     onClick: (event: "click") => void;
    //     onScroll: (event: "scroll") => void;
    //     onHover: (event: "hover") => void;
    // }

This pattern is used extensively in UI libraries for generating event
handler props from a list of event names.

### Practical Example — API Client Types

    // Define API endpoints
    type Endpoints = {
        getUser: { params: { id: number }; response: User };
        createUser: { params: { name: string; email: string }; response: User };
        deleteUser: { params: { id: number }; response: { success: boolean } };
    };

    // Generate typed request and response types
    type Requests = {
        [K in keyof Endpoints]: Endpoints[K]["params"];
    };
    // = { getUser: { id: number }; createUser: { name: string; email: string };
    //      deleteUser: { id: number } }

    type Responses = {
        [K in keyof Endpoints]: Endpoints[K]["response"];
    };
    // = { getUser: User; createUser: User; deleteUser: { success: boolean } }

    // Generate a typed API client function
    function createApiClient<E extends Record<string, any>>(
        endpoints: E
    ) {
        return function request<K extends keyof E>(
            endpoint: K,
            params: E[K]["params"]
        ): Promise<E[K]["response"]> {
            // Implementation here
            return Promise.resolve(undefined as any);
        };
    }

    const api = createApiClient({
        getUser: { params: { id: 0 }, response: null as any },
        // ...
    });

    api("getUser", { id: 42 });  // Promise<User> — fully typed!

This is the kind of type-level programming that makes TypeScript powerful
for building type-safe APIs.

================================================================================
SECTION 8: TEMPLATE LITERAL TYPES (TS 4.1+)
================================================================================

Template literal types use JavaScript template literal syntax at the
type level to create new string literal types.

### Basic Template Literal Types

    type Color = "red" | "green" | "blue";
    type Padding = "none" | "small" | "medium" | "large";

    type Style = `${Color}-${Padding}`;
    // = "red-none" | "red-small" | "red-medium" | "red-large" |
    //   "green-none" | "green-small" | ... |
    //   "blue-large"

The compiler generates all combinations of the string literals. This
is useful for creating type-safe CSS class names, API endpoint names,
event names, etc.

### Dynamic Template Literal Types

    type EventName = "click" | "scroll" | "hover";
    type Listener = `on${Capitalize<EventName>}`;
    // = "onClick" | "onScroll" | "onHover"

    type Direction = "north" | "south" | "east" | "west";
    type Opposite = `${"south" extends Direction ? "north" : "south"}`;
    // This doesn't work — conditional types in template literals need
    // different handling

### Inferring from Template Literal Types

You can use `infer` in template literal types to extract parts of a
string:

    // Extract the event name from an event handler name
    type EventHandlerName<T extends string> = T extends `on${infer E}`
        ? Uncapitalize<E>
        : never;

    type E = EventHandlerName<"onClick">;  // "click"
    type E2 = EventHandlerName<"onScroll">;  // "scroll"

This pattern is useful for converting between naming conventions
(event handler names to event names).

### Practical Use — CSS Class Generation

    type Color = "red" | "blue" | "green";
    type Size = "sm" | "md" | "lg";

    // Generate all possible button class combinations
    type ButtonClass = `btn-${Color}-${Size}`;
    // = "btn-red-sm" | "btn-red-md" | "btn-red-lg" |
    //   "btn-blue-sm" | ... | "btn-green-lg"

    function setButtonClass(className: ButtonClass) {
        // Only accepts valid button class names
    }

    setButtonClass("btn-red-lg");  // OK
    setButtonClass("btn-purple-sm");  // ERROR — not a valid combination

Template literal types provide type-safe string generation. Combined
with mapped types and key remapping, they enable powerful type-level
APIs.

================================================================================
SECTION 9: INDEXED ACCESS TYPES
================================================================================

Indexed access types let you look up the type of a specific property
in a type.

### Basic Indexed Access

    interface Person {
        name: string;
        age: number;
        email: string;
    }

    type PersonName = Person["name"];    // string
    type PersonAge = Person["age"];      // number
    type PersonContact = Person["email"]; // string

    // Multiple properties at once
    type PersonInfo = Person["name" | "age"];  // string | number
    type AllProperties = Person[keyof Person];  // string | number

### Using with Generics and keyof

    function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
        return obj[key];
    }

    let person: Person = { name: "Alice", age: 30, email: "alice@example.com" };
    getProperty(person, "name");   // string — T[K] where T=Person, K="name"
    getProperty(person, "age");    // number — T[K] where T=Person, K="age"

The return type `T[K]` is an indexed access type — it's the type of
the property K in T. This is how you write type-safe property accessors.

### Nested Indexed Access

    interface ApiResponse {
        data: {
            user: {
                id: number;
                name: string;
            };
            timestamp: number;
        };
        status: number;
    }

    type User = ApiResponse["data"]["user"];  // { id: number; name: string; }
    type UserId = ApiResponse["data"]["user"]["id"];  // number

You can chain indexed access types to drill into nested structures.

### Dynamic Property Access

    type Keys = "name" | "age";
    type Values = Person[Keys];  // string | number

You can use a union of keys to get a union of the corresponding types.

### Combining with Mapped Types

    type LazyGetters<T> = {
        [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
    };

    type PersonGetters = LazyGetters<Person>;
    // = { getName: () => string; getAge: () => number; getEmail: () => string; }

Indexed access types with mapped types and key remapping enable
transforming entire object structures at the type level.

================================================================================
SECTION 10: TYPE GUARDS AND TYPE PREDICATES
================================================================================

Type guards are functions that narrow types based on custom logic.

### Type Predicates

A type predicate is a function return type of the form `parameterName
is Type`.

    function isString(value: unknown): value is string {
        return typeof value === "string";
    }

    function isNumber(value: unknown): value is number {
        return typeof value === "number";
    }

    function processValue(value: unknown) {
        if (isString(value)) {
            // value is string here
            return value.toUpperCase();
        }
        if (isNumber(value)) {
            // value is number here
            return value.toFixed(2);
        }
        // value is still unknown here
    }

Type predicates tell the compiler that the function checks for a
specific type. The compiler trusts the type predicate and narrows
the type accordingly.

### Custom Type Guards for Complex Types

    interface Dog {
        kind: "dog";
        bark(): string;
    }

    interface Cat {
        kind: "cat";
        meow(): string;
    }

    function isDog(pet: Dog | Cat): pet is Dog {
        return (pet as Dog).kind === "dog";
    }

    function processPet(pet: Dog | Cat) {
        if (isDog(pet)) {
            pet.bark();  // OK — pet is narrowed to Dog
        } else {
            pet.meow();  // OK — pet is Cat (else branch)
        }
    }

Custom type guards are useful for complex type checks that can't be
done with simple typeof or instanceof.

### Assertive Type Guards

An assertive type guard throws if the value is not the expected type.

    function assertString(value: unknown): asserts value is string {
        if (typeof value !== "string") {
            throw new Error(`Expected string, got ${typeof value}`);
        }
    }

    function process(value: unknown) {
        assertString(value);
        // value is string here (compiler trusts the assertion)
        return value.toUpperCase();
    }

Assertive type guards are useful when you need to ensure a value is
of a certain type before proceeding, and you want to throw if it's
not.

### Narrowing with Discriminated Unions

Discriminated unions are the most common pattern for type-safe unions
in TypeScript. The discriminant is a common property with literal
types.

    interface Success {
        status: "success";
        data: string;
    }

    interface Error {
        status: "error";
        message: string;
    }

    interface Loading {
        status: "loading";
    }

    type State = Success | Error | Loading;

    function handleState(state: State) {
        switch (state.status) {
            case "success":
                return state.data;  // state is Success
            case "error":
                return state.message;  // state is Error
            case "loading":
                return "loading...";  // state is Loading
        }
    }

TypeScript narrows the type based on the discriminant property. This
is the recommended pattern for unions in TypeScript.

================================================================================
SECTION 11: EVIDENCE CHECKLIST — TYPESCRIPT GENERICS & ADVANCED TYPES (L3)
================================================================================

Can you:

- [ ] Write generic functions with type parameters and constraints
- [ ] Write generic interfaces and classes
- [ ] Use default type parameters
- [ ] Explain variance (covariance, contravariance, invariance) and
      when each applies in TypeScript
- [ ] Use all major utility types: Partial, Required, Readonly, Pick,
      Omit, Record, ReturnType, Parameters, ConstructorParameters,
      Extract, Exclude, NonNullable, Uppercase/Lowercase/Capitalize/
      Uncapitalize, Awaited
- [ ] Use the satisfies operator for type checking without widening
- [ ] Write and use conditional types: T extends U ? X : Y
- [ ] Understand distributive conditional types and how to prevent
      distribution with tuple wrapping
- [ ] Use infer to extract types from functions, arrays, promises, etc.
- [ ] Write mapped types with key remapping (as clause)
- [ ] Use template literal types for string type transformations
- [ ] Use indexed access types (T[K]) for property lookups
- [ ] Combine mapped types, key remapping, template literal types, and
      indexed access types for complex type transformations
- [ ] Write type predicates (custom type guards)
- [ ] Write assertive type guards (asserts x is T)
- [ ] Explain and use discriminated unions for type-safe unions
- [ ] Use Exclude<keyof T, K> for filtering out keys in mapped types
- [ ] Explain when to use generics vs union types vs type assertions

================================================================================
SECTION 12: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand TypeScript's generics and advanced types, the
next topics for L3 mastery are:

1. **React + TypeScript** — typing props, state, hooks, events,
   generic components, conditional props, forwardRef, context.

2. **Module System Deep Dive** — module resolution strategies, path
   mappings, declaration files, writing .d.ts files, ambient
   declarations, DefinitelyTyped conventions.

3. **Type-Safe Library Design** — designing APIs that prevent misuse
   at compile time, making illegal states unrepresentable, using
   branded types for additional type safety.

4. **Monorepo TypeScript** — project references, composite projects,
   incremental builds, shared type configurations across packages.

5. **TypeScript Compiler API** — reading and understanding the
   compiler's type checker, writing custom transformers, generating
   types programmatically.

Generics and advanced types are the toolset for type-level programming
in TypeScript. Mastery means you can design APIs that are both flexible
and type-safe, catching errors at compile time that would otherwise
only appear at runtime.

================================================================================
END OF TYPESCRIPT GENERICS & ADVANCED TYPES DEEP STUDY
================================================================================
