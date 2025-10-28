"""Setup configuration for pip installation."""

from setuptools import setup, find_packages

setup(
    name="image-analysis-mcp",
    version="1.0.0",
    description="MCP server for comprehensive read-only image analysis",
    author="Jim Dasher",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "fastmcp>=1.0.0",
        "numpy>=1.26.0",
        "opencv-python>=4.9.0",
        "pillow>=10.2.0",
        "rawpy>=0.19.0",
        "scikit-image>=0.22.0",
        "exifread>=3.0.0",
        "scikit-learn>=1.3.0",
    ],
    entry_points={
        "console_scripts": [
            "image-analysis-mcp=image_analysis_mcp.server:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "black>=24.0.0",
            "mypy>=1.8.0",
        ],
    },
)
