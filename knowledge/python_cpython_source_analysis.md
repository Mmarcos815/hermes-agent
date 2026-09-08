# ===========================================================================
# CPYTHON ATTRIBUTE LOOKUP & DESCRIPTOR INVOCATION — SOURCE ANALYSIS
# ===========================================================================
# Part 2 of Python L4→L5 deep dive
# Date: 2026-08-19
# Status: In progress
# Companion file: python_descriptor_deep_dive.md (Part 1)

## WHY THIS MATTERS

The descriptor protocol is the mechanism. But HOW does Python actually
invoke it when you write `obj.x`? What C functions are called? What
does the lookup loop look like? This is L5 evidence: reading and
understanding CPython source.

We'll trace the full path from `obj.x` in Python source to the C code
that retrieves the attribute, including:
1. The eval loop → BINARY_SUBSCR / LOAD_ATTR opcode
2. PyObject_GetAttr → _PyObject_GetAttr
3. type_getattro → the descriptor protocol
4. The MRO walk and __dict__ lookup
5. How property, __getattr__, __getattribute__ fit in

================================================================================
SECTION 1: FROM PYTHON SOURCE TO OPCODES
================================================================================

When you write:

    x = obj.attr

The Python compiler emits bytecode. Let's look at what that actually is:

    import dis

    class Foo:
        pass

    def get_attr(obj):
        return obj.attr

    dis.dis(get_attr)
    #   0 LOAD_FAST                0 (obj)
    #   2 LOAD_ATTR                0 (attr)
    #   4 RETURN_VALUE

The LOAD_ATTR opcode (opcode 22 in CPython 3.11+) is what triggers
attribute lookup. In the eval loop (Python/ceval.c), LOAD_ATTR is
handled by the `LOAD_ATTR` case in the interpreter.

In CPython 3.11+ (which uses the "faster CPython" project with
specialized opcodes), LOAD_ATTR is specialized:

- LOAD_ATTR: generic attribute lookup
- LOAD_ATTR_INSTANCE_VALUE: optimized path for instance attributes
  stored in the object's __dict__ (fast path)
- LOAD_ATTR_MODULE: optimized for module-level attributes
- LOAD_ATTR_CLASS: optimized for class-level attributes

For our purposes, we follow the generic path: LOAD_ATTR → the C
function that implements attribute lookup.

================================================================================
SECTION 2: OBJECT_GETATTR — THE C ENTRY POINT
================================================================================

In CPython, attribute access is implemented by
`PyObject_GetAttr` (Python/api.c) and its internal counterpart
`_PyObject_GetAttr` (Objects/object.c).

The PUBLIC API:

    PyObject *PyObject_GetAttr(PyObject *v, PyObject *name)

This is what `getattr(obj, 'attr')` calls. But for dot notation
(`obj.attr`), Python uses a different path — it goes through the
type's `tp_getattro` slot.

### tp_getattro

Every type has a `tp_getattro` function pointer in its type object.
This is the function called when you access an attribute on an
instance of that type.

For the default case (most types), `tp_getattro` points to
`_PyObject_GenericGetAttr` (Objects/object.c), which implements the
standard attribute lookup algorithm.

For types that customize attribute access:
- `type` (the metaclass) has its own `type_getattro`
- `module` has `module_getattro`
- Classes that define `__getattr__` or `__getattribute__` get a
  custom `tp_getattro` that calls those methods

The slot is set up in `Objects/typeobject.c` when a type is created.

================================================================================
SECTION 3: THE GENERIC ATTRIBUTE LOOKUP ALGORITHM
================================================================================

