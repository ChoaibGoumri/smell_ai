import os
import subprocess
import sys

# Mappa dei Test Case presi dal PDF "Pre_Modifications_System_Testing_Document"
# Ogni TC ha parametri specifici.
# NP (Num Projects) > 1 implica --multiple
# EP (Parallel) = true implica --parallel
# RES (Resume) = true implica --resume

TEST_CONFIG = {
    "TC1": {"args": [], "description": "Missing args (Should fail)", "expected_error": True},
    "TC2": {"args": ["--parallel", "--max_walkers", "10"], "description": "Single Project, Nested, Parallel", "input_sub": "MockDirectory2"}, 
    "TC3": {"args": ["--parallel", "--max_walkers", "5"], "description": "One File, Unreadable (Error)", "input_sub": "MockDirectory3"},
    "TC4": {"args": ["--multiple", "--parallel", "--max_walkers", "5"], "description": "Multiple Projects, General Smell"},
    "TC5": {"args": [], "description": "Empty Project (Should detect 0 smells)"},
    "TC6": {"args": [], "description": "Nested Project, No Smells"},
    "TC7": {"args": [], "description": "Project with API-Specific Smells"},
    "TC8": {"args": ["--multiple", "--parallel"], "description": "Multiple items, no smells"},
    "TC9": {"args": ["--parallel"], "description": "Single generic smell"},
    "TC10": {"args": ["--parallel", "--max_walkers", "2"], "description": "Parallel Low Walkers"},
    # ... Aggiungere altri TC se necessario. Per ora copriamo i principali scenari.
}

def run_test(tc_id, config):
    print(f"--------------------------------------------------")
    print(f"Running {tc_id}: {config['description']}")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tc_dir = os.path.join(base_dir, tc_id)
    
    # Input folder (di solito è la cartella del TC stesso o una sottocartella se specificata)
    input_dir = os.path.join(tc_dir, config.get("input_sub", ""))
    output_dir = os.path.join(tc_dir, "output")
    
    # Costruzione comando
    cmd = [sys.executable, "-m", "cli.cli_runner", "--input", input_dir, "--output", output_dir]
    cmd.extend(config.get("args", []))
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(base_dir, "../../"))
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode != 0:
            if config.get("expected_error"):
                print("✅ Test Passed (Expected Fail)")
            else:
                print(f"❌ Test Failed with return code {result.returncode}")
        else:
             print("✅ Execution Finished Successfully (Check logs for semantic correctness)")

    except Exception as e:
        print(f"❌ Exception running test: {e}")

def main():
    if len(sys.argv) > 1:
        tcs_to_run = sys.argv[1:]
    else:
        # Ordina per ID numerico se possibile, altrimenti alfabetico
        tcs_to_run = sorted(TEST_CONFIG.keys(), key=lambda x: int(x.replace("TC", "")))

    print(f"Found {len(tcs_to_run)} configured tests.")
    
    for tc_id in tcs_to_run:
        if tc_id in TEST_CONFIG:
            run_test(tc_id, TEST_CONFIG[tc_id])
        else:
            print(f"⚠️  Config for {tc_id} not found in script, skipping.")

if __name__ == "__main__":
    main()
