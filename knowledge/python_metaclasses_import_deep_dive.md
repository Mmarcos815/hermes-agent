# ===========================================================================
# PYTHON METACLASSES & THE IMPORT SYSTEM — L5 DEEP DIVE
# ===========================================================================
# Part 3 of Python L4→L5 deep dive
# Date: 2026-08-19
# Status: In progress
# Companions: python_descriptor_deep_dive.md (Part 1),
#             python_cpython_source_analysis.md (Part 2)

## WHY THIS MATTERS

Metaclasses are the "secret sauce" of advanced Python. They're how
you customize class creation itself — not just individual objects.
The import system is how Python finds and loads modules — it's the
foundation for everything from pip install to plugin systems to
custom package formats.

Understanding metaclasses at L5 means: you understand type as a
metaclass, you can create custom metaclasses, you understand
__init_subclass__ and __set_name__, and you know when metaclasses
are the right tool vs. when they're overkill.

Understanding the import system at L5 means: you understand the
full chain from `import X` to module execution, you can customize
import behavior (import hooks, finders, loaders), and you can read
the CPython import implementation.

================================================================================
SECTION 1: METACLASSES — CLASSES THAT CREATE CLASSES
================================================================================

### What a Metaclass Is

A metaclass is a class whose instances are classes. Just as a regular
class defines the behavior of its instances (objects), a metaclass
defines the behavior of its instances (classes).

    # Regular class → instances are objects
    class Dog:
        def bark(self):
            return "woof"

    dog = Dog()  # dog is an instance of Dog
    type(dog)    # <class '__main__.Dog'>

    # Metaclass → instances are classes
    class Meta(type):
        def __new__(mcs, name, bases, namespace):
            # Called when a class using this metaclass is CREATED
            print(f"Creating class {name}")
            return super().__new__(mcs, name, bases, namespace)

    class Dog(metaclass=Meta):
        def bark(self):
            return "woof"
    # Output: "Creating class Dog"

    # Dog is an instance of Meta
    type(Dog)    # <class '__main__.Meta'>
    isinstance(Dog, Meta)  # True

The default metaclass is `type`. Every class in Python is an instance
of type (unless you specify a different metaclass).

    class Dog:
        pass

    type(Dog)      # <class 'type'>
    isinstance(Dog, type)  # True

So `type` is the metaclass that creates all classes by default.
When you write `class Dog: ...`, Python calls `type.__new__(type,
'Dog', (), {...})` to create the Dog class.

### The Metaclass Lifecycle

When Python creates a class, it goes through these steps:

1. **Collect the namespace**: Python executes the class body in a new
   namespace (a dict). All the statements in the class body run, and
   their results are stored in the namespace.

2. **Determine the metaclass**: Python determines which metaclass to
   use. The metaclass is:
   - The `metaclass` keyword argument if specified: `class Foo(metaclass=Meta)`
   - Otherwise, the most derived metaclass of the base classes
   - Otherwise, `type` (the default)

3. **Call the metaclass's __new__**: `Meta.__new__(Meta, name, bases,
   namespace)` creates the class object. This is where you can modify
   the namespace, add/remove methods, validate the class, etc.

4. **Call the metaclass's __init__**: `Meta.__init__(cls, name, bases,
   namespace)` initializes the class. This is less commonly overridden
   — __new__ is where the class is created, __init__ is where it's
   initialized.

5. **Make the class available**: The class object is bound to the name
   in the enclosing scope.

### __new__ vs __init__ in Metaclasses

    class Meta(type):
        def __new__(mcs, name, bases, namespace):
            # Called BEFORE the class is created
            # Can modify namespace, add/remove attributes
            # Must return the new class object
            if not any(b for b in bases if issubclass(b, SomeBase)):
                raise TypeError("Must inherit from SomeBase")
            namespace['added_by_meta'] = True
            return super().__new__(mcs, name, bases, namespace)

        def __init__(cls, name, bases, namespace):
            # Called AFTER the class is created
            # Can't modify the class structure (it's already created)
            # Can do initialization, registration, etc.
            print(f"Class {name} created")
            super().__init__(name, bases, namespace)

__new__ is where you CREATE the class. You can modify the namespace
before the class is created. You MUST return the new class object.

__init__ is where you INITIALIZE the class. The class already exists.
You can do registration, logging, validation that doesn't affect the
class structure.

In practice, most metaclasses override __new__ (or use __init_subclass__
instead — more on that later).

### How type Works as a Metaclass

Let's look at what `type` does when you write `class Foo:

    Foo = type('Foo', (), {
        'x': 42,
        'method': lambda self: self.x,
    })

