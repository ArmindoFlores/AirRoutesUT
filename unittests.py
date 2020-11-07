import argparse
import os
import random
import subprocess
import time

from colored import stylize, attr, fg
from gooey import Gooey, GooeyParser

wsl = r"C:\Windows\Sysnative\wsl.exe"

filenameValidator = {
    'validator': {
    'test': 'exec("import os") is None and eval("os.path.isfile(user_input)")',
    'message': 'Must be a valid filename'
    }
}

dirValidator = {
    'validator': {
    'test': 'exec("import os") is None and eval("os.path.isdir(user_input)")',
    'message': 'Must be a valid directory'
    }
}

def print_warning(text):
    print(stylize(text, fg("yellow")))
    
def print_error(text):
    print(stylize(text, fg("red")))

def test(exe, tdir, sdir, use_wsl):
    test_files = list(map(lambda n: n[:-8], [file for file in os.listdir(tdir) if file.endswith(".routes0")]))
    solution_files = list(map(lambda n: n[:-8], [file for file in os.listdir(sdir) if file.endswith(".queries")]))
    
    if len(test_files) == 0:
        print_error("Error: Couldn't find any test files")
        return
    
    if use_wsl: 
        try:
            b_path = subprocess.check_output([wsl, "wslpath", "-a", exe], shell=True).decode().strip()
            t_path = subprocess.check_output([wsl, "wslpath", "-a", tdir], shell=True).decode().strip()
            s_path = subprocess.check_output([wsl, "wslpath", "-a", sdir], shell=True).decode().strip()
        except subprocess.CalledProcessError:
            print_error("Error: Couldn't run WSL. Try disabling that option if you're using a Linux machine.")
            return
    else:
        b_path = exe
        t_path = tdir
        s_path = sdir

    tested = {}
    
    c = 0
    for file in test_files:
        c += 1
        if file not in solution_files:
            print_warning(f"Warning: Could not find solution for '{file}', skipping...")
            continue
        
        file_path = f"{t_path}/{file}.routes0"
        if os.path.isfile(f"{t_path}/{file}.queries"):
            os.remove(f"{t_path}/{file}.queries")
        error = ""
        try:
            if use_wsl:
                result = subprocess.check_output([wsl, b_path, file_path],
                                                 shell=True, 
                                                 stderr=subprocess.PIPE)
            else:
                result = subprocess.check_output([b_path, file_path], 
                                                 shell=True,
                                                 stderr=subprocess.PIPE)
        except OSError:
            print_error("Couldn't run the executable. Try enabling the WSL option if you're not running in a Linux machine.")
            return
        except subprocess.CalledProcessError:
            error = "non-0"
            print_warning("Error: Program exited with non-0 status code")
        except subprocess.TimeoutExpired:
            error = "timeout"
            print_warning("Warning: Program exceeded maximum computation time, skipping...")
        else:
            if result != b"":
                print_warning("Warning: Program output on stdout/stderr detected")
                error = str(result)[1:]
            tested[file] = error    
        print(f"Progress: {c}/{len(test_files)*2}")
        
    errors = 0
    with open("results.txt", "w") as save:
        for file in tested:
            c += 1
            
            try:
                if use_wsl:
                    subprocess.check_output([wsl, "diff", f"{t_path}/{file}.queries", f"{s_path}/{file}.queries"],
                                            shell=True,
                                            stderr=subprocess.PIPE)
                else:
                    subprocess.check_output(["diff", f"{t_path}/{file}.queries", f"{s_path}/{file}.queries"],
                                            shell=True,
                                            stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                save.write(f"{file}.routes0:")
                save.write(e.output.decode())
                save.write("\n\n")
                errors += 1
            print(f"Progress: {c}/{len(test_files)*2}")
        save.write(f"Errors: {errors}")
        
    print("Finished!")
    print(f"Errors: {errors}")
        

@Gooey(program_name='UnitTests',
       tabbed_groups=True,
       progress_regex=r"^Progress: (?P<current>\d+)/(?P<total>\d+)$",
       progress_expr="current / total * 100",
       hide_progress_msg=False,
       richtext_controls=True)
def main():
    import os
    parser = GooeyParser(description="Unit tests helper program")
    
    group1 = parser.add_argument_group("General")
    group1.add_argument("program", type=str, help="Program to run", widget="FileChooser", gooey_options=filenameValidator)
    group1.add_argument("tests", type=str, help="Tests directory", widget="DirChooser", gooey_options=dirValidator)
    group1.add_argument("solution", type=str, help="Solution directory", widget="DirChooser", gooey_options=dirValidator)
    
    group2 = parser.add_argument_group("Options")
    group2.add_argument("--wsl", help="Run program within WSL2", action="store_false")
    
    args = parser.parse_args()
    test(args.program, args.tests, args.solution, not args.wsl)

if __name__ == "__main__":
    main()
