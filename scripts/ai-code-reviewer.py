#!/usr/bin/env python3
"""
ai-code-reviewer.py - Enhanced iOS/Swift Edition

Comprehensive AI-powered code reviewer specifically optimized for iOS/Swift projects.
Combines both inline code review comments and high-level architectural analysis.

ENHANCED FEATURES FOR iOS/SWIFT:
1. Specialized Swift/SwiftUI/UIKit detection and categorization
2. Modern iOS development best practices (iOS 17+, Swift 5.9+)
3. Comprehensive state management review (@Observable, @State, @Binding)
4. Memory management and retain cycle detection
5. Accessibility and inclusive design compliance
6. Security and privacy regulation adherence
7. Performance optimization recommendations
8. App Store and Human Interface Guidelines compliance
9. Modern SwiftUI patterns and navigation
10. Async/await and concurrency best practices

CORE CAPABILITIES:
1. Line-by-line code review with inline PR comments (similar to ios-ai-reviewer.js)
2. High-level architectural analysis with summary comment (from swift-analyzer.py)
3. Specialized handling for SwiftUI, UIKit, test files, and configuration files
4. Intelligent file filtering to exclude binaries and generated files
5. Enhanced iOS project structure detection and context analysis

SUPPORTED REVIEW AREAS:
- Code Quality & Swift Best Practices
- Architecture & Design Patterns (MVVM, Clean Architecture)
- Memory Management & Performance
- Security & Privacy Compliance
- Accessibility & Inclusivity
- Modern iOS Development (SwiftUI, async/await)
- Testing & Quality Assurance
- Platform Compliance (App Store, HIG)

Based on comprehensive Swift/iOS cursor rules and modern development practices.

Features:
1. Line-by-line code review with inline PR comments (similar to ios-ai-reviewer.js)
2. High-level architectural analysis with summary comment (from swift-analyzer.py)
3. Specialized handling for SwiftUI, UIKit, test files, and configuration files
4. Intelligent file filtering to exclude binaries and generated files
"""

import os
import re
import json
import time
import requests
from openai import OpenAI
from typing import List, Dict, Any, Optional, Set

# Environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL_INLINE = os.getenv('OPENAI_MODEL', 'gpt-4o')  # For inline reviews
MODEL_SUMMARY = 'gpt-4o-mini'  # For architectural summary (more cost-effective)
PR_NUMBER = os.getenv('PR_NUMBER')
REPO = os.getenv('GITHUB_REPOSITORY')
COMMIT_SHA = os.getenv('PR_HEAD_SHA')

if not all([GITHUB_TOKEN, OPENAI_API_KEY, PR_NUMBER, REPO, COMMIT_SHA]):
    print("❌ Missing required environment variables")
    exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# GitHub API headers
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

OWNER, REPO_NAME = REPO.split('/')

# File patterns to exclude from review - Enhanced for iOS/Swift projects
EXCLUDE_PATTERNS = [
    # Xcode project files
    '.xcodeproj', '.xcworkspace', '.xcassets', '.pbxproj', '.xcuserstate',
    '.xcscheme', '.xcbkptlist', '.xcscmblueprint', '.xccheckout',

    # Interface Builder files
    '.storyboard', '.xib', '.nib',

    # Configuration and metadata
    '.plist', '.entitlements', '.mobileprovision', '.p12', '.cer',

    # Package management
    '.lock', 'Package.resolved', 'Package.pins',

    # Media files
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.ico', '.icns',
    '.mp3', '.mp4', '.m4v', '.mov', '.wav', '.aiff',

    # Documentation and text files
    '.md', '.txt', '.rtf', '.pdf',

    # Data files
    '.json', '.yaml', '.yml', '.xml', '.csv', '.sqlite', '.db',

    # Generated files
    'Generated', 'Derived', 'DerivedData', '.derived',
    'xcuserdata', 'UserInterfaceState.xcuserstate',

    # Archive and compressed files
    '.zip', '.tar', '.gz', '.rar', '.7z',

    # IDE and editor files
    '.swp', '.tmp', '~', '.bak',

    # Frameworks and libraries
    '.framework', '.dylib', '.a',

    # Build artifacts
    '.ipa', '.app', '.dSYM'
]

# Rate limiting configuration
API_DELAY = 2.0  # Seconds between API calls to avoid rate limits
MAX_COMMENTS_PER_FILE = 5  # Limit comments per file to avoid spam

def rate_limited_request(func):
    """Decorator to add rate limiting to API requests."""
    def wrapper(*args, **kwargs):
        time.sleep(API_DELAY)  # Wait before making request
        return func(*args, **kwargs)
    return wrapper