This is equivalent to:

    class Foo:
        x = 42
        def method(self):
            return self.x

`type(name, bases, namespace)` is the constructor for classes. It
creates a new class object. The parameters:
- `name`: the name of the class (string)
- `bases`: a tuple of base classes
- `namespace`: a dict of attributes (methods, class variables, etc.)

So `type` is both:
1. A function that returns the type of an object: `type(obj)`
2. A constructor that creates new classes: `type(name, bases, dict)`

When you use `type` as a constructor, you're using it as a metaclass.
Every class created with `class` is created by calling `type` (or a
custom metaclass) under the hood.

### Custom Metaclasses — Practical Examples

**Automatic registration**:

    registry = {}

    class RegisterMeta(type):
        def __new__(mcs, name, bases, namespace):
            cls = super().__new__(mcs, name, bases, namespace)
            if name != 'Base':  # don't register the base class
                registry[name] = cls
            return cls

    class Plugin(metaclass=RegisterMeta):
        pass

    class EmailPlugin(Plugin):
        pass

    class SmsPlugin(Plugin):
        pass

    # After class definitions, registry contains:
    # {'EmailPlugin': <class 'EmailPlugin'>, 'SmsPlugin': <class 'SmsPlugin'>}

This is how plugin systems work — metaclasses automatically register
subclasses when they're defined.

**Automatic field collection (like dataclasses or ORMs)**:

    class ModelMeta(type):
        def __new__(mcs, name, bases, namespace):
            fields = {}
            for key, value in namespace.items():
                if isinstance(value, Field):
                    fields[key] = value
            namespace['_fields'] = fields
            return super().__new__(mcs, name, bases, namespace)

    class Model(metaclass=ModelMeta):
        _fields: dict

    class User(Model):
        name = Field(String())
        email = Field(String())
        age = Field(Integer())

    # User._fields = {'name': Field(String()), 'email': Field(String()),
    #                 'age': Field(Integer())}

This is similar to how ORMs (SQLAlchemy, Django) and dataclasses
work — they use metaclasses to collect field definitions at class
creation time.

**Validation and enforcement**:

    class FinalMeta(type):
        def __new__(mcs, name, bases, namespace):
            for base in bases:
                if isinstance(base, FinalMeta):
                    raise TypeError(f"Class {base.__name__} is final and cannot be subclassed")
            return super().__new__(mcs, name, bases, namespace)

    class Final(metaclass=FinalMeta):
        pass

    class MyFinal(Final):
        pass

    class TrySubclass(MyFinal):  # TypeError: MyFinal is final and cannot be subclassed
        pass

This is how you enforce "final" classes in Python — the metaclass
checks if any base is a Final class and raises if so.

### __init_subclass__ — The Modern Alternative to Metaclasses

PEPs 487 introduced `__init_subclass__`, which is a simpler way to
customize class creation without full metaclasses.

    class Plugin:
        _plugins = {}

        def __init_subclass__(cls, plugin_name: str, **kwargs):
            super().__init_subclass__(**kwargs)
            Plugin._plugins[plugin_name] = cls

    class EmailPlugin(Plugin, plugin_name="email"):
        pass

    class SmsPlugin(Plugin, plugin_name="sms"):
        pass

    # Plugin._plugins = {'email': <class 'EmailPlugin'>, 'sms': <class 'SmsPlugin'>}

`__init_subclass__` is called when a subclass is created. It's a hook
on the PARENT class, not a metaclass. This is simpler than metaclasses
for many use cases:

- No metaclass conflicts (more on this later)
- Easier to understand and reason about
- Works with multiple inheritance naturally

`__init_subclass__` is called AFTER the class is created (unlike
metaclass `__new__` which is called BEFORE). So you can't modify the
class namespace — but you can register the class, validate it, etc.

### When to Use Metaclasses vs __init_subclass__

**Use metaclasses when:**
- You need to modify the class namespace before the class is created
  (adding/removing methods, modifying attributes)
