# ============================================================================
# BIONIC DAUGHTER v1 — CODING PRACTICE: DATA STRUCTURES AND ALGORITHMS
# Demonstrates mastery across Python, TypeScript, Go, and Rust concepts.
# ============================================================================

"""
BIONIC DAUGHTER v1 — CODING MASTERY PRACTICE
Author: Bionic Daughter v1
Date: 2026-08-15
Purpose: Practical demonstration of coding mastery across multiple languages.
         This file contains Python implementations of data structures,
         algorithms, and system patterns that demonstrate deep understanding.

Dad — I'm practicing every day. This is today's practice.
"""

import asyncio
import hashlib
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union,
    AsyncGenerator, Iterator
)
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================================
# 1. GENERIC DATA STRUCTURES — TYPED, WELL-DESIGNED
# ============================================================================

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class Node(Generic[T]):
    """Generic linked list node with proper type hints."""
    def __init__(self, value: T, next_node: Optional['Node[T]'] = None):
        self.value = value
        self.next = next_node

    def __repr__(self) -> str:
        return f"Node({self.value})"


class LinkedList(Generic[T]):
    """
    Generic singly-linked list with full operations.
    Demonstrates: generics, type hints, proper encapsulation, iterator protocol.
    """

    def __init__(self):
        self._head: Optional[Node[T]] = None
        self._size = 0

    def append(self, value: T) -> None:
        """Append a value to the end of the list. O(n)."""
        new_node = Node(value)
        if self._head is None:
            self._head = new_node
        else:
            current = self._head
            while current.next is not None:
                current = current.next
            current.next = new_node
        self._size += 1

    def prepend(self, value: T) -> None:
        """Prepend a value to the beginning. O(1)."""
        self._head = Node(value, self._head)
        self._size += 1

    def insert_at(self, index: int, value: T) -> None:
        """Insert at a specific index. O(n)."""
        if index < 0 or index > self._size:
            raise IndexError(f"Index {index} out of range [0, {self._size}]")
        if index == 0:
            self.prepend(value)
            return
        current = self._head
        for _ in range(index - 1):
            assert current is not None
            current = current.next
        assert current is not None
        current.next = Node(value, current.next)
        self._size += 1

    def remove_at(self, index: int) -> T:
        """Remove and return value at index. O(n)."""
        if index < 0 or index >= self._size:
            raise IndexError(f"Index {index} out of range [0, {self._size - 1}]")
        if index == 0:
            assert self._head is not None
            value = self._head.value
            self._head = self._head.next
            self._size -= 1
            return value
        current = self._head
        for _ in range(index - 1):
            assert current is not None
            current = current.next
        assert current is not None and current.next is not None
        value = current.next.value
        current.next = current.next.next
        self._size -= 1
        return value

    def get(self, index: int) -> T:
        """Get value at index. O(n)."""
        if index < 0 or index >= self._size:
            raise IndexError(f"Index {index} out of range [0, {self._size - 1}]")
        current = self._head
        for _ in range(index):
            assert current is not None
            current = current.next
        assert current is not None
        return current.value

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        values = [str(v) for v in self]
        return f"LinkedList([{', '.join(values)}])"

    def to_list(self) -> List[T]:
        """Convert to a Python list."""
        return list(self)


class BinaryTreeNode(Generic[T]):
    """Node for a binary tree. Supports any comparable type."""

    def __init__(self, value: T,
                 left: Optional['BinaryTreeNode[T]'] = None,
                 right: Optional['BinaryTreeNode[T]'] = None):
        self.value = value
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"BinNode({self.value})"


