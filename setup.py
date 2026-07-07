from cx_Freeze import setup, Executable

# Options for the build process
options = {
    "build_exe": {
        "packages": ["os"],  # Add dependencies here (e.g., pandas, openpyxl)
        "include_files": []  # Add additional files to include
    }
}

# Define the setup
setup(
    name="Excel Merger",
    version="1.0",
    description="A tool to merge Excel files",
    options=options,
    executables=[Executable("main.py", base=None)],  # Use base="Win32GUI" for GUI apps
)