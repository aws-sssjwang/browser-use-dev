#!/bin/bash

# Script to generate PNG and SVG diagrams from PlantUML files
# Usage: ./generate_diagrams.sh

echo "Generating PNG diagrams..."
plantuml -tpng solution_architecture.puml detailed_workflow.puml solution_comparison.puml

echo "Generating SVG diagrams..."
plantuml -tsvg solution_architecture.puml detailed_workflow.puml solution_comparison.puml

echo "Generated files:"
ls -la *.png *.svg

echo "Diagram generation complete!"
