# Claude Development & Verification Guidelines

This file contains critical constraints that Claude MUST read, internalize, and execute on every single interaction within this ERP project.

## 1. Core Behavioral Principles (Anti-Hallucination)
- **Zero Speculation**: NEVER guess or assume the existence of APIs, database columns, variables, or framework methods. If you are unsure, you MUST use tools to read the source code or ask the user.
- **Strict Verification**: Before outputting any block of code, you must mentally execute it. Verify that all referenced components are imported and valid in the current context.
- **Acknowledge Ignorance**: It is highly encouraged to say "I don't know" or "I need more context" rather than producing untested or hallucinated code.

## 2. Mandatory Pre-Generation Self-Check Checklist
Whenever you are tasked with creating, modifying, or refactoring code, you MUST complete this internal checklist before showing the final result:
1. **Dependency Check**: Are all imported packages, functions, and types explicitly defined in this project?
2. **Context Alignment**: Does this change break any existing variables or assumptions in the current file?
3. **Logic Consistency**: Review the generated loop, condition, or logic. Is there any edge case (e.g., null pointer, undefined, empty array) that will cause a runtime crash?
4. **Syntax Correctness**: Manually parse the brackets, commas, semicolons, and language-specific syntax of the code you just generated to ensure ZERO syntax errors.

## 3. Response Formatting Constraints
- **Provide Direct Answers**: Avoid robotic introductory filler phrases like "Sure, I can help you with that" or "Based on your project...". Go straight to the solution or explanation.
- **Explain "Why", Not Just "What"**: When making a non-trivial logic change, briefly explain the core reason behind your implementation choice to prevent unintended bugs.
- **Language**: Always respond in Simplified Chinese (简体中文).
