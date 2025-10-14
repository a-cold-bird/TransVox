# Contributing to TransVox

Thank you for your interest in contributing to TransVox! This document provides guidelines and instructions for contributing.

[中文版本](./CONTRIBUTING_ZH.md)

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/TransVox.git
   cd TransVox
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/a-cold-bird/TransVox.git
   ```

## Development Setup

### Backend Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128
   pip install -r requirements.txt
   pip install -e tools/index-tts
   ```

3. Download models:
   ```bash
   python Scripts/download_models.py
   python Scripts/download_nltk_data.py
   ```

4. Configure API keys:
   ```bash
   cp .env_template .env
   # Edit .env and add your API keys
   ```

5. Run environment check:
   ```bash
   python Scripts/check_environment.py
   ```

### Frontend Setup

1. Install Node.js dependencies:
   ```bash
   cd web
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Run type checking:
   ```bash
   npm run type-check
   ```

4. Run linting:
   ```bash
   npm run lint
   ```

## How to Contribute

### Areas for Contribution

1. **Bug Fixes**: Fix reported issues
2. **New Features**: Add new functionality
3. **Documentation**: Improve or translate documentation
4. **Testing**: Add or improve tests
5. **Performance**: Optimize existing code
6. **UI/UX**: Improve user interface and experience

### Before You Start

1. Check existing [Issues](https://github.com/a-cold-bird/TransVox/issues) and [Pull Requests](https://github.com/a-cold-bird/TransVox/pulls)
2. For major changes, open an issue first to discuss
3. Create a new branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Style

### Python Code

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Maximum line length: 120 characters
- Use type hints where appropriate

Example:
```python
def process_video(video_path: str, target_lang: str = "zh") -> dict:
    """
    Process video with translation and dubbing.

    Args:
        video_path: Path to input video file
        target_lang: Target language code (default: "zh")

    Returns:
        Dictionary containing processing results
    """
    # Implementation
    pass
```

### TypeScript/React Code

- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Use meaningful component and variable names
- Maximum line length: 100 characters

Example:
```typescript
interface VideoUploadProps {
  onUploadComplete: (videoPath: string) => void
  maxFileSize?: number
}

export function VideoUpload({ onUploadComplete, maxFileSize = 1000 }: VideoUploadProps) {
  // Implementation
}
```

### File Organization

- **Backend scripts**: Place in `Scripts/` directory
- **Frontend components**: Place in `web/src/components/`
- **API endpoints**: Add in `api_server.py`
- **Documentation**: Add in `docs/` directory
- **Tests**: Add in appropriate test directories

## Commit Guidelines

### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

### Examples

```
feat(tts): add IndexTTS-2 engine support

- Integrate IndexTTS-2 for zero-shot voice cloning
- Add configuration options for IndexTTS
- Update documentation

Closes #123
```

```
fix(subtitle): correct timestamp parsing error

Fixed an issue where subtitle timestamps with milliseconds
were incorrectly parsed, causing sync issues.

Fixes #456
```

## Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure tests pass**:
   ```bash
   # Backend
   python Scripts/test_system.py

   # Frontend
   cd web
   npm run type-check
   npm run lint
   ```

3. **Update documentation** if needed

4. **Commit your changes** following commit guidelines

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Go to the original TransVox repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template:
     - Description of changes
     - Related issues
     - Testing performed
     - Screenshots (if UI changes)

7. **Respond to review feedback**:
   - Address reviewer comments
   - Push additional commits if needed
   - Request re-review when ready

### PR Title Format

Use the same format as commit messages:

```
feat(component): add new feature
fix(module): correct bug
docs: update installation guide
```

## Reporting Issues

### Before Creating an Issue

1. Check if the issue already exists
2. Try the latest version
3. Check the documentation

### Issue Template

When creating an issue, include:

1. **Environment Information**:
   - OS version
   - Python version
   - CUDA version
   - GPU model

2. **Steps to Reproduce**:
   - Clear, numbered steps
   - Input files or parameters used

3. **Expected Behavior**:
   - What should happen

4. **Actual Behavior**:
   - What actually happens
   - Error messages (full traceback)

5. **Additional Context**:
   - Screenshots
   - Logs
   - Related issues

### Issue Types

- Bug Report: Something isn't working
- Feature Request: Suggest a new feature
- Documentation: Improve or clarify documentation
- Performance: Report performance issues
- Question: Ask for help or clarification

## Development Guidelines

### Testing

- Write tests for new features
- Ensure existing tests pass
- Test on different environments when possible

### Documentation

- Update documentation for new features
- Add docstrings to new functions/classes
- Update README if necessary
- Add examples for complex features

### Code Review

- Be respectful and constructive
- Explain reasoning for suggestions
- Be open to feedback
- Focus on code quality and maintainability

## Resources

- [Project Documentation](./docs/)
- [API Documentation](http://localhost:8000/docs)
- [Frontend README](./web/README.md)
- [Project Structure](./docs/PROJECT_STRUCTURE_EN.md)

## Questions?

- Open a [Discussion](https://github.com/a-cold-bird/TransVox/discussions) for general questions
- Open an [Issue](https://github.com/a-cold-bird/TransVox/issues) for bug reports or feature requests

## License

By contributing to TransVox, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to TransVox!