def fetch_pr_files() -> List[Dict[str, Any]]:
    """Fetch the list of files changed in the pull request."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error fetching PR files: {response.text}")
        return []
    return response.json()

def should_review_file(file_data: Dict[str, Any]) -> bool:
    """Determine if a file should be reviewed based on exclude patterns and status."""
    filename = file_data['filename']

    # Skip removed files
    if file_data['status'] == 'removed':
        print(f"⏭️  Skipping {filename} (file removed)")
        return False

    # Skip files matching exclude patterns
    if any(pattern in filename for pattern in EXCLUDE_PATTERNS):
        print(f"⏭️  Skipping {filename} (matches exclude pattern)")
        return False

    # Must have a patch (diff content)
    if not file_data.get('patch'):
        print(f"⏭️  Skipping {filename} (no patch content)")
        return False

    return True

def is_ios_project_file(filename: str) -> bool:
    """Check if file is part of iOS project structure for enhanced categorization."""
    ios_project_indicators = [
        'Package.swift',           # Swift Package Manager
        'project.pbxproj',         # Xcode project file
        'Info.plist',             # iOS app configuration
        'AppDelegate.swift',       # iOS app delegate
        'SceneDelegate.swift',     # iOS scene delegate
        'ContentView.swift',       # SwiftUI main view
        'LaunchScreen.storyboard', # Launch screen
        '.entitlements',          # App entitlements
        'Podfile',                # CocoaPods
        'Cartfile',               # Carthage
        'fastlane',               # Deployment automation
        '.xcconfig',              # Xcode configuration
        'GoogleService-Info.plist', # Firebase
        'Localizable.strings'      # Localization
    ]

    return any(indicator in filename for indicator in ios_project_indicators)

def get_file_context_info(filename: str, content: str) -> Dict[str, Any]:
    """Extract additional context information from iOS files for better review."""
    context = {
        'is_ios_project': is_ios_project_file(filename),
        'uses_async_await': 'async ' in content or 'await ' in content,
        'uses_combine': 'import Combine' in content or 'Publisher' in content,
        'uses_core_data': 'import CoreData' in content or 'NSManagedObject' in content,
        'uses_swift_data': 'import SwiftData' in content or '@Model' in content,
        'uses_networking': any(keyword in content for keyword in ['URLSession', 'Alamofire', 'NetworkReachability']),
        'has_ui_tests': 'XCUIApplication' in content or 'XCUIElement' in content,
        'has_unit_tests': 'XCTestCase' in content or '@testable' in content,
        'uses_accessibility': any(keyword in content for keyword in ['accessibilityLabel', 'accessibilityHint', 'VoiceOver']),
        'uses_localization': 'NSLocalizedString' in content or 'String(localized:' in content,
        'file_size_lines': len(content.split('\n')),
        'complexity_indicators': {
            'nested_closures': content.count('{ ') > 3,
            'long_functions': any(line.strip().startswith('func ') and len(line) > 80 for line in content.split('\n')),
            'many_parameters': ')(' in content.replace(') (', ')('),  # Method chaining detection
        }
    }

    return context

def categorize_file(filename: str, content: str) -> str:
    """Categorize file type for targeted review prompts with enhanced detection."""
    # Get additional context
    context = get_file_context_info(filename, content)

    # Enhanced test detection
    if (re.search(r'Test\.swift$', filename) or
        '/Tests/' in filename or
        'Test' in filename or
        'Mock' in filename or
        'Stub' in filename or
        context['has_ui_tests'] or
        context['has_unit_tests'] or
        any(keyword in content for keyword in ['XCTest', '@testable', 'XCTAssert', 'XCUIApplication'])):
        return 'Test'

    # Enhanced SwiftUI detection
    if filename.endswith('.swift'):
        swiftui_indicators = [
            'import SwiftUI', 'SwiftUI.', 'View', '@State', '@Binding',
            '@ObservableObject', '@Observable', '@StateObject', '@EnvironmentObject',
            'NavigationView', 'NavigationStack', 'VStack', 'HStack', 'ZStack',
            'Button', 'Text', 'Image', 'ScrollView', 'List', 'Form',
            'NavigationSplitView', 'Grid', 'LazyVStack', 'LazyHStack'
        ]
        if any(indicator in content for indicator in swiftui_indicators):
            return 'SwiftUI'

        # Enhanced UIKit detection
        uikit_indicators = [
            'import UIKit', 'UIView', 'UIViewController', 'UITableView',
            'UICollectionView', 'UIButton', 'UILabel', 'UIImageView',
            'viewDidLoad', 'viewWillAppear', 'IBOutlet', 'IBAction',
            'UINavigationController', 'UITabBarController', 'UIStoryboard'
        ]
        if any(indicator in content for indicator in uikit_indicators):
            return 'UI'

        # Special case for main app files
        if filename in ['AppDelegate.swift', 'SceneDelegate.swift', 'App.swift']:
            return 'SwiftUI' if '@main' in content else 'UI'

        # General Swift file
        return 'Swift'

    # Enhanced configuration file detection
    config_files = [
        '.plist', '.xcconfig', '.json', '.yaml', '.yml',
        'Package.swift', 'Podfile', 'Cartfile', '.entitlements'
    ]
    if any(filename.endswith(ext) or ext in filename for ext in config_files):
        return 'Config'

    return 'Swift'

def parse_diff_for_review(patch: str) -> tuple[List[Dict[str, Any]], Set[int]]:
    """Parse diff patch to extract context and valid line numbers for comments."""
    lines = patch.split('\n')
    context_lines = []
    valid_comment_lines = set()  # Track which lines can receive comments
    new_line_number = 0

    for line in lines:
        if line.startswith('@@'):
            # Extract starting line number for new file
            match = re.search(r'@@ .* \+(\d+)(,\d+)? @@', line)
            if match:
                new_line_number = int(match.group(1)) - 1
        elif line.startswith('+'):
            # New added line - these can receive comments
            new_line_number += 1
            content = line[1:]  # Remove '+' prefix
            context_lines.append({
                'line_number': new_line_number,
                'content': content,
                'type': 'added'
            })
            valid_comment_lines.add(new_line_number)  # Mark as valid for comments
        elif line.startswith(' '):
            # Context line (unchanged)
            new_line_number += 1
            context_lines.append({
                'line_number': new_line_number,
                'content': line[1:],  # Remove ' ' prefix
                'type': 'context'
            })
        # Skip removed lines (don't increment line number)

    return context_lines[:300], valid_comment_lines  # Limit context to avoid huge prompts

def get_system_message(category: str) -> str:
    """Get specialized system message based on file category with comprehensive Swift/iOS guidelines."""

    base_instructions = """You are a senior iOS developer expert with 10+ years of Swift, SwiftUI, and iOS development experience.
