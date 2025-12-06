#!/bin/bash
# Sync results from Oracle Cloud to local machine

# Usage: ./sync_results.sh <oracle_ip>

if [ -z "$1" ]; then
    echo "Usage: $0 <oracle_ip_address>"
    exit 1
fi

ORACLE_IP=$1
LOCAL_DIR="./oracle_results"

echo "=== Syncing Results from Oracle Cloud ==="
echo "Source: ubuntu@$ORACLE_IP:~/planet9_results/"
echo "Dest: $LOCAL_DIR"
echo ""

mkdir -p "$LOCAL_DIR"

rsync -avz --progress \
    ubuntu@$ORACLE_IP:~/planet9_results/ \
    "$LOCAL_DIR/"

echo ""
echo "✓ Sync complete"
echo "Results saved to: $LOCAL_DIR"
echo ""
echo "To generate time-lapse from snapshots:"
echo "  python src/viz/time_lapse.py"
