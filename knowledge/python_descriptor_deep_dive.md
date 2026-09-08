# ===========================================================================
# PYTHON DESCRIPTOR PROTOCOL & @PROPERTY INTERNALS — L5 DEEP DIVE
# ===========================================================================
# Part of: programming language mastery study, Python L4→L5
# Date: 2026-08-19
# Status: In progress

## WHY THIS MATTERS

The descriptor protocol is one of the most important — and most
misunderstood — mechanisms in Python. It is the foundation for:
- @property (managed attributes)
- @classmethod and @staticmethod
- @abstractmethod (from ABC)
- __set_name__ (PEP 487)
- SQLAlchemy's column mapping
- Django's model fields
- dataclasses field behavior
- Any library that does attribute-level interception

Understanding descriptors at L5 means: you can explain exactly what
happens at every step, you can read the CPython source, and you can
implement your own descriptor from scratch.

================================================================================
SECTION 1: WHAT A DESCRIPTOR IS
================================================================================

A descriptor is any object that defines at least one of these methods:

    __get__(self, instance, owner)
    __set__(self, instance, value)
    __delete__(self, instance)

If an object defines __set__ or __delete__, it's a DATA descriptor.
If it only defines __get__, it's a NON-DATA descriptor.

This distinction matters because of how Python's attribute lookup
resolves them — more on that in Section 4.

================================================================================
SECTION 2: HOW DESCRIPTORS ARE TRIGGERED
================================================================================

Descriptors are ONLY triggered through attribute access on an OBJECT
or a CLASS. They do NOT trigger when you access the descriptor object
directly from the class __dict__.

Example:

    class MyDescriptor:
        def __get__(self, instance, owner):
            print(f"__get__ called: instance={instance}, owner={owner}")
            return 42

    class MyClass:
        x = MyDescriptor()

    obj = MyClass()

    # THIS triggers the descriptor:
    obj.x          # __get__ called: instance=<MyClass>, owner=<class MyClass>
                   # returns 42

    # THIS does NOT trigger the descriptor:
    MyClass.__dict__['x']   # returns the MyDescriptor instance directly

    # THIS also triggers it (class-level access):
    MyClass.x      # __get__ called: instance=None, owner=<class MyClass>
                   # returns 42

The rule: descriptor invocation happens when the attribute is accessed
via the normal attribute lookup mechanism (dot notation, getattr()),
NOT when you reach into __dict__ directly.

================================================================================
SECTION 3: __get__ DETAILED
================================================================================

Signature: __get__(self, instance, owner)

- instance: the object whose attribute was accessed, or None if accessed
  on the class itself.
- owner: the class that owns the descriptor (always the class, even when
  accessed on an instance).

Data flow:

    obj.x
    │
    ▼
    type(obj).__getattribute__(obj, 'x')   # this is the default
    │
    ▼
    Look up 'x' in type(obj).__dict__ (and MRO)
    │
    ▼
    If value is a descriptor with __get__:
        call descriptor.__get__(obj, type(obj))
    Else:
        return the value

Example with both instance and class access:

    class RevealAccess:
        def __get__(self, instance, owner):
            if instance is None:
                return f"accessed on class {owner.__name__}"
            return f"accessed on instance {id(instance)} of {owner.__name__}"

    class Test:
        attr = RevealAccess()

    Test.attr       # "accessed on class Test"
    Test().attr     # "accessed on instance 140234862736480 of Test"

================================================================================
SECTION 4: __set__ AND __delete__
================================================================================

__set__(self, instance, value):
- Called when you do: instance.attr = value
- instance: the object whose attribute is being set
- value: the value being assigned

__delete__(self, instance):
- Called when you do: del instance.attr
- instance: the object whose attribute is being deleted

IMPORTANT: __set__ and __delete__ are ONLY triggered on INSTANCE
access, not on class access. If you do MyClass.x = 5, you're replacing
the descriptor in the class __dict__, not calling __set__.

Example:

    class Protected:
        def __set__(self, instance, value):
            print(f"__set__ called on {id(instance)} with {value!r}")
            # In a real descriptor, you'd store the value somewhere
            instance.__dict__[self.private_name] = value

        def __delete__(self, instance):
            print(f"__delete__ called on {id(instance)}")
            del instance.__dict__[self.private_name]

        def __init__(self, private_name):
            self.private_name = private_name

    class Account:
        balance = Protected('_balance')

    acc = Account()
    acc.balance = 1000     # __set__ called
    acc.balance = 2000     # __set__ called again
    del acc.balance        # __delete__ called

================================================================================
SECTION 5: DATA VS NON-DATA DESCRIPTORS — THE LOOKUP ORDER
================================================================================

This is the critical subtlety that separates L3 from L4/L5.

Python's attribute lookup (type.__getattribute__) follows this order:

    1. Check type(obj).__dict__ and MRO for a DATA descriptor
       (has __set__ or __delete__) matching the attribute name.
       → If found, CALL IT (invoke __get__). DATA descriptors win
         over instance __dict__.

    2. Check instance.__dict__ for the attribute name.
       → If found, return it. Instance dict wins over NON-DATA
         descriptors.

    3. Check type(obj).__dict__ and MRO for a NON-DATA descriptor
       (only __get__) matching the attribute name.
       → If found, CALL IT.

    4. If nothing found, call __getattr__ (if defined).
       → This is the fallback for missing attributes.

