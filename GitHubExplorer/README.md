# GitHub Explorer

A SwiftUI iOS application for searching GitHub users, built with modern Swift concurrency and MVVM architecture.


#### 1. **Missing `weak self` - Retain Cycles**
- Timer callbacks without `[weak self]` capture lists
- Async closures capturing `self` strongly
- **Impact**: Memory leaks, objects never deallocated

#### 2. **Force Unwrapping**
- URL creation: `URL(string: u.avatarURL)!`
- Multiple force unwraps: `text!.first!`
- Network parsing: `try! JSONSerialization.jsonObject(with: data!)`
- **Impact**: App crashes when nil values encountered

#### 3. **Poor Variable Naming**
- Single letter variables: `t`, `u`, `l`, `e`, `gs`, `st`
- Unclear abbreviations and poor naming conventions
- Global variables: `g`, `isAppRunning`, `π`
- **Impact**: Code becomes unreadable and unmaintainable

#### 4. **Memory Leaks**
- Timers never invalidated (commented out cleanup)
- Strong reference cycles in closures
- **Impact**: Memory usage grows until app crash

#### 5. **Magic Numbers**
- Hard-coded values: `42`, `3.14159`, `1000`, `100`
- No constants or meaningful names
- **Impact**: Hard to maintain and understand

#### 6. **Global State & Singletons**
- Mutable global variables throughout
- Overuse of singletons with public mutable state
- **Impact**: Unpredictable behavior, hard to test

#### 7. **Boolean Traps**
- Functions with multiple boolean parameters
- `doSomething(_ flag: Bool, _ other: Bool, _ third: Bool)`
- **Impact**: Confusing API, easy to make mistakes

#### 8. **Functions Doing Too Much**
- Single functions handling multiple responsibilities
- Mixed concerns (network, file, UI, math operations)
- **Impact**: Hard to test, debug, and maintain

#### 9. **Poor Error Handling**
- Using `try!` instead of proper error handling
- Force casting: `response as! HTTPURLResponse`
- **Impact**: App crashes instead of graceful error handling

#### 10. **Side Effects in Wrong Places**
- Heavy work in initializers
- Side effects in computed properties
- Modifying global state unexpectedly
- **Impact**: Unpredictable performance and behavior

### ✅ Clean Version:

Switch to `main` branch to see the properly implemented version with:
- Proper memory management with `[weak self]`
- Safe optional handling instead of force unwrapping
- Clear, descriptive variable names
- Proper error handling
- Clean architecture
- Modern Swift patterns

## Project Structure

```
GitHubExplorer/
├── Models/
│   └── GitHubUser.swift
├── Services/
│   ├── Protocols/
│   │   └── GitHubServiceProtocol.swift
│   └── GitHubService.swift
├── ViewModels/
│   └── UserSearchViewModel.swift 
├── Utils/
│   └── NetworkUtilities.swift 
└── ContentView.swift 
```

## Technical Stack

- **Language**: Swift 5.9+
- **Framework**: SwiftUI
- **Architecture**: MVVM
- **Concurrency**: async/await
- **Dependency Management**: SPM

---