`_PyObject_GenericGetAttr` (Objects/object.c) implements the default
attribute lookup. Here's the algorithm in pseudocode, mapped to the
actual C code:

    PyObject *_PyObject_GenericGetAttr(PyObject *obj, PyObject *name) {
        // 1. Look up the type of obj
        PyTypeObject *type = Py_TYPE(obj);

        // 2. Look for a data descriptor in the type's MRO
        //    (this is where properties, __set__ descriptors live)
        //    The lookup walks the MRO and checks each __dict__ for
        //    a descriptor with __set__ or __delete__
        PyObject *descr = lookup_data_descriptor(type, name);
        if (descr != NULL) {
            // Data descriptor found — invoke it
            return PyObject_GetAttr(descr, obj);  // calls descr.__get__(obj, type)
        }

        // 3. Look in the instance's __dict__
        PyObject *dict = HEAD(obj->_dict);  // or tp_dictoffset
        if (dict != NULL) {
            PyObject *value = PyDict_GetItem(dict, name);
            if (value != NULL) {
                Py_INCREF(value);
                return value;  // instance __dict__ wins over non-data descriptors
            }
        }

        // 4. Look for a non-data descriptor in the type's MRO
        descr = lookup_non_data_descriptor(type, name);
        if (descr != NULL) {
            return PyObject_GetAttr(descr, obj);  // invoke __get__
        }

        // 5. If __getattr__ is defined on the type, call it
        if (type->tp_getattro == type_getattro_with_getattr) {
            // ... call __getattr__ ...
        }

        // 6. Raise AttributeError
        PyErr_Format(PyExc_AttributeError,
                     "'%.50s' object has no attribute '%V'",
                     type->tp_name, name);
        return NULL;
    }

The actual C code is more complex (it handles reference counting,
error cases, optimization for common cases), but this is the logical
flow. The key insight: the order is DATA DESCRIPTOR → INSTANCE DICT →
NON-DATA DESCRIPTOR → __GETATTR__.

================================================================================
SECTION 4: DATA DESCRIPTOR LOOKUP — HOW PYTHON FINDS THEM
================================================================================

The data descriptor lookup (step 2 above) is the critical part.
Here's how it works in detail:

    static PyObject *
    lookup_data_descriptor(PyTypeObject *type, PyObject *name) {
        // Walk the MRO (method resolution order)
        for (Py_ssize_t i = 0; i < type->tp_mro->len; i++) {
            PyTypeObject *base = (PyTypeObject *)
                PyList_GetItem(type->tp_mro, i);

            // Get the type's __dict__ (the descriptor proxy)
            PyObject *dict = base->tp_dict;

            // Look up the name in the dict
            PyObject *descr = PyDict_GetItem(dict, name);
            if (descr != NULL) {
                // Check if it's a data descriptor
                if (Py_TYPE(descr)->tp_descr_get != NULL &&
                    Py_TYPE(descr)->tp_descr_set != NULL) {
                    // Has both __get__ and __set__ → data descriptor
                    return descr;
                }
            }
        }
        return NULL;  // no data descriptor found
    }

The check for data descriptor is: `tp_descr_get != NULL && tp_descr_set != NULL`.
- `tp_descr_get` is the C-level equivalent of __get__
- `tp_descr_set` is the C-level equivalent of __set__

For `property`:
- property_type has both tp_descr_get (property_descr_get) and
  tp_descr_set (property_descr_set) → DATA DESCRIPTOR

For a custom descriptor with only __get__:
- tp_descr_get is set, tp_descr_set is NULL → NON-DATA DESCRIPTOR

This is why @property triggers before instance __dict__: property is
a data descriptor, and data descriptors are checked first in the
lookup order.

================================================================================
SECTION 5: HOW __GET__ IS ACTUALLY CALLED
================================================================================

When a descriptor is found, Python calls it through the descriptor
protocol's C-level mechanism:

    // In _PyObject_GenericGetAttr, after finding a descriptor:
    PyObject *get = PyObject_GetAttr(descr, obj);

This calls `descr.__get__(obj, type(obj))`. But the ACTUAL mechanism
is through `tp_descr_get`:

    // The C-level descriptor protocol:
    typedef PyObject *(*descrgetfunc)(PyObject *self,
                                       PyObject *obj,
                                       PyObject *type);

    // For a descriptor object:
    // descr->ob_type->tp_descr_get is the __get__ implementation

    // When invoked:
    PyObject *result = descr->ob_type->tp_descr_get(descr, obj, type(obj));

For a property object:
- property_descr_get is called with (self=property, obj=instance, type=class)
- If obj is NULL (class-level access), property_descr_get returns self
- Otherwise, it calls the stored getter function with (obj,) as arguments

The descriptor protocol in C is defined by two slots in the type object:
- `tp_descr_get`: the __get__ function pointer
- `tp_descr_set`: the __set__ function pointer

Any object whose type has tp_descr_get set is a descriptor.
If it ALSO has tp_descr_set set, it's a data descriptor.

================================================================================
SECTION 6: TYPE_GETATTRO — HOW CLASS ATTRIBUTE LOOKUP WORKS
================================================================================

When you access `MyClass.x` (class-level access), the lookup goes
through `type_getattro` (for the `type` metaclass) or the type's
own `tp_getattro`.

