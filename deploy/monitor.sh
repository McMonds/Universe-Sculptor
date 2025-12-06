#!/bin/bash
# Monitor Planet 9 Historical Solver on Oracle Cloud

echo "=== Planet 9 Solver Status ==="
echo ""

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q planet9_solver; then
    echo "Status: RUNNING ✓"
else
    echo "Status: STOPPED ✗"
    exit 1
fi

echo ""
echo "--- Latest Logs (last 30 lines) ---"
docker logs --tail 30 planet9_solver

echo ""
echo "--- Resource Usage ---"
docker stats planet9_solver --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo "--- Snapshots Generated ---"
ls -lht ~/planet9_results/snapshots/*.h5 2>/dev/null | head -5 || echo "No snapshots yet"

echo ""
echo "--- Disk Usage ---"
du -sh ~/planet9_results

echo ""
echo "To view live logs: docker logs -f planet9_solver"
