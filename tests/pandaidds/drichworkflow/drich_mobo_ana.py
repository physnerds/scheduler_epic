import os
import json
import base64
import numpy as np
import subprocess

def get_outcome_value_for_completed_job(parameters, job_id, eta_points, particle, num_particles):
    path = os.path.join(os.environ["AIDE_WORKDIR"], "log/results", f"drich-mobo-out_{job_id}.npz")
    results = np.load(path, allow_pickle=True)
    return {k: results[k].tolist() for k in results}


def run_func_analy(parameters,job_id, eta_point_x, eta_point_y, p_eta_min,p_eta_max,radiator,particle, num_particles=1500, input_file_name=None):
    print(f"start run_func_analy, job_id: {job_id}")

    is_tuple = isinstance(input_file_name, (list, tuple))
    input_root_name = input_file_name[0] if is_tuple else input_file_name
    p_eta_point = [p,[p_eta_min,p_eta_max], radiator,eta_points[0],eta_points[1]]
    if not input_root_name:
        #p, (eta_min, eta_max) = p_eta_point
        eta_min = p_eta_point[1][0]
        eta_max = p_eta_point[1][1]
        
        input_root_name = f"recon_scan_{job_id}_{particle}_p_{p}_eta_{eta_min}_{eta_max}.root"

    shell_command = [
        "python3", os.path.join(os.environ["AIDE_HOME"], "ProjectUtils/ePICUtils/runTestsAndObjectiveCalc_local_sep_analy.py"),
        str(job_id), str(num_particles),
        base64.b64encode(bytes(json.dumps(p_eta_point), 'ascii')),
        particle, input_root_name
    ]

    if is_tuple:
        jfilename = "input_files.json"
        with open(jfilename, "w") as f:
            json.dump({"input_files": input_file_name}, f)
        shell_command.append(jfilename)

    commandout = subprocess.run(shell_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = commandout.returncode
    output = commandout.stdout.decode('utf-8') if commandout.stdout else ""
    error = commandout.stderr.decode('utf-8') if commandout.stderr else ""

    print(f"{job_id} run command: {shell_command}")
    print(f"Return code: {return_code}")
    print(f"stdout:\n{output}")
    print(f"stderr:\n{error}")

    if return_code != 0:
        print("Analysis step failed.")

    return get_outcome_value_for_completed_job(parameters, job_id, p_eta_point, particle, num_particles)
