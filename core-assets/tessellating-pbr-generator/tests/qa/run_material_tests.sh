#!/bin/bash
# Run tests for all example materials

echo "🧪 Testing Tessellating PBR Texture Generator with Example Materials"
echo "=================================================================="

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create output directory
mkdir -p tests/qa/material_test_output

# Test each material configuration
materials=("stone_wall" "polished_metal" "wood_planks" "fabric")

for material in "${materials[@]}"; do
    echo ""
    echo "Testing $material..."
    echo "-------------------"
    
    # Run with example config
    python main.py \
        -c "examples/materials/${material}.json" \
        -r "512x512" \
        -o "tests/qa/material_test_output/${material}" \
        --preview \
        --debug
    
    # Check exit code
    if [ $? -eq 0 ]; then
        echo "✅ $material generation successful"
    else
        echo "❌ $material generation failed"
    fi
done

echo ""
echo "Testing with CLI arguments only..."
echo "---------------------------------"

# Test direct CLI usage
python main.py \
    -m "concrete" \
    -r "1024x1024" \
    -o "tests/qa/material_test_output/cli_concrete" \
    -t diffuse normal roughness height ao \
    --preview

echo ""
echo "Running comprehensive QA tests..."
echo "--------------------------------"

# Run comprehensive test suite
python tests/qa/test_comprehensive.py

echo ""
echo "🏁 All tests complete!"
echo "Check tests/qa/material_test_output/ for generated textures"
echo "Check tests/qa/test_output/qa_report.json for detailed results"