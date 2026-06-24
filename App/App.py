import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_and_install(package):
    """Check if a package is installed and install it if not."""
    spec = importlib.util.find_spec(package)
    if spec is None:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{package} installed successfully!")
    else:
        print(f"{package} is already installed.")

def check_pyqt_conflict():
    """Check if both PyQt5 and PyQt6 are installed."""
    try:
        import PyQt5
        import PyQt6
        print("️ WARNING: Both PyQt5 and PyQt6 are installed!")
        print("This will cause conflicts with PyInstaller.")
        response = input("Do you want to uninstall PyQt5? (y/n): ").lower()
        if response in ['y', 'yes']:
            print("Uninstalling PyQt5...")
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "PyQt5", "-y"])
            print("PyQt5 uninstalled successfully!")
            return True
        else:
            print("Continuing with both packages (may cause issues)...")
            return False
    except ImportError:
        # One or both are not installed
        try:
            import PyQt6
            print(" PyQt6 is installed (good for your application)")
            return True
        except ImportError:
            print("PyQt6 is not installed (will install it)")
            return True
        except:
            return True

def create_exe():
    """Create an executable from Execute.py using PyInstaller."""
    
    print("=" * 60)
    print("Building Compressive Strength Predictor Executable")
    print("=" * 60)
    
    # Define paths
    current_dir = Path(__file__).parent
    script_path = current_dir / "Execute.py"
    exe_name = "CCS_Predictor"
    
    # Check if Execute.py exists
    if not script_path.exists():
        print(f"ERROR: {script_path} not found!")
        print("Please ensure Execute.py is in the same directory as this script.")
        return False
    
    print(f"Found source script: {script_path}")
    
    # Check for PyQt conflict
    print("\nChecking for Qt binding conflicts...")
    check_pyqt_conflict()
    
    # Check and install required packages
    print("\nChecking required packages...")
    required_packages = ['pyinstaller', 'pandas', 'numpy', 'matplotlib']
    
    for package in required_packages:
        check_and_install(package)
    
    # Install PyQt6 specifically (since your code uses PyQt6)
    check_and_install('PyQt6')
    
    # Additional packages that might be needed
    check_and_install('scikit-learn')
    check_and_install('scipy')
    
    print("\n" + "=" * 60)
    print("Starting PyInstaller build process...")
    print("=" * 60)
    
    # PyInstaller command with explicit PyQt5 exclusion
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', exe_name,
        '--distpath', str(current_dir),
        '--workpath', str(current_dir / 'build'),
        '--specpath', str(current_dir),
        '--clean',
        '--noconfirm',
        '--exclude', 'PyQt5',  # Explicitly exclude PyQt5
        '--exclude', 'PyQt5.QtCore',
        '--exclude', 'PyQt5.QtGui',
        '--exclude', 'PyQt5.QtWidgets',
        str(script_path)
    ]
    
    # Check if model file exists and add it to the bundle
    model_file = current_dir / "ccs_model.pkl"
    if model_file.exists():
        print(f"Found model file: {model_file}")
        cmd.extend(['--add-data', f'{str(model_file)};.'])
    else:
        print("WARNING: ccs_model.pkl not found!")
        print("The executable will need the model file in the same directory.")
    
    # Add hidden imports for common packages
    hidden_imports = [
        'sklearn',
        'sklearn.ensemble',
        'sklearn.tree',
        'sklearn.utils._weight_vector',
        'sklearn.utils._typedefs',
        'scipy._lib.messagestream',
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.np_datetime',
        'numpy.core._dtype_ctypes'
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    print(f"\nRunning command: {' '.join(cmd[:10])}...")  # Show first 10 args
    print("\nThis may take a few minutes...")
    
    try:
        # Run PyInstaller
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            if "ERROR" in line or "error" in line.lower():
                print(f"\n ERROR: {line.strip()}")
            elif "WARNING" in line:
                print(f"️  WARNING: {line.strip()}")
            elif "INFO" in line:
                # Only show some INFO messages to avoid clutter
                if "Analysis" in line or "Processing" in line or "Building" in line:
                    if "Processing standard module hook" not in line:  # Skip most hook messages
                        print(f"   {line.strip()}")
        
        process.wait()
        
        print("\n" + "=" * 60)
        
        if process.returncode == 0:
            print(" Build completed successfully!")
            
            # Check for output
            exe_path = current_dir / f"{exe_name}.exe"
            if exe_path.exists():
                print(f"\n Executable created: {exe_path}")
                print(f"Size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
                
                # Clean up temporary files
                spec_file = current_dir / f"{exe_name}.spec"
                build_dir = current_dir / "build"
                
                if spec_file.exists():
                    spec_file.unlink()
                    print(f"Cleaned up: {spec_file}")
                
                if build_dir.exists():
                    import shutil
                    shutil.rmtree(build_dir)
                    print(f"Cleaned up: {build_dir}")
                
                print("\n" + "=" * 60)
                print(" Build complete! You can now run CCS_Predictor.exe")
                print("=" * 60)
                return True
            else:
                print("ERROR: Executable was not created!")
                return False
        else:
            print(f"\n Build failed with return code: {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        return False

def create_spec_file_alternative():
    """Create a spec file manually as an alternative approach."""
    current_dir = Path(__file__).parent
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['Execute.py'],
    pathex=[{repr(str(current_dir))}],
    binaries=[],
    datas=[
        ('ccs_model.pkl', '.')
    ] if os.path.exists('ccs_model.pkl') else [],
    hiddenimports=[
        'sklearn',
        'sklearn.ensemble',
        'sklearn.tree',
        'sklearn.utils._weight_vector',
        'sklearn.utils._typedefs',
        'scipy._lib.messagestream',
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.np_datetime',
        'numpy.core._dtype_ctypes'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['PyQt5'],  # Explicitly exclude PyQt5
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CCS_Predictor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Clean up build directory after successful build
import shutil
import os
if os.path.exists('build'):
    shutil.rmtree('build')
'''
    
    spec_file = current_dir / "CCS_Predictor.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    print(f"Created spec file: {spec_file}")
    
    # Build using the spec file
    cmd = ['pyinstaller', '--clean', '--noconfirm', str(spec_file)]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build with spec file failed: {e}")
        return False

def main():
    """Main function."""
    print("Compressive Strength Predictor - EXE Builder")
    print("=" * 60)
    print()
    
    print("Choose build method:")
    print("1. Automatic build (recommended)")
    print("2. Manual spec file build (if automatic fails)")
    print("3. Uninstall PyQt5 and try again")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        success = create_exe()
    elif choice == '2':
        success = create_spec_file_alternative()
    elif choice == '3':
        # Uninstall PyQt5 explicitly
        print("Uninstalling PyQt5...")
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "PyQt5", "-y"])
        print("PyQt5 uninstalled. Now trying automatic build...")
        success = create_exe()
    else:
        print("Invalid choice. Using automatic build...")
        success = create_exe()
    
    if success:
        print("\n Build process completed successfully!")
    else:
        print("\n Build process failed!")
        
        # Suggest manual steps
        print("\nIf the build continues to fail, try these manual steps:")
        print("1. Uninstall PyQt5: pip uninstall PyQt5 -y")
        print("2. Install only PyQt6: pip install PyQt6")
        print("3. Run PyInstaller manually:")
        print("   pyinstaller --onefile --windowed --name CCS_Predictor --exclude PyQt5 Execute.py")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()
