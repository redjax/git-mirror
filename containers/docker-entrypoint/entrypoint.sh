#!/bin/sh

echo ""
echo "Setting gituser permissions"
echo ""

# chown -R gituser:gituser /data
# chown -R gituser:gituser /home/gituser

chmod -R 700 /data

echo ""
echo "Continuing Docker boot"
echo ""

## Continue with Docker startup
exec runuser -u gituser "$@"
