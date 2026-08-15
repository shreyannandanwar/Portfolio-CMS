#!/bin/bash

# Test GitHub API with and without token

echo "======================================"
echo "Testing GitHub API Rate Limits"
echo "======================================"
echo

# Test without token
echo "1. Without Token (Anonymous):"
echo "------------------------------"
RESPONSE=$(curl -s -I https://api.github.com/users/shreyannandanwar | grep -i "x-ratelimit")
echo "$RESPONSE"
echo

# Test with token (if GITHUB_TOKEN is set)
if [ -n "$GITHUB_TOKEN" ]; then
    echo "2. With Token (Authenticated):"
    echo "------------------------------"
    RESPONSE=$(curl -s -I -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/users/shreyannandanwar | grep -i "x-ratelimit")
    echo "$RESPONSE"
    echo
else
    echo "2. GITHUB_TOKEN not set. Run:"
    echo "   export GITHUB_TOKEN=your_token_here"
    echo "   Then run this script again."
    echo
fi

echo "======================================"
echo "Rate Limit Reference:"
echo "  - Anonymous: 60 requests/hour"
echo "  - Authenticated: 5,000 requests/hour"
echo "======================================"
