import os
import json
import base64
import subprocess
from ProjectUtils.ePICUtils.editxml_local import create_xml

def run_func_simreco(parameters, job_id, p, eta_point_x, eta_point_y, p_eta_min,p_eta_max,radiator, particle, num_particles=1500, output_file_name=None):
    print(f"start run_func, job_id: {job_id}")

    print("start to create xml")
    create_xml(parameters, job_id)
    print("finished to create xml")
    p_eta_point = [p,[p_eta_min,p_eta_max], radiator,eta_point_x,eta_point_y]
    if output_file_name:
        output_root_name = output_file_name
    else:
        p = p_eta_point[0]
        eta_min = p_eta_point[1][0]
        eta_max = p_eta_point[1][1]
        output_root_name = f"recon_scan_{job_id}_{particle}_p_{p}_eta_{eta_min}_{eta_max}.root"

    shell_command = [
        "python3", os.path.join(os.environ["AIDE_HOME"], "ProjectUtils/ePICUtils/runTestsAndObjectiveCalc_local_sep_simreco.py"),
        str(job_id), str(num_particles),
        base64.b64encode(bytes(json.dumps(p_eta_point), 'ascii')),
        particle, output_root_name
    ]
    commandout = subprocess.run(shell_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = commandout.returncode
    output = commandout.stdout.decode('utf-8') if commandout.stdout else ""
    error = commandout.stderr.decode('utf-8') if commandout.stderr else ""

    print(f"{job_id} run command: {shell_command}")
    print(f"Return code: {return_code}")
    print(f"stdout:\n{output}")
    print(f"stderr:\n{error}")

    if return_code != 0:
        print("Simulation/Reconstruction step failed.")

    return return_code