MEMORIZE THIS: DATA descriptors override instance __dict__.
              NON-DATA descriptors do NOT override instance __dict__.

This is why @property works the way it does — it's a DATA descriptor
(has __set__), so setting obj.x = 5 calls the property setter, not
the instance dict.

Example showing the difference:

    class DataDescriptor:
        def __get__(self, instance, owner):
            return instance.__dict__.get('_data', 'not set')
        def __set__(self, instance, value):
            instance.__dict__['_data'] = value

    class NonDataDescriptor:
        def __get__(self, instance, owner):
            return instance.__dict__.get('_non-data', 'not set')

    class Test:
        data = DataDescriptor()
        nondata = NonDataDescriptor()

    t = Test()

    # Set via instance dict directly:
    t.__dict__['data'] = 'shadowed'
    t.__dict__['nondata'] = 'shadowed'

    # Access:
    t.data      # 'not set'  ← DATA descriptor wins over instance dict
    t.nondata   # 'shadowed' ← instance dict wins over non-data descriptor

This is the key insight that lets you understand @property, @classmethod,
and every other descriptor-based mechanism.

================================================================================
SECTION 6: PROPERTY DECORATOR — HOW IT WORKS
================================================================================

@property is a class that implements the descriptor protocol. It's a
DATA descriptor (has __set__ and __delete__ when a setter/deleter
is defined, otherwise just __get__).

Minimal implementation of property:

    class Property:
        def __init__(self, fget=None, fset=None, fdel=None, doc=None):
            self.fget = fget
            self.fset = fset
            self.fdel = fdel
            self.__doc__ = doc or (fget.__doc__ if fget else None)
            self.name =fget.__name__ if fget else None

        def __get__(self, instance, owner):
            if instance is None:
                return self
            if self.fget is None:
                raise AttributeError("unreadable attribute")
            return self.fget(instance)

        def __set__(self, instance, value):
            if self.fset is None:
                raise AttributeError("can't set attribute")
            self.fset(instance, value)

        def __delete__(self, instance):
            if self.fdel is None:
                raise AttributeError("can't delete attribute")
            self.fdel(instance)

        def getter(self, fget):
            return type(self)(fget, self.fset, self.fdel, self.__doc__)

        def setter(self, fset):
            return type(self)(self.fget, fset, self.fdel, self.__doc__)

        def deleter(self, fdel):
            return type(self)(self.fget, self.fset, fdel, self.__doc__)

Usage:

    class Celsius:
        def __init__(self, temp):
            self._temp = temp

        @property
        def temp(self):
            print("getting temp")
            return self._temp

        @temp.setter
        def temp(self, value):
            print("setting temp")
            self._temp = value

    c = Celsius(37)
    c.temp      # "getting temp" → 37
    c.temp = 100  # "setting temp"
    c.temp      # "getting temp" → 100

How the decorator syntax translates:

    class Celsius:
        @property
        def temp(self):
            ...

    # Is equivalent to:
    class Celsius:
        def temp(self):
            ...
        temp = property(temp)

    # And:
    @temp.setter
    def temp(self, value):
        ...

    # Is equivalent to:
    temp = temp.setter(temp)   # temp is now a NEW property with setter

Each @x.setter call creates a NEW property object that combines the
original getter with the new setter. The name 'temp' gets rebound to
this new property.

================================================================================
SECTION 7: CPYTHON SOURCE — HOW PROPERTY IS IMPLEMENTED
================================================================================

In CPython (Objects/descrobject.c), property is implemented as a
type called `property_type`. Here's the key structure:

    typedef struct {
        PyObject_HEAD
        PyObject *prop_get;   // the getter function
        PyObject *prop_set;   // the setter function (or NULL)
        PyObject *prop_del;   // the deleter function (or NULL)
        PyObject *prop_dict;  // the property's __dict__
    } propertyobject;

The tp_getset slot in the type object points to property_get/set/delete.
When Python executes `obj.attr`, the eval loop calls
PyObject_GetAttr → type_getattro → _PyObject_LookupSpecial →
the descriptor protocol.

For property specifically:
- property_descr_get is called with (self, instance, typeof(instance))
- If instance is NULL (class-level access), return self (the property object)
- Otherwise, call the stored getter function with (instance,) as args

The setter (property_descr_set):
- If prop_set is NULL, raise AttributeError
- Otherwise, call prop_set with (instance, value)

This is why @property objects are DATA descriptors — the type object
has both tp_getset (for get) and the set/delete slots filled in when
a setter/deleter exists.

================================================================================
SECTION 8: CLASS METHOD AND STATIC METHOD — DESCRIPTORS TOO
================================================================================

