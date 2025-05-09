import subprocess
import os
import shutil

def eps_to_svg_inkscape(eps_path, svg_path, quality="high"):
    """
    Converts an EPS file to SVG using Inkscape.
    First converts EPS to PDF using Ghostscript, then converts PDF to SVG using Inkscape.
    
    Args:
        eps_path: Path to input EPS file
        svg_path: Path to output SVG file
        quality: "high" or "default" - determines conversion parameters
        
    Returns:
        True on success, False on failure.
    """
    if not shutil.which("inkscape"):
        print("ERROR: Inkscape command not found. Please install Inkscape and ensure it's in your PATH.")
        return False
        
    if not shutil.which("gs"):
        print("ERROR: Ghostscript (gs) command not found. Please install Ghostscript and ensure it's in your PATH.")
        return False

    if not os.path.exists(eps_path):
        print(f"ERROR: Input EPS file not found: {eps_path}")
        return False

    try:
        # Step 1: Convert EPS to PDF using Ghostscript with improved quality
        temp_pdf = eps_path + ".temp.pdf"
        gs_cmd = [
            "gs", 
            "-dNOPAUSE", 
            "-dBATCH", 
            "-dEPSCrop",  # Crop to the EPS bounding box
            "-dPDFSETTINGS=/prepress",  # Highest quality PDF output
            "-dCompatibilityLevel=1.7",  # Use latest PDF compatibility
            "-dAutoRotatePages=/None",  # Don't rotate pages
            "-dDetectDuplicateImages=true",  # Optimize output
            "-sDEVICE=pdfwrite", 
            f"-sOutputFile={temp_pdf}", 
            eps_path
        ]
        
        print(f"Running command: {' '.join(gs_cmd)}")
        gs_result = subprocess.run(gs_cmd, capture_output=True, text=True, check=False)
        
        if gs_result.returncode != 0:
            print(f"ERROR: Ghostscript conversion failed.")
            print("STDOUT:", gs_result.stdout)
            print("STDERR:", gs_result.stderr)
            return False
            
        if not os.path.exists(temp_pdf):
            print(f"ERROR: Ghostscript ran but output PDF file not found.")
            return False
        
        # Step 2: Convert PDF to SVG using Inkscape with improved quality
        inkscape_cmd = [
            "inkscape",
            temp_pdf,
            f"--export-filename={svg_path}",
        ]
        
        # Add quality options
        if quality == "high":
            inkscape_cmd.extend([
                "--export-text-to-path",  # Convert text to paths for better preservation
                "--export-area-drawing",  # Export the drawing (not the page)
                "--export-dpi=300"        # Higher resolution
            ])
        
        print(f"Running command: {' '.join(inkscape_cmd)}")
        result = subprocess.run(inkscape_cmd, capture_output=True, text=True, check=False)

        # Clean up temporary PDF file
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)

        if result.returncode == 0:
            if os.path.exists(svg_path):
                print(f"Successfully converted '{eps_path}' to '{svg_path}' using Inkscape.")
                return True
            else:
                print(f"ERROR: Inkscape ran but output file '{svg_path}' not found.")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
        else:
            print(f"ERROR: Inkscape conversion failed for '{temp_pdf}'.")
            print(f"Return code: {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except FileNotFoundError: # Should be caught by shutil.which, but as a fallback
        print("ERROR: Command not found. Please ensure Inkscape and Ghostscript are in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def batch_convert_eps_to_svg(input_dir, output_dir, quality="high"):
    """
    Batch converts all EPS files in the input directory to SVG files in the output directory.
    Preserves the directory structure.
    
    Args:
        input_dir: The directory containing EPS files
        output_dir: The directory to save converted SVG files
        quality: "high" or "default" - quality settings for conversion
    
    Returns:
        tuple: (total_files, success_count, failed_files)
    """
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        return 0, 0, []
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    total_files = 0
    success_count = 0
    failed_files = []
    
    # Walk through input directory
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.eps'):
                # Get relative path to maintain directory structure
                rel_path = os.path.relpath(root, input_dir)
                
                # Create the output directory structure
                output_subdir = os.path.join(output_dir, rel_path)
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                
                # Prepare input and output paths
                eps_path = os.path.join(root, file)
                svg_filename = os.path.splitext(file)[0] + '.svg'
                svg_path = os.path.join(output_subdir, svg_filename)
                
                print(f"Converting {eps_path} to {svg_path}")
                total_files += 1
                
                # Perform the conversion
                if eps_to_svg_inkscape(eps_path, svg_path, quality):
                    success_count += 1
                else:
                    failed_files.append(eps_path)
    
    return total_files, success_count, failed_files

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch convert EPS files to SVG')
    parser.add_argument('--input', default='data', help='Input directory containing EPS files')
    parser.add_argument('--output', default='output', help='Output directory for SVG files')
    parser.add_argument('--quality', choices=['high', 'default'], default='high',
                        help='Quality settings for conversion')
    
    args = parser.parse_args()
    
    input_dir = args.input
    output_dir = args.output
    quality = args.quality
    
    print(f"Starting batch conversion from '{input_dir}' to '{output_dir}'")
    print(f"Using two-step conversion method with {quality} quality settings")
    
    total, successful, failed = batch_convert_eps_to_svg(input_dir, output_dir, quality)
    
    print("\nConversion Summary:")
    print(f"Total EPS files found: {total}")
    print(f"Successfully converted: {successful}")
    print(f"Failed conversions: {len(failed)}")
    
    if failed:
        print("\nFailed files:")
        for file in failed:
            print(f" - {file}")