Follow Apple's Human Interface Guidelines and Swift best practices. Focus on code quality, performance, security, and maintainability.

## CORE SWIFT/iOS PRINCIPLES:
- Use Swift's latest features (Swift 5.9+, iOS 17+) and protocol-oriented programming
- Prefer value types (structs) over classes when appropriate
- Follow SOLID principles and clean architecture patterns
- Use strong type system with proper optionals and Result types
- Prioritize async/await over completion handlers
- Always handle errors gracefully with structured error types
- Follow Apple's naming conventions: camelCase for properties/methods, PascalCase for types
- Use descriptive names following Apple style guide

## PERFORMANCE & MEMORY:
- Profile with Instruments for memory leaks and performance bottlenecks
- Implement lazy loading for large datasets and images
- Use weak references to prevent retain cycles
- Optimize network requests with proper caching strategies
- Handle background task processing efficiently
- Implement proper state restoration
- Use @MainActor for UI-updating code paths

## SECURITY & PRIVACY:
- Encrypt sensitive data and use Keychain for secure storage
- Implement certificate pinning for network security
- Use biometric authentication when appropriate
- Follow App Transport Security guidelines
- Validate all inputs and sanitize user data
- Comply with privacy regulations and App Store guidelines
- Never log sensitive information

## ACCESSIBILITY & INCLUSIVITY:
- Support VoiceOver with proper accessibility labels and hints
- Implement Dynamic Type for text scaling
- Support dark mode and high contrast modes
- Handle all screen sizes and orientations (including iPad)
- Test with accessibility features enabled
- Provide alternative text for images and icons
- Ensure minimum touch target sizes (44pt)

## TESTING & QUALITY ASSURANCE:
- Write comprehensive unit tests with XCTest
- Implement UI tests for critical user flows with XCUITest
- Use Test-Driven Development (TDD) where appropriate
- Test edge cases, error scenarios, and performance
- Maintain high test coverage (>80%)
- Use SwiftUI previews for rapid UI testing
- Test with different device configurations

## ARCHITECTURE & PATTERNS:
- Use MVVM architecture with SwiftUI
- Implement proper dependency injection
- Follow single responsibility principle
- Use protocol extensions for shared functionality
- Structure projects: Features/, Core/, UI/, Resources/
- Separate business logic from UI logic
- Use Repository pattern for data access"""

    if category == 'SwiftUI':
        return base_instructions + """

