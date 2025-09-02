import logging
import json
import getpass, os
from itertools import product

#from drich_mobo_simreco import run_func_simreco
from ProjectUtils.ePICUtils.editxml_local import create_xml

from drich_mobo_ana import run_func_analy

from ax.core.parameter_constraint import ParameterConstraint
from ax.core.parameter import RangeParameter,ParameterType

def constraint_ax(constraints,parameters):
    # constraint_dict: Dict[str,float], bound: float
    constraint_list = []
    for c in constraints:
        param_dict = {}
        param_list = constraints[c]["parameters"]
        for param in parameters:
            if param in param_list:
                param_dict[param] = constraints[c]["weights"][param_list.index(param)]
            else:
                param_dict[param] = 0
        print("param dict: ", param_dict, " param_list: ", param_list)
        constraint_list.append( ParameterConstraint(param_dict,constraints[c]["bound"]) )
    return constraint_list
        

# define global parameters. It will generate a list of parameters working together with hyperparameters.
# For a group of hyperparameters, we may need to evaluate different types of events, then in the final
# step to merge the results.
# [{'eta_points': 0.1, 'particles': 'pi+'},
#  {'eta_points': 0.1, 'particles': 'kaon+'},
#  {'eta_points': 0.2, 'particles': 'pi+'},
#  {'eta_points': 0.2, 'particles': 'kaon+'}]
global_parameters = {
    
    "particles": ["pi+"],
    #"eta_points": [0.1, 0.2]
    "p": [15], 
    "eta_point_x": [0.02457205],
    "eta_point_y": [0.00878185],
    "p_eta_min": [1.5],
    "p_eta_max": [2.0],
    "radiator": [0] #could be 0 or 1
    #p_eta_point: [0, 0.02457205, 0.00878185],
    
}