For a regular class, attribute lookup on the CLASS follows a simpler
path:

    // type_getattro (for type metaclass) or generic for other types:

    PyObject *type_getattro(PyObject *obj, PyObject *name) {
        // obj here is the CLASS (a type object)

        // 1. Look in the class's __dict__ directly
        PyObject *dict = ((PyTypeObject *)obj)->tp_dict;
        PyObject *value = PyDict_GetItem(dict, name);
        if (value != NULL) {
            Py_INCREF(value);
            return value;
        }

        // 2. If it's a descriptor, invoke it
        //    (but at class level, __get__ is called with instance=NULL)
        if (Py_TYPE(value)->tp_descr_get != NULL) {
            return Py_TYPE(value)->tp_descr_get(value, NULL, obj);
        }

        // 3. Look in base classes (MRO)
        // ... walk MRO ...

        // 4. AttributeError
    }

The key difference: at class level, the instance __dict__ is NOT
checked (there's no instance). And descriptors are invoked with
`instance=NULL`, which is how __get__ knows it's being accessed on
the class.

This is why:

    class Foo:
        @property
        def x(self):
            return 42

    Foo.x      # Returns the property object itself (descriptor.__get__(None, Foo))
    Foo().x    # Returns 42 (descriptor.__get__(instance, Foo) calls the getter)

================================================================================
SECTION 7: __GETATTRIBUTE__ AND __GETATTR__ IN THE LOOKUP
================================================================================

These two methods customize attribute lookup at the Python level.
They're implemented in C as part of the type's `tp_getattro`.

### __getattribute__ (tp_getattro)

If a class defines `__getattribute__`, Python uses it for ALL
attribute access (replacing the generic algorithm). This is powerful
but dangerous — you must implement the full descriptor protocol
yourself or call `super().__getattribute__`.

    class Custom:
        def __getattribute__(self, name):
            print(f"accessing {name}")
            return super().__getattribute__(name)

    obj = Custom()
    obj.x  # prints "accessing x", then does normal lookup

In CPython, `type_getattro` checks if the type has a custom
`tp_getattro` (which is set when `__getattribute__` is defined) and
if so, calls it instead of the generic algorithm.

### __getattr__ (fallback)

`__getattr__` is called ONLY when the normal lookup fails to find
the attribute. It's the last resort.

In CPython, after the generic lookup fails (step 6 in Section 3),
if the type has `__getattr__` defined, Python calls it with the
attribute name as argument.

    class Lazy:
        def __init__(self):
            self._cache = {}

        def __getattr__(self, name):
            if name not in self._cache:
                self._cache[name] = f"computed {name}"
            return self._cache[name]

    obj = Lazy()
    obj.x  # __getattr__ called, returns "computed x"
    obj.x  # Now cached in instance dict — no __getattr__ next time

The key: __getattr__ is NOT called if the attribute is found through
the normal lookup (including descriptors and instance __dict__). It's
only the fallback.

================================================================================
SECTION 8: LEANING ON CPYTHON SOURCE — WHERE TO LOOK
================================================================================

The key files in CPython source (for CPython 3.11+):

| File | What It Contains |
|------|------------------|
| `Objects/object.c` | `_PyObject_GenericGetAttr`, `_PyObject_GetAttr`, the generic lookup |
| `Objects/typeobject.c` | `type_getattro`, type attribute handling, MRO iteration |
| `Python/ceval.c` | The eval loop, LOAD_ATTR opcode handling |
| `Objects/descrobject.c` | `property` implementation (property_type, property_descr_get/set) |
| `Objects/classobject.c` | Class object implementation (older, for old-style classes in 2.x — mostly legacy in 3.x) |
| `Include/object.h` | PyObject, type object structs, tp_getattro, tp_descr_get/set slots |
| `Include/descrobject.h` | Descriptor protocol C API |

For the descriptor protocol specifically:
- `Objects/descrobject.c`: read `property_get`, `property_set`, `property_delete`
- `Objects/object.c`: read `_PyObject_GenericGetAttr` for the lookup order
- `Include/object.h`: read the `PyTypeObject` struct for `tp_descr_get`/`tp_descr_set`

To build and read CPython source, clone the repo:
    git clone https://github.com/python/cpython.git
    cd cpython
    git checkout 3.11  # or the version you're studying

================================================================================
SECTION 9: TRACING A REAL ATTRIBUTE ACCESS
================================================================================

Let's trace what happens when you do `obj.x` on a class with a property:

    class Temperature:
        def __init__(self, celsius):
            self._celsius = celsius

        @property
        def celsius(self):
            return self._celsius

        @celsius.setter
        def celsius(self, value):
            self._celsius = value

    t = Temperature(37)
    t.celsius      # 37
    t.celsius = 100  # sets _celsius to 100

Here's the exact C-level trace for `t.celsius`:

    1. LOAD_ATTR opcode in eval loop (ceval.c)
       → calls _PyObject_GetAttr(t, "celsius")

    2. _PyObject_GetAttr → dispatches to t's type's tp_getattro
       → for a regular class, this is _PyObject_GenericGetAttr

    3. _PyObject_GenericGetAttr:
       a. Look up type(Temperature) in MRO for data descriptors
          → finds property object 'celsius' in Temperature.__dict__
          → checks: property_type has tp_descr_get AND tp_descr_set
          → YES → DATA DESCRIPTOR FOUND

       b. Invoke descriptor:
          → property_descr_get(property_obj, t, Temperature)
          → property_descr_get calls the stored getter (Temperature.celsius.fget)
          → getter returns t._celsius (37)
          → returns 37

    4. Result: 37 returned to Python code

For `t.celsius = 100`:

    1. STORE_ATTR opcode in eval loop
       → calls PyObject_SetAttr(t, "celsius", 100)

    2. PyObject_SetAttr → dispatches to type's tp_setattro
       → generic: _PyObject_GenericSetAttr

    3. _PyObject_GenericSetAttr:
       a. Look up data descriptor in type MRO
          → finds property 'celsius' (has tp_descr_set)
       b. Invoke descriptor's __set__:
          → property_descr_set(property_obj, t, 100)
          → calls the stored setter (Temperature.celsius.fset)
          → setter sets t._celsius = 100
       c. Return

    4. Result: _celsius is now 100

Notice: the instance __dict__ is NEVER checked for properties. The
data descriptor always wins. This is why you can't accidentally
shadow a property by setting an instance attribute with the same name.

================================================================================
SECTION 10: SUMMARY — THE LOOKUP ORDER (THE THING TO MEMORIZE)
================================================================================

The attribute lookup algorithm (from `obj.x` to the result):

    1. DATA DESCRIPTOR CHECK
       Walk MRO, find descriptor with __set__ or __delete__
       → If found, CALL __get__ and return result
       → DATA DESCRIPTORS WIN OVER EVERYTHING BELOW

    2. INSTANCE __DICT__ CHECK
       Look up name in obj.__dict__
       → If found, return it
       → INSTANCE DICT WINS OVER NON-DATA DESCRIPTORS

    3. NON-DATA DESCRIPTOR CHECK
       Walk MRO, find descriptor with only __get__ (no __set__)
       → If found, CALL __get__ and return result

    4. __GETATTRIBUTE__ CHECK
       If type defines __getattribute__, it was already called
       in step 1 (replaces the whole algorithm).
       If custom __getattribute__ called super() and still didn't
       find it, continue here.

    5. __GETATTR__ FALLBACK
       If the normal lookup FAILED (no descriptor, no instance dict
       entry, no __getattribute__ found it), call __getattr__ if
       the type defines it.

    6. ATTRIBUTEERROR
       If nothing found, raise AttributeError

MEMORIZE: DATA DESCRIPTORS > INSTANCE DICT > NON-DATA DESCRIPTORS > __GETATTR__

================================================================================
SECTION 11: EVIDENCE CHECKLIST — CPYTHON SOURCE MASTERY
================================================================================

Can you:

- [ ] Find and read `_PyObject_GenericGetAttr` in CPython source
- [ ] Explain the data descriptor vs non-data descriptor distinction
      at the C level (tp_descr_get vs tp_descr_set)
- [ ] Trace the full path from `obj.x` to the result, naming each
      C function involved
- [ ] Explain how property is implemented in descrobject.c
- [ ] Explain how __getattr__ and __getattribute__ hook into the
      type's tp_getattro slot
- [ ] Explain why data descriptors override instance __dict__
- [ ] Read the LOAD_ATTR opcode implementation in ceval.c
- [ ] Explain the MRO walk in attribute lookup
- [ ] Build CPython from source and run a test program under GDB
      to step through the lookup

================================================================================
END OF CPYTHON SOURCE ANALYSIS
================================================================================
