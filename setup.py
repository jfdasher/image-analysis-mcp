"""Setup configuration for pip installation."""

from setuptools import setup, find_packages

setup(
    name="image-analysis-mcp",
    version="1.0.0",
    description="MCP server for comprehensive read-only image analysis",
    author="Jim Dasher",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12,<3.14",
    install_requires=[
        "fastmcp>=1.0.0",
        "numpy>=2.0.0,<2.3",
        "opencv-python>=4.10.0",
        "pillow>=10.2.0",
        "rawpy>=0.25.0",
        "scikit-image>=0.24.0",
        "exifread>=3.0.0",
        "scikit-learn>=1.5.0",
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