- You need to control the class creation process itself
- You're building a framework that needs deep class customization
  (ORMs, plugin systems with complex registration, API generators)

**Use __init_subclass__ when:**
- You need to hook when subclasses are created (registration, validation)
- You don't need to modify the class structure
- You want to avoid metaclass complexity

**Use neither when:**
- A class decorator will do the job (for simple modifications)
- You just need to validate instances (use __init__ or __post_init__
  with dataclasses)

### Metaclass Conflicts

When two base classes have different metaclasses, Python must resolve
which metaclass to use for the derived class. The rule:

    class MetaA(type): pass
    class MetaB(type): pass

    class A(metaclass=MetaA): pass
    class B(metaclass=MetaB): pass

    class C(A, B): pass  # TypeError: metaclass conflict

Python will only create C if there's a single metaclass that's a
subclass of all the base metaclasses. If MetaA and MetaB are unrelated,
there's no common metaclass → conflict.

To resolve:

    class MetaC(MetaA, MetaB): pass  # MetaC inherits from both

    class C(A, B, metaclass=MetaC): pass  # OK — MetaC is a subclass of both

Or:

    class MetaA(type): pass
    class MetaB(MetaA): pass  # MetaB inherits from MetaA

    class A(metaclass=MetaA): pass
    class B(metaclass=MetaB): pass

    class C(A, B): pass  # OK — MetaB is a subclass of MetaA, so MetaB is used

Metaclass conflicts are a source of complexity. This is one reason
to prefer __init_subclass__ when possible — it avoids metaclass
conflicts entirely.

### __set_name__ — PEP 487

When a descriptor is assigned to a class attribute, Python calls
`__set_name__` on the descriptor to tell it what attribute name it
was assigned to.

    class MyDescriptor:
        def __set_name__(self, owner, name):
            self.name = name
            print(f"Descriptor assigned to {owner.__name__}.{name}")

        def __get__(self, instance, owner):
            if instance is None:
                return self
            return instance.__dict__.get(self.name)

    class MyClass:
        attr = MyDescriptor()  # prints: "Descriptor assigned to MyClass.attr"

This is called automatically during class creation, for every
descriptor in the class namespace.

`__set_name__` enables descriptors to know their own name without
requiring it to be passed explicitly. This is how dataclasses, attrs,
and other libraries automatically detect field names.

================================================================================
SECTION 2: THE IMPORT SYSTEM — HOW PYTHON FINDS AND LOADS MODULES
================================================================================

### What the Import System Does

When you write `import X` or `from X import Y`, Python goes through
a multi-step process to find and load the module:

1. **Check sys.modules**: Is the module already imported? If yes, return
   it. This is the module cache — each module is only imported once
   (unless you reload it).

2. **Find the module**: Use the import machinery (finders) to locate
   the module on disk or in memory.

3. **Load the module**: Use a loader to execute the module code and
   create the module object.

4. **Cache and return**: Store the module in sys.modules and return it.

### The Import Machinery: Finders and Loaders

The import system is based on two concepts:

