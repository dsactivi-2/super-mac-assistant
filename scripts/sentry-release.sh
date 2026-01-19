#!/bin/bash
# Sentry Release Script for super-mac-assistant
set -e

export SENTRY_ORG="activi-0m"
export SENTRY_PROJECT="super-mac-assistant"

if [ -z "$SENTRY_AUTH_TOKEN" ]; then
    echo "❌ SENTRY_AUTH_TOKEN not set"
    exit 1
fi

VERSION=$(sentry-cli releases propose-version 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo "1.0.0")

echo "🚀 Creating Sentry release: $VERSION"
sentry-cli releases new "$VERSION"
sentry-cli releases set-commits "$VERSION" --auto || true
sentry-cli releases finalize "$VERSION"
sentry-cli releases deploys "$VERSION" new -e production
echo "✅ Release $VERSION created!"
