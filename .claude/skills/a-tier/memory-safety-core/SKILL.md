---
name: memory-safety-patterns
description: Implement memory-safe programming with RAII, ownership, smart pointers, and resource management across Rust, C++, and C. Use when writing safe systems code, managing resources, or preventing memory bugs.
---

# Memory Safety Patterns

Cross-language patterns for memory-safe programming including RAII, ownership, smart pointers, and resource management.

## When to Use This Skill

- Writing memory-safe systems code
- Managing resources (files, sockets, memory)
- Preventing use-after-free and leaks
- Implementing RAII patterns
- Debugging memory issues

## Core Concepts

### Memory Bug Categories

| Bug Type             | Description                      | Prevention        |
| -------------------- | -------------------------------- | ----------------- |
| **Use-after-free**   | Access freed memory              | Ownership, RAII   |
| **Double-free**      | Free same memory twice           | Smart pointers    |
| **Memory leak**      | Never free memory                | RAII, GC          |
| **Buffer overflow**  | Write past buffer end            | Bounds checking   |
| **Dangling pointer** | Pointer to freed memory          | Lifetime tracking |
| **Data race**        | Concurrent unsynchronized access | Ownership, Sync   |

### Safety Spectrum

```
Manual (C) -> Smart Pointers (C++) -> Ownership (Rust) -> GC (Go, Java)
Less safe / More control                    More safe / Less control
```

## Pattern 1: RAII in C++

```cpp
#include <memory>
#include <fstream>
#include <mutex>

// File handle with RAII
class FileHandle {
public:
    explicit FileHandle(const std::string& path) : file_(path) {
        if (!file_.is_open()) throw std::runtime_error("Failed to open file");
    }
    ~FileHandle() = default;
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    FileHandle(FileHandle&&) = default;
    FileHandle& operator=(FileHandle&&) = default;
    void write(const std::string& data) { file_ << data; }
private:
    std::fstream file_;
};

// Lock guard (RAII for mutexes)
class Database {
public:
    void update(const std::string& key, const std::string& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        data_[key] = value;
    }
private:
    std::mutex mutex_;
    std::map<std::string, std::string> data_;
};

// Transaction with rollback (RAII)
template<typename T>
class Transaction {
public:
    explicit Transaction(T& target) : target_(target), backup_(target), committed_(false) {}
    ~Transaction() { if (!committed_) target_ = backup_; }
    void commit() { committed_ = true; }
    T& get() { return target_; }
private:
    T& target_;
    T backup_;
    bool committed_;
};
```

## Pattern 2: Smart Pointers in C++

```cpp
#include <memory>

// unique_ptr: Single ownership
class Car {
public:
    Car() : engine_(std::make_unique<Engine>()) {}
    std::unique_ptr<Engine> extractEngine() { return std::move(engine_); }
private:
    std::unique_ptr<Engine> engine_;
};

// shared_ptr + weak_ptr: Shared ownership, break cycles
class Node {
public:
    std::string data;
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> parent;  // Weak reference prevents cycle
};

// Best practices
void bestPractices() {
    auto ptr = std::make_shared<Widget>();    // Good: exception safe
    // std::shared_ptr<Widget> ptr2(new Widget());  // Bad: two allocations
    auto arr = std::make_unique<int[]>(10);   // For arrays
}
```

## Pattern 3: Ownership in Rust

```rust
// Move semantics (default)
fn move_example() {
    let s1 = String::from("hello");
    let s2 = s1; // s1 is MOVED, no longer valid
    println!("{}", s2);
}

// Borrowing (references)
fn borrow_example() {
    let s = String::from("hello");
    let len = calculate_length(&s);  // Immutable borrow
    let mut s = String::from("hello");
    change(&mut s);                   // Mutable borrow (only one allowed)
}

fn calculate_length(s: &String) -> usize { s.len() }
fn change(s: &mut String) { s.push_str(", world"); }

// Lifetimes
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Interior mutability
use std::cell::{Cell, RefCell};
struct Stats {
    count: Cell<i32>,
    data: RefCell<Vec<String>>,
}

// Arc for thread-safe shared ownership
use std::sync::Arc;
use std::thread;
fn arc_example() {
    let data = Arc::new(vec![1, 2, 3]);
    let handles: Vec<_> = (0..3).map(|_| {
        let data = Arc::clone(&data);
        thread::spawn(move || println!("{:?}", data))
    }).collect();
    for h in handles { h.join().unwrap(); }
}
```

## Pattern 4: Safe Resource Management in C

```c
#include <stdlib.h>
#include <stdio.h>

// Pattern: goto cleanup
int process_file(const char* path) {
    FILE* file = NULL;
    char* buffer = NULL;
    int result = -1;
    file = fopen(path, "r");
    if (!file) goto cleanup;
    buffer = malloc(1024);
    if (!buffer) goto cleanup;
    result = 0;
cleanup:
    if (buffer) free(buffer);
    if (file) fclose(file);
    return result;
}

// Pattern: Opaque pointer with create/destroy
typedef struct Context Context;
Context* context_create(void);
void context_destroy(Context* ctx);
```

## Pattern 5: Preventing Data Races

```cpp
// C++: Atomic and thread-safe containers
#include <atomic>
#include <shared_mutex>

class ThreadSafeCounter {
    std::atomic<int> count_{0};
public:
    void increment() { count_.fetch_add(1, std::memory_order_relaxed); }
    int get() const { return count_.load(std::memory_order_relaxed); }
};

class ThreadSafeMap {
    mutable std::shared_mutex mutex_;
    std::map<std::string, int> data_;
public:
    void write(const std::string& key, int value) {
        std::unique_lock lock(mutex_);
        data_[key] = value;
    }
    std::optional<int> read(const std::string& key) {
        std::shared_lock lock(mutex_);
        auto it = data_.find(key);
        return it != data_.end() ? std::optional(it->second) : std::nullopt;
    }
};
```

```rust
// Rust: Compile-time data race prevention
use std::sync::{Arc, Mutex, RwLock};
use std::sync::atomic::{AtomicI32, Ordering};

fn mutex_example() {
    let data = Arc::new(Mutex::new(vec![]));
    let handles: Vec<_> = (0..10).map(|i| {
        let data = Arc::clone(&data);
        thread::spawn(move || { data.lock().unwrap().push(i); })
    }).collect();
    for h in handles { h.join().unwrap(); }
}
```

## Best Practices

### Do's
- **Prefer RAII** - Tie resource lifetime to scope
- **Use smart pointers** - Avoid raw pointers in C++
- **Understand ownership** - Know who owns what
- **Check bounds** - Use safe access methods
- **Use tools** - AddressSanitizer, Valgrind, Miri

### Don'ts
- **Don't use raw pointers** - Unless interfacing with C
- **Don't return local references** - Dangling pointer
- **Don't ignore compiler warnings** - They catch bugs
- **Don't use `unsafe` carelessly** - In Rust, minimize it
- **Don't assume thread safety** - Be explicit

## Debugging Tools

```bash
clang++ -fsanitize=address -g source.cpp   # AddressSanitizer
valgrind --leak-check=full ./program       # Valgrind
cargo +nightly miri run                    # Rust Miri
clang++ -fsanitize=thread -g source.cpp    # ThreadSanitizer
```