## SWIFTUI SPECIFIC GUIDELINES:
### State Management:
- Use @Observable for reference types (avoid @ObservableObject/@StateObject in new code)
- Use @State only for view-local state management
- Use @Binding for two-way data flow between parent/child views
- Use @Environment for app-wide state and dependency injection
- Pass dependencies via initializers, not as global singletons
- Use @Bindable properties within @Observable classes for direct binding

### UI Architecture:
- Prefer SwiftUI over UIKit for new development
- Use NavigationStack with type-safe navigation for iOS 16+
- Use NavigationSplitView for multi-column layouts on larger screens
- Implement navigationDestination() for programmatic navigation
- Create reusable custom ViewModifiers for shared styling
- Extract complex views into smaller, focused components

### Layout & Design:
- Use Grid for complex, flexible layouts
- Use ViewThatFits for adaptive interfaces
- Apply containerRelativeFrame() for responsive sizing
- Use LazyVStack/LazyHStack for performance with large lists
- Implement proper ScrollView with scrollTargetBehavior()
- Use contentMargins() for consistent spacing
- Support all device sizes with adaptive layouts

### Data Flow & Performance:
- Use Swift Data with @Query for data persistence (iOS 17+)
- Implement lazy loading with stable, identifiable items
- Use TaskGroup for concurrent operations
- Minimize view body computations with @ViewBuilder
- Use id() modifier to control view identity and animations
- Avoid frequent @State updates that trigger re-renders

### Animations & Interactions:
- Use .animation(value:) for state-driven animations
- Implement Phase Animations for complex transitions
- Use .symbolEffect() for SF Symbol animations
- Add .sensoryFeedback() for haptic responses
- Use gesture system for custom touch interactions
- Ensure animations respect reduced motion settings

### Modern SwiftUI Features:
- Use SF Symbols 5 with variable colors and weights
- Implement containerShape() for custom hit testing
- Use scrollTargetLayout() for precise scroll positioning
- Apply visualEffect() for blur and material effects
- Use scrollBounceBehavior() to control scroll physics
- Implement sheet(item:) for data-driven presentations"""

    elif category == 'UI':
        return base_instructions + """

## UIKIT SPECIFIC GUIDELINES:
### View Controller Best Practices:
- Follow view controller lifecycle properly (viewDidLoad, viewWillAppear, etc.)
- Implement proper memory management with weak references
- Use delegation pattern appropriately with weak references
- Avoid massive view controllers - extract logic into separate classes
- Handle view controller transitions smoothly
- Implement proper state restoration

### Auto Layout & Interface:
- Use Auto Layout programmatically or with Interface Builder
- Create adaptive layouts that work on all device sizes
- Implement proper safe area handling
- Use stack views for simple layouts
- Handle keyboard appearance/dismissal properly
- Ensure proper content inset adjustments

### Modern UIKit Features:
- Use UICollectionView compositional layouts
- Implement UICollectionView diffable data sources
- Use UIContextMenuConfiguration for context menus
- Apply UIBehavioralConfiguration for modern cell styling
- Use UIAction for button configurations
- Implement proper UIScene lifecycle management

### Integration Guidelines:
- Use UIHostingController to embed SwiftUI in UIKit
- Use UIViewRepresentable to wrap UIKit components in SwiftUI
- Handle data flow between UIKit and SwiftUI properly
- Maintain consistent navigation patterns across frameworks
- Ensure proper memory management in integration scenarios"""

    elif category == 'Test':
        return base_instructions + """

## TESTING SPECIFIC GUIDELINES:
### Unit Testing:
- Write focused, fast, and isolated unit tests
- Use descriptive test method names (test_givenCondition_whenAction_thenExpectation)
- Test business logic separately from UI logic
- Mock external dependencies and network calls
- Test edge cases, error conditions, and boundary values
- Use XCTAssert family of assertions appropriately
- Group related tests using test suites

### UI Testing:
- Test critical user flows and navigation paths
- Use accessibility identifiers for reliable element selection
- Test across different device configurations and orientations
- Verify proper keyboard handling and input validation
- Test accessibility features (VoiceOver, Dynamic Type)
- Use page object pattern for maintainable UI tests
- Test error states and recovery scenarios

### Performance Testing:
- Write performance tests for critical code paths
- Use XCTMeasure for performance benchmarking
- Test memory usage and leak detection
- Validate app launch time and responsiveness
- Test with large datasets and stress conditions

### Test Architecture:
- Use dependency injection for testable code
- Create test doubles (mocks, stubs, fakes) appropriately
- Use factory methods for test data creation
- Maintain test data isolation between test runs
- Use continuous integration for automated testing
- Implement snapshot testing for UI regression detection"""

    elif category == 'Config':
        return base_instructions + """