#just keep it like global variable.....
n_evts_per_job = 100
n_tot_evts = 200
# Define your objective function
def objective_function_step_simreco(*, particles, p,eta_point_x, eta_point_y, p_eta_min, p_eta_max, radiator,**parameters):
    import base64,subprocess
    print("start to create xml")
    job_id = "0_0_0"
    create_xml(parameters,job_id)
    p_eta_point = [p,[p_eta_min,p_eta_max],radiator,eta_point_x,eta_point_y]
    print("Content of the p_eta_points ",p_eta_point)
    print ("Number of events ",n_evts_per_job)
    output_file_name = "recon_file.root"
    shell_command = [
        "python3", os.path.join(os.environ["AIDE_HOME"], "ProjectUtils/ePICUtils/runTestsAndObjectiveCalc_local_sep_simreco.py"),
        str(job_id), str(n_evts_per_job),
        base64.b64encode(bytes(json.dumps(p_eta_point), 'ascii')),
        particles, output_file_name
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
    else:
        print("Simulation/Reconstruction step succeeded.")
    
    
def objective_function_step_ana(*, particles, p, eta_point_x, eta_point_y, p_eta_min, p_eta_max, radiator, input_file_names,**parameters):
    import base64
    import numpy as np
    import subprocess
    ret = {}
    p_eta_point = [p,[p_eta_min,p_eta_max],radiator,eta_point_x,eta_point_y]
    jfilename = "input_files.json"
    job_id = "0_0_0"
    num_particles = n_evts_per_job
    with open(jfilename,"w") as f:
        json.dump({"input_files":input_file_names},f)
        
    # read the json content back to make sure it has proper information
    with open(jfilename,"r") as f:
        j_data = json.load(f)
    print("Printing the json content from objective_function_step_ana ",j_data)
    
    shell_command = [
        "python3", os.path.join(os.environ["AIDE_HOME"],
                    "ProjectUtils/ePICUtils/runTestsAndObjectiveCalc_local_sep_analy.py"),
        str(job_id), str(num_particles),
        base64.b64encode(bytes(json.dumps(p_eta_point), 'ascii')),
        particles, " ", jfilename
    ]
    print("shell Command ",shell_command)
    commandout = subprocess.run(shell_command,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = commandout.returncode
    output = commandout.stdout.decode('utf-8') if commandout.stdout else ""
    error = commandout.stderr.decode('utf-8') if commandout.stderr else ""

    print(f"ana func Return code: {return_code}")
    print(f"ana func stdout:\n{output}")
    print(f"ana func stderr:\n{error}")
    
    if return_code!=0:
        print("Analysis step failed")

    path = os.path.join(os.environ["AIDE_WORKDIR"], "log/results", f"drich-mobo-out_{job_id}.npz")
    results = np.load(path, allow_pickle=True)
    print(f"objective_function_step_ana: results:: {results}") 
    ret = {k: results[k].tolist() for k in results}
    print(f"objective_function_step_ana: ret:: {ret}")
    return ret
    


def objective_function_step_final(*,ret,**parameters):
    print(f"step_final global_parameters: {global_parameters}")
    print(f"step_final results :{ret}")
    return ret
    #return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2 + xyz_sum * 0.1}


# This file will be imported to load the objective function at remote sites in PanDA
# to avoid excuting the whole file, __name__ == "__main__" must be used.
# There is another way to only ship the codes of the objective function to remote sites.
# However, if this objective function calls some other functions, this way of only shipping
# the function codes will not work.

def get_user_name():
    rucio_account = os.environ.get('RUCIO_ACCOUNT', None)
    if rucio_account:
        return rucio_account

    username = getpass.getuser()
    return username
    
if __name__ == "__main__":
    # move imports here
    # so the remote execution will not import these libraries

    import argparse
    from ProjectUtils.config_editor import *
    
    parser = argparse.ArgumentParser(description="Optimization, dRICH")
    parser.add_argument('-n', '--name', help='workflow name', type=str, default='drich-mobo')
    parser.add_argument('-c', '--config', 
                        help='Optimization configuration file', 
                        type = str, required = True)
    parser.add_argument('-d', '--detparameters', 
                        help='Detector parameter configuration file', 
                        type = str, required = True)

    args = parser.parse_args()

    config = ReadJsonFile(args.config)
    detconfig = ReadJsonFile(args.detparameters)
    
    from ax.service.ax_client import AxClient, ObjectiveProperties
    from scheduler import AxScheduler, PanDAiDDSRunner, JobLibRunner
    from scheduler.utils.common import setup_logging
    from scheduler.job.job import JobType
    from scheduler.job.multi_steps_job import MultiStepsFunction


    search_space = [
    {
        "name": name,
        "type": "range",
        "bounds": [
            float(detconfig["parameters"][name]["lower"]),
            float(detconfig["parameters"][name]["upper"])
        ],
        "value_type": "float",
    }
    for name in detconfig["parameters"]
    ]
    
    setup_logging(log_level="debug")

    logging.debug("setup ax client")
    # Initialize Ax client
    ax_client = AxClient()

    logging.info("Creating experiment")

    # Define your parameter space
    ax_client.create_experiment(
        name="drich_mobo_multistep",
        parameters=search_space,
        objectives={"objective": ObjectiveProperties(minimize=True)},
    )

    logging.info("defining objectives")

    # PanDA attributes
    init_env = [
        "source /cvmfs/unpacked.cern.ch/registry.hub.docker.com/fyingtsai/eic_xl:24.11.1/opt/conda/setup_mamba.sh;"
        "source /cvmfs/unpacked.cern.ch/registry.hub.docker.com/fyingtsai/eic_xl:24.11.1/opt/conda/dRICH-MOBO//MOBO-tools/setup_new.sh;"
        "command -v singularity &> /dev/null || export SINGULARITY=/cvmfs/oasis.opensciencegrid.org/mis/singularity/current/bin/singularity;"
        "export AIDE_HOME=$(pwd);"
        "export PWD_PATH=$(pwd);"
        'export SINGULARITY_OPTIONS="--bind /cvmfs:/cvmfs,$(pwd):$(pwd)"; '
        "export SIF=/cvmfs/singularity.opensciencegrid.org/eicweb/eic_xl:24.11.1-stable; export SINGULARITY_BINDPATH=/cvmfs,/afs; "
        "env; "
    ]
    
    init_env = " ".join(init_env)
    username = get_user_name()
    
    dataset_name_prefix = "user."+username+".drich_mobo_multistep" 
    panda_attrs = {
        "name": dataset_name_prefix,
        "init_env": init_env,
        "cloud": "US",
        "queue": "BNL_PanDA_1",  # BNL_OSG_PanDA_1, BNL_PanDA_1
        "source_dir": None,  # used to upload files in the source directory to PanDA, which will be used for the remote jobs.
                             # None is the current directory.
        "source_dir_parent_level": 1,
        "exclude_source_files": [
            r"(^|/)\.[^/]+",    # file starts with "."
            "doc*", "DTLZ2*", ".*json", ".*log", "work", "log", "OUTDIR",
            "calibrations", "fieldmaps", "gdml", "EICrecon-drich-mobo",
            "eic-software", "epic-geom-drich-mobo", "irt", "share", "back*",
            "__pycache__", ".ipynb_checkpoints"
        ],
        "max_walltime": 3600,
        "core_count": 1,
        "total_memory": 4000,
        "enable_separate_log": True,
        "job_dir": None,
    }

    #"user.wguan.my_experiment"

    # Create a runner
    runner = PanDAiDDSRunner(**panda_attrs)
    logging.info(f"created runner: {runner}")

    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    logging.info(f"created scheduler: {scheduler}")

    panda_idds_runner = PanDAiDDSRunner(**panda_attrs)

    objective_function = MultiStepsFunction(
        objective_funcs={
            "simreco": {
                "func": objective_function_step_simreco, #objective_function_step_simreco,
                "job_type": JobType.FUNCTION,
                "runner": panda_idds_runner,
                "return_func_results": False,    # here the outputs are in dataset, so no need to wait for function outputs
                "with_output_dataset": True,
                "output_file": "recon_file.root",
                # if global parameters are used, please add '#global_parameter_key' to
                # the dataset name. PanDA-iDDS will automatically replace it to different
                # keys based on the global parameters. Otherwise, all files with different
                # global parameters will be in the same dataset.
                "output_dataset": f"{dataset_name_prefix}.simreco.#global_parameter_key.#job_id",
                "num_events": n_tot_evts,
                "num_events_per_job": n_evts_per_job,
            },
            "ana": {
                "func": objective_function_step_ana,
                "job_type": JobType.FUNCTION,
                "runner": panda_idds_runner,
                "with_input_datasets": True,
                # Here the dataset name should be the same dataset name of the previous step.
                # PanDA-iDDS will get the list of files in the input dataset and create an
                # additional argument "input_file_names=<file_list_in_dataset>".
                # So the function objective_function_step_ana must have a placeholder argument
                # for 'input_file_names'. You can use any other names instead of 'input_file_names'.
                "input_datasets": {"input_file_names": f"{dataset_name_prefix}.simreco.#global_parameter_key.#job_id"},
            },
            "final": {
                "func": objective_function_step_final,
                "job_type": JobType.FUNCTION,
                "runner": JobLibRunner(n_jobs=-1),
                "parent_result_parameter_name": "ret",      # will add a parameter xyz=<get_parent_results> to the func
            },
        },
        deps={
            "final": {"parent": "ana", "dep_type": "results", "dep_map": "all2one"},
            "ana": {"parent": "simreco", "dep_type": "datasets", "dep_map": "one2one"},    # depends on the dataset. It will use rucio to manage the datasets.
        },
        global_parameters=global_parameters,
        global_parameters_steps=["simreco", "ana"],
        final="final",    # if final is not set, it will use the last step in objective_funcs.
                          # The final step will set its result as the job's result
    )

    # Set the objective function
    scheduler.set_objective_function(objective_function)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=1)
    print("Best parameters:", best_params)