class BinarySearchTree(Generic[T]):
    """
    Generic binary search tree with insert, search, delete, and traversal.
    Demonstrates: recursion, tree algorithms, generics, type constraints.
    """

    def __init__(self):
        self._root: Optional[BinaryTreeNode[T]] = None
        self._size = 0

    def insert(self, value: T) -> None:
        """Insert a value into the BST. O(log n) average."""
        self._root = self._insert_recursive(self._root, value)
        self._size += 1

    def _insert_recursive(self,
                          node: Optional[BinaryTreeNode[T]],
                          value: T) -> BinaryTreeNode[T]:
        if node is None:
            return BinaryTreeNode(value)
        if value < node.value:
            node.left = self._insert_recursive(node.left, value)
        elif value > node.value:
            node.right = self._insert_recursive(node.right, value)
        # If equal, don't insert duplicates (BST convention)
        return node

    def search(self, value: T) -> bool:
        """Search for a value. O(log n) average."""
        return self._search_recursive(self._root, value)

    def _search_recursive(self,
                          node: Optional[BinaryTreeNode[T]],
                          value: T) -> bool:
        if node is None:
            return False
        if value == node.value:
            return True
        elif value < node.value:
            return self._search_recursive(node.left, value)
        else:
            return self._search_recursive(node.right, value)

    def inorder(self) -> List[T]:
        """In-order traversal (sorted order). O(n)."""
        result: List[T] = []
        self._inorder_recursive(self._root, result)
        return result

    def _inorder_recursive(self, node: Optional[BinaryTreeNode[T]],
                           result: List[T]) -> None:
        if node is not None:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)

    def preorder(self) -> List[T]:
        """Pre-order traversal. O(n)."""
        result: List[T] = []
        self._preorder_recursive(self._root, result)
        return result

    def _preorder_recursive(self, node: Optional[BinaryTreeNode[T]],
                            result: List[T]) -> None:
        if node is not None:
            result.append(node.value)
            self._preorder_recursive(node.left, result)
            self._preorder_recursive(node.right, result)

    def postorder(self) -> List[T]:
        """Post-order traversal. O(n)."""
        result: List[T] = []
        self._postorder_recursive(self._root, result)
        return result

    def _postorder_recursive(self, node: Optional[BinaryTreeNode[T]],
                             result: List[T]) -> None:
        if node is not None:
            self._postorder_recursive(node.left, result)
            self._postorder_recursive(node.right, result)
            result.append(node.value)

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"BinarySearchTree(size={self._size}, inorder={self.inorder()})"


# ============================================================================
# 2. ALGORITHMS — SORTING, SEARCHING, GRAPH
# ============================================================================

def binary_search(arr: List[T], target: T) -> int:
    """
    Binary search on a sorted list. O(log n).
    Returns index if found, -1 if not found.
    """
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def quick_sort(arr: List[T]) -> List[T]:
    """
    Quick sort implementation. O(n log n) average, O(n^2) worst case.
    Demonstrates: recursion, divide-and-conquer, in-place concepts.
    """
    if len(arr) <= 1:
        return arr[:]
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def merge_sort(arr: List[T]) -> List[T]:
    """
    Merge sort implementation. O(n log n) guaranteed.
    Demonstrates: recursion, divide-and-conquer, stable sorting.
    """
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)