## CONFIGURATION & PROJECT GUIDELINES:
### Project Structure:
- Organize files logically (Features/, Core/, Resources/, Tests/)
- Use proper target membership for files
- Configure build settings appropriately for Debug/Release
- Set up proper code signing and provisioning profiles
- Use xcconfig files for build configuration management
- Implement proper scheme configuration

### Dependencies & Package Management:
- Use Swift Package Manager for dependency management
- Pin dependency versions for reproducible builds
- Regularly audit and update dependencies for security
- Minimize external dependencies where possible
- Use local packages for shared code between targets
- Configure proper dependency resolution strategies

### Build & Deployment:
- Set up proper CI/CD pipelines
- Configure proper build optimization flags
- Implement code signing automation
- Use fastlane for deployment automation
- Set up proper crash reporting and analytics
- Configure proper App Store metadata and screenshots

### Security Configuration:
- Configure App Transport Security appropriately
- Set up proper keychain access groups
- Configure background execution properly
- Set up proper URL scheme handling
- Configure proper push notification certificates
- Implement proper certificate pinning configuration"""

    else:  # Generic Swift
        return base_instructions + """

## GENERAL SWIFT GUIDELINES:
### Language Features:
- Use optionals properly with nil-coalescing and optional chaining
- Prefer immutable (let) over mutable (var) declarations
- Use computed properties and property observers appropriately
- Implement proper custom operators only when beneficial
- Use generics and associated types for type safety
- Leverage protocol extensions for default implementations

### Concurrency & Async Programming:
- Use async/await for asynchronous operations
- Use TaskGroup for concurrent operations
- Handle cancellation properly with Task.isCancelled
- Use actors for thread-safe shared state
- Avoid blocking the main thread with heavy computations
- Use proper error propagation with throws/async throws

### Data Management:
- Use Codable for JSON serialization/deserialization
- Implement proper data validation and sanitization
- Use UserDefaults only for simple preferences
- Implement proper data persistence strategies
- Use Core Data or Swift Data for complex data models
- Handle data migration properly between app versions

### Networking & APIs:
- Use URLSession with async/await for network requests
- Implement proper error handling for network failures
- Use proper HTTP status code handling
- Implement request/response caching strategies
- Use proper authentication mechanisms (OAuth, JWT)
- Validate SSL certificates and implement certificate pinning"""

async def review_file_inline(file_data: Dict[str, Any]) -> None:
    """Perform inline code review for a single file."""
    filename = file_data['filename']
    patch = file_data['patch']

    print(f"🔍 Reviewing {filename} for inline comments...")

    # Read full file content for better categorization
    full_content = ''
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            full_content = f.read()
    except (FileNotFoundError, UnicodeDecodeError):
        full_content = patch  # Fallback to patch content

    # Categorize file and parse diff
    category = categorize_file(filename, full_content)
    context_info = get_file_context_info(filename, full_content)
    context_lines, valid_comment_lines = parse_diff_for_review(patch)

    if not context_lines:
        print(f"⚠️  No context lines found for {filename}")
        return

    print(f"📝 Found {len(valid_comment_lines)} valid lines for comments in {filename} (Category: {category})")

    # Build context for AI - focus on added lines
    added_lines = [line for line in context_lines if line['type'] == 'added']
    if not added_lines:
        print(f"⚠️  No added lines to review in {filename}")
        return

    diff_context = '\n'.join([
        f"Line {line['line_number']}: {line['content']}"
        for line in context_lines
    ])

    # Construct messages with enhanced context
    system_msg = get_system_message(category)

    # Create context summary for better AI understanding
    context_summary = f"""
FILE CONTEXT:
- Category: {category}
- File size: {context_info['file_size_lines']} lines
- iOS Project file: {context_info['is_ios_project']}
- Uses async/await: {context_info['uses_async_await']}
- Uses SwiftData: {context_info['uses_swift_data']}
- Uses Core Data: {context_info['uses_core_data']}
- Has networking: {context_info['uses_networking']}
- Has accessibility features: {context_info['uses_accessibility']}
- Has localization: {context_info['uses_localization']}
- Complexity indicators: {context_info['complexity_indicators']}"""

    # Enhanced user message with comprehensive iOS/Swift context
    user_msg = f"""Review the changes in Swift/iOS file "{filename}" (Category: {category}).
{context_summary}

