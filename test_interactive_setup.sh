#!/bin/bash
# Test script to demonstrate interactive credential input

echo "🧪 Testing Interactive Credential Setup"
echo "========================================"
echo ""
echo "This script demonstrates the new interactive credential feature."
echo ""
echo "The setup.sh script will now:"
echo "  1. Check if accounts.txt exists"
echo "  2. If not, prompt you to enter credentials"
echo "  3. Save credentials to accounts.txt"
echo "  4. Continue with deployment"
echo ""
echo "Let's test it!"
echo ""

# Remove existing accounts.txt for testing
rm -f accounts.txt

# Run setup with simulated input
echo "Running setup.sh..."
bash setup.sh

