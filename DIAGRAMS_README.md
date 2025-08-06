# PlantUML Diagrams for Technical Design Document

This directory contains PlantUML source files and generated diagrams for the technical design document: "Version JupyterLab UI Testing Automation - From ADAM to Browser Use Web-UI".

## Generated Diagrams

### 1. Solution Architecture (`solution_architecture.puml`)
- **PNG**: `Solution Architecture.png` (47KB)
- **SVG**: `Solution Architecture.svg` (11KB)
- **Description**: High-level architecture showing the local automation solution components

### 2. Detailed Solution Workflow (`detailed_workflow.puml`)
- **PNG**: `Detailed Solution Workflow.png` (49KB)
- **SVG**: `Detailed Solution Workflow.svg` (12KB)
- **Description**: Step-by-step workflow of the automation process

### 3. ADAM vs Local Solution Comparison (`solution_comparison.puml`)
- **PNG**: `ADAM vs Local Solution Comparison.png` (55KB)
- **SVG**: `ADAM vs Local Solution Comparison.svg` (13KB)
- **Description**: Side-by-side comparison of blocked ADAM approach vs implemented local solution

## Usage Instructions

### Regenerating Diagrams
```bash
# Make sure PlantUML is installed
brew install plantuml

# Run the generation script
./generate_diagrams.sh

# Or generate manually
plantuml -tpng *.puml    # Generate PNG files
plantuml -tsvg *.puml    # Generate SVG files
```

### Embedding in Documents
- **For web documents**: Use SVG files for better scalability
- **For presentations**: Use PNG files for better compatibility
- **For print documents**: Use PNG files at high resolution

### File Formats
- **PNG**: Better for presentations and documents with fixed layouts
- **SVG**: Better for web pages and scalable documents
- **PlantUML source**: Editable source files for future modifications

## Technical Details

- **PlantUML Version**: 1.2025.4
- **Java Runtime**: OpenJDK 24.0.2
- **Generated on**: macOS with Homebrew installation
- **Color Scheme**: Professional blue/green theme with clear visual hierarchy

## Modification Guide

To modify the diagrams:
1. Edit the corresponding `.puml` file
2. Run `./generate_diagrams.sh` to regenerate images
3. Verify the output in both PNG and SVG formats
4. Update this README if new diagrams are added