REVIEW FOCUS AREAS:
1. **Code Quality**: Swift best practices, naming conventions, type safety
2. **Architecture**: MVVM patterns, dependency injection, separation of concerns
3. **Performance**: Memory management, lazy loading, async operations
4. **Security**: Data validation, secure storage, privacy compliance
5. **Accessibility**: VoiceOver support, Dynamic Type, inclusive design
6. **Modern Swift**: Latest language features, async/await, @Observable
7. **iOS Guidelines**: Human Interface Guidelines, App Store compliance

PROVIDE SPECIFIC FEEDBACK ON:
- State management patterns (@State, @Binding, @Observable)
- Memory leaks and retain cycles (weak/unowned references)
- Error handling and edge cases
- Thread safety and @MainActor usage
- Navigation patterns and deep linking
- Accessibility implementations
- Performance optimizations
- Security vulnerabilities
- Code maintainability and readability

Return a JSON array with objects containing "line" (number) and "comment" (string) fields.
Focus on the most critical issues. Maximum {MAX_COMMENTS_PER_FILE} comments.
Be specific and actionable in your suggestions.

Valid line numbers for comments: {sorted(list(valid_comment_lines))}

FILE CHANGES:
```
{diff_context}
```

Prioritize issues by severity: Security > Performance > Bugs > Best Practices > Style"""

    try:
        # Call OpenAI API with rate limiting
        print(f"🤖 Calling OpenAI API for {filename}...")
        time.sleep(1)  # Brief delay before API call

        response = client.chat.completions.create(
            model=MODEL_INLINE,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.2,
            max_tokens=800  # Reduced to limit response size
        )

        ai_content = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            # Handle potential markdown code blocks
            if ai_content.startswith('```'):
                ai_content = re.sub(r'^```\w*\n?', '', ai_content)
                ai_content = re.sub(r'\n?```$', '', ai_content)

            suggestions = json.loads(ai_content)

            if not isinstance(suggestions, list):
                print(f"⚠️  Non-array response for {filename}")
                return

            # Filter and limit suggestions
            valid_suggestions = []
            for suggestion in suggestions:
                if not all(key in suggestion for key in ['line', 'comment']):
                    continue

                line_number = suggestion['line']

                # Validate line number is in valid comment lines
                if line_number not in valid_comment_lines:
                    print(f"⚠️  Skipping invalid line {line_number} for {filename}")
                    continue

                valid_suggestions.append(suggestion)

                # Limit number of comments per file
                if len(valid_suggestions) >= MAX_COMMENTS_PER_FILE:
                    break

            print(f"📝 Posting {len(valid_suggestions)} valid comments for {filename}")

            # Post each valid suggestion as inline comment
            for i, suggestion in enumerate(valid_suggestions):
                line_number = suggestion['line']
                comment_text = suggestion['comment'].strip()

                # Ensure proper sentence ending
                if comment_text and not comment_text.endswith(('.', '!', '?')):
                    comment_text += '.'

                # Post comment to GitHub with rate limiting
                print(f"📤 Posting comment {i+1}/{len(valid_suggestions)} for {filename}:{line_number}")
                await post_inline_comment(filename, line_number, comment_text)

        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON response for {filename}: {e}")

    except Exception as e:
        print(f"❌ Error reviewing {filename}: {e}")

@rate_limited_request
async def post_inline_comment(filename: str, line_number: int, comment: str) -> None:
    """Post an inline comment to the GitHub PR with rate limiting."""
    payload = {
        'body': comment,
        'commit_id': COMMIT_SHA,
        'path': filename,
        'line': line_number,
        'side': 'RIGHT'
    }

    url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/pulls/{PR_NUMBER}/comments"

    try:
        response = requests.post(url, headers=HEADERS, json=payload)

        if response.status_code == 201:
            print(f"✅ Posted comment on {filename}:{line_number}")
        elif response.status_code == 422:
            print(f"⚠️  Invalid line number {line_number} for {filename} (line not in diff)")
        elif response.status_code == 403:
            print(f"🚫 Rate limited - waiting longer before next request...")
            time.sleep(10)  # Wait longer if rate limited
        else:
            print(f"⚠️  Failed to post comment on {filename}:{line_number} - {response.status_code}")

    except Exception as e:
        print(f"❌ Exception posting comment on {filename}:{line_number}: {str(e)}")

def generate_architectural_summary(files: List[Dict[str, Any]]) -> str:
    """Generate high-level architectural analysis summary."""
    print("🏗️  Generating architectural analysis...")

    # Create a more detailed file analysis for the prompt
    file_details = []
    for file_data in files:
        filename = file_data['filename']
        additions = file_data.get('additions', 0)
        deletions = file_data.get('deletions', 0)
        file_details.append(f"- {filename} (+{additions}/-{deletions} lines)")

    file_list = "\n".join(file_details)

    prompt = f"""You are an expert iOS developer and architect reviewing a pull request for a Swift/iOS application.

