#!/bin/bash

# Quick Setup Guide for Africa's Talking SMS Integration
# Run this script or follow the manual steps below

echo "SafeRoute SMS Integration Setup"
echo "================================"
echo ""

# Step 1: Install package
echo "Step 1: Installing africastalking package..."
pip install africastalking -q
echo "✓ Done"
echo ""

# Step 2: Create .env file
echo "Step 2: Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env created from template"
else
    echo "✓ .env already exists"
fi
echo ""

# Step 3: Show instructions
echo "Step 3: Configure credentials"
echo "-----"
echo "Edit .env file and add your Africa's Talking credentials:"
echo ""
echo "  AT_USERNAME=your_africastalking_username"
echo "  AT_API_KEY=your_africastalking_api_key"
echo ""
echo "Get credentials from: https://africastalking.com/account/settings/api"
echo ""

# Step 4: Test
echo "Step 4: Test the integration"
echo "-----"
echo "Run tests with:"
echo ""
echo "  python manage.py shell"
echo "  >>> from core.sms_tests import run_all_tests"
echo "  >>> run_all_tests()"
echo ""

echo "================================"
echo "Setup complete!"
echo "================================"
