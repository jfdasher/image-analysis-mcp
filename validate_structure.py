"""Simple validation script to check code structure."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Checking imports...")

try:
    from image_analysis_mcp import utils
    print("✓ utils module imported")
except ImportError as e:
    print(f"✗ Failed to import utils: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp.analysis import metadata
    print("✓ metadata module imported")
except ImportError as e:
    print(f"✗ Failed to import metadata: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp.analysis import histogram
    print("✓ histogram module imported")
except ImportError as e:
    print(f"✗ Failed to import histogram: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp.analysis import tonal
    print("✓ tonal module imported")
except ImportError as e:
    print(f"✗ Failed to import tonal: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp.analysis import color
    print("✓ color module imported")
except ImportError as e:
    print(f"✗ Failed to import color: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp.analysis import spatial
    print("✓ spatial module imported")
except ImportError as e:
    print(f"✗ Failed to import spatial: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp.analysis import frequency
    print("✓ frequency module imported")
except ImportError as e:
    print(f"✗ Failed to import frequency: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp.analysis import preview
    print("✓ preview module imported")
except ImportError as e:
    print(f"✗ Failed to import preview: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp import tools
    print("✓ tools module imported")
except ImportError as e:
    print(f"✗ Failed to import tools: {e}")
    sys.exit(1)

try:
    from image_analysis_mcp import server
    print("✓ server module imported")
except ImportError as e:
    print(f"✗ Failed to import server: {e}")
    sys.exit(1)

print("\n✓ All modules imported successfully!")
print("\nStructure validation complete.")