**Files Changed ({len(files)} files):**
{file_list}

Please provide a **comprehensive, structured analysis** covering:

## 📋 Pull Request Summary
- Brief overview of the changes and their purpose
- Impact assessment (High/Medium/Low) on app functionality and user experience
- Compatibility with iOS versions and device types

## 🏗️ Architecture & Design Patterns
- SwiftUI vs UIKit usage and integration patterns
- MVVM architecture implementation and data flow
- Dependency injection and separation of concerns
- Protocol-oriented programming usage
- Design pattern adherence (Repository, Factory, Observer, etc.)
- Clean Architecture and SOLID principles compliance

## 🧠 Memory Management & Performance
- Retain cycle detection and weak/unowned reference usage
- @MainActor usage for UI updates and thread safety
- Async/await implementation and Task management
- Lazy loading strategies for UI and data
- Performance impact of state management (@Observable, @State, @Binding)
- Memory optimization opportunities
- Network request efficiency and caching strategies

## 🎨 SwiftUI & Modern iOS Development
- State management best practices (@Observable vs @StateObject)
- Navigation patterns (NavigationStack, NavigationSplitView)
- Layout system usage (Grid, LazyVStack, ViewThatFits)
- Animation and interaction implementations
- SF Symbols and visual effect usage
- Modern iOS 17+ feature adoption

## 🔒 Security & Privacy Compliance
- Data encryption and Keychain usage
- Input validation and sanitization
- Network security (certificate pinning, ATS)
- Biometric authentication implementation
- Privacy compliance (data collection, tracking)
- App Transport Security configuration
- Secure coding practices

## ♿ Accessibility & Inclusivity
- VoiceOver support and accessibility labels
- Dynamic Type implementation
- High contrast and dark mode support
- Touch target size compliance (44pt minimum)
- Accessibility identifier usage for testing
- Inclusive design considerations
- Support for assistive technologies

## 🧪 Testing & Quality Assurance
- Unit test coverage and quality
- UI test implementation for critical flows
- Test architecture and dependency injection
- Mock and stub usage for external dependencies
- Performance test coverage
- Accessibility testing implementation
- Edge case and error scenario coverage

## 📱 iOS Platform Compliance
- Human Interface Guidelines adherence
- App Store submission readiness
- Platform-specific feature usage
- Device compatibility considerations
- iOS version support strategy
- Background task handling
- Push notification implementation

## ⚡ Action Items & Recommendations
### 🔴 **Critical Issues** (Must Fix Before Merge)
1. Security vulnerabilities or data exposure risks
2. Memory leaks or retain cycles
3. Thread safety violations

### 🟡 **Important Improvements** (Should Address Soon)
1. Performance optimizations
2. Accessibility enhancements
3. Architecture improvements

### 🟢 **Enhancement Opportunities** (Future Considerations)
1. Code organization and maintainability
2. Modern iOS feature adoption
3. Developer experience improvements

## 🎯 Overall Assessment
- **Code Quality Score**: X/10 (based on Swift best practices)
- **iOS Compliance Score**: X/10 (based on platform guidelines)
- **Security Score**: X/10 (based on security best practices)
- **Accessibility Score**: X/10 (based on inclusive design)
- **Merge Readiness**: ✅ Ready / ⚠️ Needs Minor Changes / ❌ Major Revisions Required

### Key Strengths
- Highlight positive aspects of the implementation

### Areas for Improvement
- Specific recommendations for enhancement

### Next Steps
- Concrete action items with priority levels