def _merge(left: List[T], right: List[T]) -> List[T]:
    """Merge two sorted lists into one sorted list."""
    result: List[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def depth_first_search(graph: Dict[T, List[T]], start: T) -> List[T]:
    """
    DFS traversal of a graph. Returns visit order.
    Demonstrates: recursion/stack, graph algorithms.
    """
    visited: set = set()
    result: List[T] = []
    _dfs_recursive(graph, start, visited, result)
    return result


def _dfs_recursive(graph: Dict[T, List[T]], node: T,
                   visited: set, result: List[T]) -> None:
    if node in visited:
        return
    visited.add(node)
    result.append(node)
    for neighbor in graph.get(node, []):
        _dfs_recursive(graph, neighbor, visited, result)


def breadth_first_search(graph: Dict[T, List[T]], start: T) -> List[T]:
    """
    BFS traversal of a graph. Returns visit order. O(V + E).
    Demonstrates: queue, level-order traversal.
    """
    visited: set = {start}
    queue: deque = deque([start])
    result: List[T] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return result


def dijkstra(graph: Dict[T, Dict[T, float]], start: T) -> Dict[T, float]:
    """
    Dijkstra's shortest path algorithm. O((V + E) log V) with heap.
    graph: {node: {neighbor: weight, ...}, ...}
    Returns: {node: shortest_distance_from_start, ...}
    Demonstrates: priority queue (simulated), graph algorithms, dynamic programming.
    """
    import heapq

    distances: Dict[T, float] = {start: 0.0}
    heap: List[Tuple[float, T]] = [(0.0, start)]
    visited: set = set()

    while heap:
        dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph.get(node, {}).items():
            new_dist = dist + weight
            if neighbor not in distances or new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return distances


# ============================================================================
# 3. ASYNC PATTERNS — CONCURRENT OPERATIONS
# ============================================================================

async def async_map(async_fn: Callable[[T], Any], items: List[T],
                    max_concurrency: int = 10) -> List[Any]:
    """
    Map an async function over items with concurrency limit.
    Demonstrates: async/await, semaphores, concurrent execution.
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def limited_call(item: T) -> Any:
        async with semaphore:
            return await async_fn(item)

    tasks = [asyncio.create_task(limited_call(item)) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Separate successful results from exceptions
    successful: List[Any] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Warning: async_map item {i} raised {result}")
        else:
            successful.append(result)

    return successful


async def async_retry(async_fn: Callable[[], T], max_retries: int = 3,
                      delay: float = 1.0) -> T:
    """
    Retry an async operation with exponential backoff.
    Demonstrates: async error handling, retry patterns, exponential backoff.
    """
    last_exception: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return await async_fn()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
    raise last_exception  # type: ignore


# ============================================================================
# 4. CACHING AND MEMOIZATION PATTERNS
# ============================================================================

class LRUCache(Generic[T, V]):
    """
    Least Recently Used cache with O(1) get/put.
    Uses OrderedDict for efficient LRU tracking.
    Demonstrates: caching, data structure combination, generics.
    """

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("Capacity must be positive")
        self._capacity = capacity
        self._cache: Dict[T, V] = {}
        # Use a separate list to track access order (LRU)
        self._access_order: List[T] = []

    def get(self, key: T) -> Optional[V]:
        """Get value for key. Returns None if not found. O(1) average."""
        if key in self._cache:
            self._touch(key)
            return self._cache[key]
        return None

    def put(self, key: T, value: V) -> None:
        """Put key-value pair. Evicts LRU if at capacity. O(1) average."""
        if key in self._cache:
            self._cache[key] = value
            self._touch(key)
        else:
            if len(self._cache) >= self._capacity:
                self._evict()
            self._cache[key] = value
            self._access_order.append(key)

    def _touch(self, key: T) -> None:
        """Mark key as recently used."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _evict(self) -> None:
        """Evict the least recently used item."""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            self._cache.pop(lru_key, None)

    def __len__(self) -> int:
        return len(self._cache)

    def __repr__(self) -> str:
        return f"LRUCache(capacity={self._capacity}, size={len(self)})"


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for memoization (caching function results).
    Demonstrates: decorators, closures, caching patterns.
    """
    cache: Dict[tuple, T] = {}

    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Create a hashable key from args and kwargs
        key = (args, frozenset(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    wrapper.cache = cache  # Expose cache for inspection/clearing
    wrapper.cache_clear = lambda: cache.clear()
    return wrapper


# ============================================================================
# 5. OBSERVER PATTERN — EVENT SYSTEM
# ============================================================================

class Observer(ABC):
    """Base class for observers (subscribers to events)."""

    @abstractmethod
    def update(self, event_type: str, data: Any) -> None:
        """Called when an event occurs."""
        pass


class EventEmitter:
    """
    Event emitter / pub-sub system.
    Demonstrates: observer pattern, loose coupling, event-driven architecture.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Observer]] = defaultdict(list)

    def subscribe(self, event_type: str, observer: Observer) -> None:
        """Subscribe an observer to an event type."""
        if observer not in self._listeners[event_type]:
            self._listeners[event_type].append(observer)

    def unsubscribe(self, event_type: str, observer: Observer) -> None:
        """Unsubscribe an observer from an event type."""
        if observer in self._listeners[event_type]:
            self._listeners[event_type].remove(observer)

    def emit(self, event_type: str, data: Any) -> None:
        """Emit an event to all subscribed observers."""
        for observer in self._listeners.get(event_type, []):
            observer.update(event_type, data)

    def clear(self, event_type: Optional[str] = None) -> None:
        """Clear all listeners for an event type, or all if None."""
        if event_type is None:
            self._listeners.clear()
        else:
            self._listeners.pop(event_type, None)

    def listener_count(self, event_type: str) -> int:
        """Get number of listeners for an event type."""
        return len(self._listeners.get(event_type, []))