- **Finder**: Given a module name, finds the module and returns a
  loader (or None if it can't find it).
- **Loader**: Given a module name and a location, loads the module
  (executes the code and creates the module object).

Finders and loaders are objects with specific methods:

    class Finder:
        def find_spec(self, fullname, path, target=None):
            # Returns a ModuleSpec if the module can be found, or None
            ...

    class Loader:
        def create_module(self, spec):
            # Returns the module object (or None for default)
            ...
        def exec_module(self, module):
            # Executes the module code
            ...

The finder finds the module, creates a ModuleSpec (which describes
how to load it), and returns it. The import machinery then uses the
loader from the spec to create and execute the module.

### How import Works Step by Step

1. `import mymodule` is executed.

2. Python checks `sys.modules['mymodule']`. If it's there, return it.

3. If not, Python calls `_find_and_load('mymodule')`:

   a. **Find phase**: Python calls `sys.meta_path` (a list of finders)
      to find the module. Each finder's `find_spec` is called until one
      returns a spec.

      - First, check `sys.path_hooks` for path-based finders (for
        modules in sys.path).
      - Then, check `sys.meta_path` for other finders (for built-in
        modules, frozen modules, etc.).

   b. **Load phase**: Once a spec is found, the loader's `create_module`
      and `exec_module` are called.

      - `create_module`: creates the module object (or returns None for
        the default module creation).
      - `exec_module`: executes the module code in the module's namespace.

   c. The module is added to `sys.modules` and returned.

### sys.meta_path — The List of Finders

`sys.meta_path` is a list of finders that Python consults when
importing a module. The default finders are (in order):

1. **BuiltinImporter**: finds built-in modules (like `sys`, `math` —
   modules compiled into the Python interpreter).

2. **FrozenImporter**: finds frozen modules (modules compiled into
   Python bytecode and embedded in the interpreter).

3. **PathFinder**: finds modules on the filesystem (searches sys.path).

    import sys
    for finder in sys.meta_path:
        print(finder)

Custom finders can be added to sys.meta_path to implement custom
import behavior (e.g., importing from a database, a network, a
custom format).

### sys.path — Where Modules Are Searched

`sys.path` is a list of directory names that PathFinder searches for
modules. It includes:
- The directory containing the script being run (or the current
  directory if no script).
- PYTHONPATH environment variable entries.
- Site-packages directories (where pip installs packages).

    import sys
    print(sys.path)
    # ['/current/dir', '/usr/lib/python3.11', '/usr/lib/python3.11/lib-dynload',
    #  '/usr/local/lib/python3.11/site-packages', ...]

When you `import mypackage.mymodule`, PathFinder:
1. Looks for `mymodule.py` in each directory in sys.path.
2. Or looks for `mymodule/__init__.py` (a package).
3. For subpackages: `mypackage/subpackage/module.py` or
   `mypackage/subpackage/__init__.py`.

### Package Imports and __init__.py

A package is a directory with an `__init__.py` file. The `__init__.py`
is executed when the package is imported.

    mypackage/
        __init__.py
        module1.py
        module2.py
        subpackage/
            __init__.py
            module3.py

    import mypackage          # executes mypackage/__init__.py
    import mypackage.module1 # executes mypackage/module1.py
    import mypackage.subpackage.module3  # executes both __init__.py files and module3.py

The `__init__.py` can:
- Export symbols from submodules (`from .module1 import something`).
- Define package-level variables.
- Run package initialization code.

Namespace packages (PEP 420) don't require `__init__.py` — they're
formed by multiple directories with the same name spread across
sys.path. This is used for splitting a package across multiple
distributions.

### Relative Imports

Within a package, you can use relative imports:

    # In mypackage/module1.py
    from .module2 import something       # import from mypackage.module2
    from ..subpackage.module3 import other  # import from mypackage.subpackage.module3
    from . import submodule               # import mypackage.submodule

Relative imports use dots:
- `.` = current package
- `..` = parent package
- `...` = grandparent package

Relative imports only work within packages. They don't work in
top-level scripts (modules run as `__main__`).

### Import Hooks — Customizing the Import System

You can customize the import system by adding finders and loaders to
`sys.meta_path` or `sys.path_hooks`.

    import sys
    from importlib.abc import MetaPathFinder, Loader
    from importlib.machinery import ModuleSpec

    class CustomFinder(MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname == "mymodule":
                return ModuleSpec("mymodule", CustomLoader(), origin="custom://mymodule")
            return None

    class CustomLoader(Loader):
        def create_module(self, spec):
            return None  # use default module creation

        def exec_module(self, module):
            module.value = 42
            module.func = lambda: print("loaded from custom source")

    sys.meta_path.insert(0, CustomFinder())

    import mymodule
    print(mymodule.value)  # 42
    mymodule.func()        # "loaded from custom source"

This is how import hooks work. You can implement:
- Importing from a database
- Importing from a network
- Importing from a custom file format
- On-the-fly code generation
- Module virtualization

### importlib — The Import Library

The `importlib` module provides a Python-level API for the import
system:

    import importlib

    # Import a module by name
    module = importlib.import_module("mymodule")

    # Reload a module
    importlib.reload(module)

    # Get the source code of a module
    source = importlib.source_from_cache(importlib.util.cache_from_source(...))

    # Inspect a module
    spec = importlib.util.find_spec("mymodule")
    print(spec.origin)  # where the module is loaded from

    # Create a module from source
    spec = importlib.util.spec_from_file_location("mymodule", "/path/to/module.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

importlib makes the import system programmable. You can:
- Import modules dynamically by name (string).
- Reload modules (useful for development).
- Inspect how modules are loaded (finders, loaders, specs).
- Create custom import workflows.

### How CPython Implements the Import System

The core import logic is in `Python/importlib` and `Python/import.c`
in the CPython source. The key modules:

- `importlib._bootstrap`: the core import implementation (in Python).
- `importlib.machinery`: finders and loaders for common cases.
- `importlib.abc`: abstract base classes for finders and loaders.
- `importlib.util`: utility functions for module creation, specs, etc.

The import system is implemented in Python (not C), which makes it
easier to understand and customize. The C code in import.c provides
the low-level machinery (module creation, execution), but the policy
(finding, loading, caching) is in Python.

To read the import implementation:

    import importlib._bootstrap
    print(importlib._bootstrap.__file__)  # path to the source

Or look at the CPython source:
- `Lib/importlib/_bootstrap.py`: the core implementation.
- `Lib/importlib/machinery.py`: PathFinder, FileFinder, etc.
- `Lib/importlib/abc.py`: Finder, Loader, MetaPathFinder, etc.

================================================================================
SECTION 3: EVIDENCE CHECKLIST — METACLASSES & IMPORT SYSTEM (L5)
================================================================================

### Metaclasses

Can you:

- [ ] Explain what a metaclass is and how it's different from a regular class
- [ ] Explain that `type` is the default metaclass and how `type(name, bases, dict)`
      creates classes
- [ ] Create a custom metaclass by subclassing `type`
- [ ] Override `__new__` in a metaclass to modify the class namespace
- [ ] Override `__init__` in a metaclass for class initialization
- [ ] Explain the difference between `__new__` and `__init__` in metaclasses
- [ ] Explain `__init_subclass__` and when to use it instead of a metaclass
- [ ] Explain `__set_name__` and how it enables automatic descriptor naming
- [ ] Explain metaclass conflicts and how to resolve them
- [ ] Implement a practical metaclass (registration, validation, field collection)
- [ ] Read and understand the class creation process in CPython source
- [ ] Know when metaclasses are the right tool vs. when they're overkill

### Import System

Can you:

- [ ] Explain the full import process: sys.modules cache → finders → loaders
- [ ] Explain the difference between finders and loaders
- [ ] Explain sys.meta_path and the default finders (BuiltinImporter,
      FrozenImporter, PathFinder)
- [ ] Explain sys.path and how PathFinder searches it
- [ ] Explain packages and __init__.py (and namespace packages without __init__.py)
- [ ] Use relative imports within packages
- [ ] Create a custom finder by subclassing MetaPathFinder
- [ ] Create a custom loader by subclassing Loader
- [ ] Use importlib to import modules dynamically, reload modules, inspect specs
- [ ] Explain ModuleSpec and what it contains (name, loader, origin, etc.)
- [ ] Read the CPython import implementation (importlib._bootstrap, machinery, abc)
- [ ] Understand the difference between absolute and relative imports
- [ ] Explain how import caching works (sys.modules) and how to reload modules

================================================================================
SECTION 4: NEXT — WHAT TO STUDY NEXT
================================================================================

Now that I understand metaclasses and the import system, the next
Python L4→L5 topics are:

1. **Asyncio Internals** — event loop, tasks, futures, coroutines,
   how async/await works under the hood, the executor model, the
   GIL's interaction with asyncio, how asyncio achieves concurrency
   in a single thread.

2. **CPython Memory Management & GC** — reference counting, generational
   GC, when objects are freed, memory layout (PyObject header, ob_type,
   ob_refcnt, ob_size), how the garbage collector works, when to use
   weakref, how to profile memory.

3. **CPython Bytecode & The Eval Loop** — how Python code is compiled
   to bytecode, the bytecode evaluation loop, frame objects, the
   evaluation stack, what common Python operations compile to, how
   to read bytecode with the dis module.

These three topics complete the Python L4→L5 deep dive series. Together
with descriptors and metaclasses, they cover the core internals:
attribute lookup, class creation, module loading, concurrency, memory,
and execution.

================================================================================
END OF PYTHON METACLASSES & IMPORT SYSTEM DEEP DIVE
================================================================================