Format as **clear Markdown** with emojis, bullet points, and specific code examples where helpful.
Focus on actionable feedback that will improve the iOS app's quality, security, and user experience."""

    try:
        print("🤖 Calling OpenAI API for architectural analysis...")
        response = client.chat.completions.create(
            model=MODEL_SUMMARY,
            messages=[
                {"role": "system", "content": "You are an expert Swift/SwiftUI architect and code reviewer with 10+ years of iOS development experience."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,  # Increased for more comprehensive analysis
            temperature=0.1   # Lower temperature for more consistent analysis
        )

        summary_content = response.choices[0].message.content.strip()
        print("✅ Successfully generated architectural analysis")
        return summary_content

    except Exception as e:
        error_msg = f"❌ Error generating architectural analysis: {str(e)}"
        print(error_msg)

        # Return a basic fallback summary
        return f"""## 🏗️ AI Architectural Analysis

**Note**: Error occurred during analysis generation.

### Files Reviewed
{file_list}

### Status
Analysis could not be completed due to: {str(e)}

Please review the inline comments for detailed feedback on individual files."""

@rate_limited_request
def post_summary_comment(content: str) -> bool:
    """Post the architectural summary as a PR comment. Returns True if successful."""
    print("📝 Posting architectural summary to PR...")

    # Enhanced header with more context
    full_comment = f"""# 🤖 AI Code Review Summary

{content}

---
> 💡 **Note**: This analysis was generated by AI and should be reviewed by human developers.
>
> 🔍 **Inline Comments**: Check individual file diffs for detailed line-by-line feedback.
>
> 📅 **Generated**: {os.getenv('GITHUB_SHA', 'Unknown commit')[:7]}"""

    url = f"https://api.github.com/repos/{OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/comments"
    payload = {"body": full_comment}

    try:
        response = requests.post(url, headers=HEADERS, json=payload)

        if response.status_code == 201:
            print("✅ Successfully posted architectural analysis summary to PR")
            return True
        elif response.status_code == 403:
            print("🚫 Rate limited when posting summary - waiting and retrying...")
            time.sleep(15)  # Wait longer for summary

            # Retry once
            response = requests.post(url, headers=HEADERS, json=payload)
            if response.status_code == 201:
                print("✅ Successfully posted summary after retry")
                return True
            else:
                print(f"❌ Failed summary retry: {response.status_code}")
                return False
        else:
            print(f"❌ Failed to post summary comment: {response.status_code} - {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Exception posting summary comment: {str(e)}")
        return False

async def main():
    """Main execution function."""
    print("🚀 Starting comprehensive AI code review...")
    print(f"⚙️  Rate limiting: {API_DELAY}s between requests, max {MAX_COMMENTS_PER_FILE} comments per file")

    # Fetch PR files
    files = fetch_pr_files()
    if not files:
        print("ℹ️  No files found in PR")
        return

    print(f"📊 Total files in PR: {len(files)}")

    # Filter files for review
    files_to_review = [f for f in files if should_review_file(f)]

    if not files_to_review:
        print("ℹ️  No files to review after filtering")
        # Still post a summary even if no files to review
        summary = """## 🏗️ AI Code Review Summary

**Status**: No reviewable code files found in this PR.

The PR may contain only:
- Binary files (images, assets)
- Configuration files
- Documentation files

No code review comments were generated."""
        post_summary_comment(summary)
        return

    print(f"📁 Files selected for review: {[f['filename'] for f in files_to_review]}")

    # 1. Perform inline reviews for each file
    print("\n🔍 Starting inline code reviews...")
    total_comments_posted = 0

    for i, file_data in enumerate(files_to_review, 1):
        print(f"\n📄 Processing file {i}/{len(files_to_review)}: {file_data['filename']}")
        try:
            await review_file_inline(file_data)

            # Add delay between files to avoid overwhelming GitHub API
            if i < len(files_to_review):  # Don't delay after last file
                print(f"⏸️  Waiting {API_DELAY}s before next file...")
                time.sleep(API_DELAY)

        except Exception as e:
            print(f"❌ Error processing {file_data['filename']}: {str(e)}")
            continue

    # 2. Generate and post architectural summary (always attempt this)
    print(f"\n🏗️  Generating architectural summary for {len(files_to_review)} files...")
    try:
        print("⏸️  Waiting before summary generation...")
        time.sleep(3)  # Extra wait before summary

        summary = generate_architectural_summary(files_to_review)
        success = post_summary_comment(summary)

        if not success:
            print("⚠️  Retrying summary post with simplified content...")
            # Fallback: post a simple summary
            simple_summary = f"""## 🏗️ AI Code Review Summary

**Files Reviewed**: {len(files_to_review)} files
- {chr(10).join([f"• {f['filename']}" for f in files_to_review])}

**Status**: Analysis completed with rate limiting. Check inline comments for specific feedback.

*Note: Simplified summary due to API limitations.*"""

            time.sleep(5)  # Wait before retry
            post_summary_comment(simple_summary)

    except Exception as e:
        print(f"❌ Critical error in summary generation: {str(e)}")
        # Always try to post something
        error_summary = f"""## 🏗️ AI Code Review Summary

**Error**: Summary generation failed: {str(e)}

**Files in PR**: {len(files_to_review)} reviewable files found.

Please check individual file comments for detailed feedback."""

        time.sleep(3)
        post_summary_comment(error_summary)

    print(f"\n✅ Code review process complete!")
    print(f"📈 Processed {len(files_to_review)} files with rate limiting")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())