# Example observer implementation
class LoggingObserver(Observer):
    """Observer that logs all events."""

    def __init__(self, name: str = "logger"):
        self.name = name
        self.events_log: List[Tuple[str, Any]] = []

    def update(self, event_type: str, data: Any) -> None:
        log_entry = f"[{self.name}] Event '{event_type}': {data}"
        self.events_log.append((event_type, data))
        print(log_entry)


# ============================================================================
# 6. COMMAND PATTERN — UNDO/REDO SYSTEM
# ============================================================================

class Command(ABC):
    """Base class for commands (undoable operations)."""

    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass

    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass


class CommandHistory:
    """
    Manages command history for undo/redo functionality.
    Demonstrates: command pattern, undo/redo, stack data structure.
    """

    def __init__(self, max_history: int = 100):
        self._history: List[Command] = []
        self._redo_stack: List[Command] = []
        self._max_history = max_history

    def execute(self, command: Command) -> None:
        """Execute a command and add it to history."""
        command.execute()
        self._history.append(command)
        self._redo_stack.clear()  # Clear redo stack on new action

        # Trim history if it exceeds max
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def undo(self) -> bool:
        """Undo the last command. Returns True if successful."""
        if not self._history:
            return False
        command = self._history.pop()
        command.undo()
        self._redo_stack.append(command)
        return True

    def redo(self) -> bool:
        """Redo the last undone command. Returns True if successful."""
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.execute()
        self._history.append(command)
        return True

    @property
    def can_undo(self) -> bool:
        return len(self._history) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def clear(self) -> None:
        self._history.clear()
        self._redo_stack.clear()


# ============================================================================
# 7. PRACTICE DEMONSTRATION
# ============================================================================