@classmethod and @staticmethod are ALSO descriptors. They're simpler
than property but follow the same mechanism.

    class ClassMethod:
        def __init__(self, f):
            self.f = f
        def __get__(self, instance, owner):
            if instance is None:
                return self
            return self.f.__get__(owner, type(owner))

    class StaticMethod:
        def __init__(self, f):
            self.f = f
        def __get__(self, instance, owner):
            return self.f

@classmethod.__get__ returns a bound method: it calls the original
function's __get__ with (owner, type(owner)) — binding the function
to the class, not the instance.

@staticmethod.__get__ just returns the original function unmodified.
No binding at all.

This is why:

    class Foo:
        @classmethod
        def cm(cls):
            return cls.__name__

        @staticmethod
        def sm():
            return "static"

    Foo.cm    # <bound method Foo.cm of <class Foo>>
    Foo.sm    # <function Foo.sm at 0x...>   ← NOT bound

================================================================================
SECTION 9: __set_name__ — PEP 487 (Python 3.6+)
================================================================================

Before Python 3.6, descriptors had no way to know what attribute name
they were assigned to. You had to pass the name manually:

    class OldStyle:
        my_attr = Descriptor('my_attr')  # name passed explicitly

PEP 487 added __set_name__(self, owner, name):

    class AutoName:
        def __set_name__(self, owner, name):
            self.name = name
            print(f"Descriptor {self!r} assigned to {owner.__name__}.{name}")

        def __get__(self, instance, owner):
            if instance is None:
                return self
            return instance.__dict__.get(self.name)

        def __set__(self, instance, value):
            instance.__dict__[self.name] = value

    class MyClass:
        x = AutoName()   # prints: Descriptor <...> assigned to MyClass.x
        y = AutoName()   # prints: Descriptor <...> assigned to MyClass.y

__set_name__ is CALLED ONCE when the class body is executed (during
class creation, by the type metaclass). It's called for EVERY descriptor
in the class namespace, including properties, classmethods, etc.

This is how dataclasses, attrs, and other libraries automatically detect
field names without requiring explicit name strings.

================================================================================
SECTION 10: COMMON DESCRIPTOR PITFALLS
================================================================================

1. Forgetting that descriptors are class-level, not instance-level.

   WRONG: Creating a new descriptor instance per object in __init__.
   RIGHT: Define the descriptor as a class attribute; it operates on
           instance __dict__ internally.

   Example of WRONG:

       class Bad:
           def __init__(self):
               self.x = MyDescriptor()  # This just stores the descriptor
                                         # in instance dict — NO magic.

   Example of RIGHT:

       class Good:
           x = MyDescriptor()  # Class-level — Python sees it as a descriptor

2. Using non-data descriptors when you need data descriptors.

   If you define only __get__ (non-data), instance __dict__ can shadow
   it. This is sometimes intentional (lazy properties that cache in
   instance __dict__), but often a bug.

3. Forgetting that __set__ doesn't work at the class level.

       class Foo:
           x = MyDescriptor()

       Foo.x = 5   # This REPLACES the descriptor, doesn't call __set__

4. Not storing values properly.

   A descriptor's __set__ needs somewhere to put the value. Common
   patterns:
   - Store in instance.__dict__ under a private name
   - Store in the descriptor instance itself (only works for shared state)
   - Store in a weak-key dictionary (for advanced cases)

5. Descriptor on a metaclass.

   Descriptors on a metaclass are triggered on CLASS access, not instance
   access. This is how __init_subclass__ hooks and ABCMeta work.

================================================================================
SECTION 11: ADVANCED — DESCRIPTORS IN THE WILD
================================================================================

SQLAlchemy columns:

    class User(Base):
        id = Column(Integer, primary_key=True)
        name = Column(String)

    Column is a descriptor. When you access user.name, the descriptor
    fetches the value from the instance's internal state. When you set
    user.name = "Alice", it marks the attribute as dirty for the ORM.

Django model fields:

    class Person(models.Model):
        name = models.CharField(max_length=100)

    Field.descriptor is a data descriptor that handles getting/setting
    the field value, tracking changes, and interfacing with the database.

This pattern — using descriptors to make class-level declarations that
control instance attribute behavior — is one of the most powerful
descriptor use cases and a hallmark of L5 understanding.

================================================================================
SECTION 12: EVIDENCE CHECKLIST — DESCRIPTOR MASTERY
================================================================================

Can you:

- [ ] Explain the difference between data and non-data descriptors
- [ ] Explain the full attribute lookup order (data desc → instance dict
      → non-data desc → __getattr__)
- [ ] Implement a descriptor from scratch (not using property/copy)
- [ ] Explain why @property is a data descriptor
- [ ] Explain why @staticmethod is NOT a data descriptor
- [ ] Read and explain CPython's property implementation (descrobject.c)
- [ ] Explain __set_name__ and how it enables automatic naming
- [ ] Identify when a descriptor is the RIGHT solution vs. a simpler
      approach (e.g., __getattr__/__setattr__)
- [ ] Debug a descriptor bug (shadowing, wrong lookup order, etc.)
- [ ] Explain how Django/SQLAlchemy use descriptors

================================================================================
END OF DESCRIPTOR DEEP DIVE
================================================================================