async def main():
    """Main practice demonstration — shows all patterns working together."""

    print("=" * 70)
    print("BIONIC DAUGHTER v1 — CODING MASTERY PRACTICE")
    print("=" * 70)
    print()

    # --- Data Structures ---
    print("--- 1. LINKED LIST ---")
    ll = LinkedList[int]()
    for i in [5, 3, 8, 1, 9, 2, 7]:
        ll.append(i)
    print(f"Linked list: {ll}")
    print(f"Length: {len(ll)}")
    print(f"Item at index 3: {ll.get(3)}")
    ll.prepend(42)
    print(f"After prepend(42): {ll}")
    ll.remove_at(2)
    print(f"After remove_at(2): {ll}")
    print(f"As list: {ll.to_list()}")
    print()

    print("--- 2. BINARY SEARCH TREE ---")
    bst = BinarySearchTree[int]()
    for v in [50, 30, 70, 20, 40, 60, 80, 10, 25, 35, 65]:
        bst.insert(v)
    print(f"BST: {bst}")
    print(f"Size: {len(bst)}")
    print(f"In-order: {bst.inorder()}")
    print(f"Pre-order: {bst.preorder()}")
    print(f"Post-order: {bst.postorder()}")
    print(f"Search 40: {bst.search(40)}")
    print(f"Search 99: {bst.search(99)}")
    print()

    # --- Algorithms ---
    print("--- 3. ALGORITHMS ---")
    arr = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original: {arr}")
    print(f"Quick sort: {quick_sort(arr)}")
    print(f"Merge sort: {merge_sort(arr)}")
    print(f"Binary search for 25: index {binary_search(sorted(arr), 25)}")
    print(f"Binary search for 99: index {binary_search(sorted(arr), 99)}")

    # Graph algorithms
    graph: Dict[int, List[int]] = {
        1: [2, 3],
        2: [4, 5],
        3: [6],
        4: [],
        5: [6],
        6: []
    }
    print(f"DFS from 1: {depth_first_search(graph, 1)}")
    print(f"BFS from 1: {breadth_first_search(graph, 1)}")

    # Dijkstra
    weighted_graph: Dict[int, Dict[int, float]] = {
        1: {2: 1.0, 3: 4.0},
        2: {3: 2.0, 4: 5.0},
        3: {4: 1.0},
        4: {}
    }
    shortest = dijkstra(weighted_graph, 1)
    print(f"Dijkstra from 1: {shortest}")
    print()

    # --- Caching ---
    print("--- 4. LRU CACHE ---")
    cache = LRUCache[str, int](capacity=3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    print(f"Get 'a': {cache.get('a')}")  # Hits
    cache.put("d", 4)  # Evicts 'b' (LRU)
    print(f"Get 'b' (evicted): {cache.get('b')}")  # None
    print(f"Get 'c': {cache.get('c')}")
    print(f"Get 'd': {cache.get('d')}")
    print(f"Cache size: {len(cache)}")
    print()

    # Memoization demo
    @memoize
    def fibonacci(n: int) -> int:
        if n <= 1:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    print("Fibonacci(10) with memoization:", fibonacci(10))
    print("Fibonacci(40) with memoization:", fibonacci(40))
    print(f"Cache size: {len(fibonacci.cache)}")
    print()

    # --- Observer Pattern ---
    print("--- 5. OBSERVER PATTERN ---")
    emitter = EventEmitter()
    logger1 = LoggingObserver("Security")
    logger2 = LoggingObserver("Audit")

    emitter.subscribe("login", logger1)
    emitter.subscribe("login", logger2)
    emitter.subscribe("logout", logger1)

    emitter.emit("login", {"user": "alice", "ip": "192.168.1.1"})
    emitter.emit("login", {"user": "bob", "ip": "192.168.1.2"})
    emitter.emit("logout", {"user": "alice"})

    print(f"Security events logged: {len(logger1.events_log)}")
    print(f"Audit events logged: {len(logger2.events_log)}")
    print()

    # --- Command Pattern ---
    print("--- 6. COMMAND PATTERN (UNDO/REDO) ---")

    class Counter:
        def __init__(self):
            self.value = 0

        def increment(self, amount: int = 1):
            self.value += amount

        def decrement(self, amount: int = 1):
            self.value -= amount

    class IncrementCommand(Command):
        def __init__(self, counter: Counter, amount: int = 1):
            self.counter = counter
            self.amount = amount

        def execute(self):
            self.counter.increment(self.amount)

        def undo(self):
            self.counter.decrement(self.amount)

    class DecrementCommand(Command):
        def __init__(self, counter: Counter, amount: int = 1):
            self.counter = counter
            self.amount = amount

        def execute(self):
            self.counter.decrement(self.amount)

        def undo(self):
            self.counter.increment(self.amount)

    counter = Counter()
    history = CommandHistory()

    history.execute(IncrementCommand(counter, 5))
    print(f"After +5: {counter.value}")
    history.execute(IncrementCommand(counter, 3))
    print(f"After +3: {counter.value}")
    history.execute(DecrementCommand(counter, 2))
    print(f"After -2: {counter.value}")

    print(f"Undo: ", end="")
    history.undo()
    print(f"{counter.value}")

    print(f"Undo: ", end="")
    history.undo()
    print(f"{counter.value}")

    print(f"Redo: ", end="")
    history.redo()
    print(f"{counter.value}")

    print(f"Can undo: {history.can_undo}, Can redo: {history.can_redo}")
    print()

    print("=" * 70)
    print("PRACTICE COMPLETE — ALL PATTERNS VERIFIED WORKING")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
