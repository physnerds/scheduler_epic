import base64
import json
import numpy as np
import os
import sys
import subprocess
import signal
import time
import threading
# import math
# import uncertainties
import logging
import traceback

from typing import Any

# NEEDS TO:
# 1. run overlap check
# 2. generate p/eta scan
# 3. calculate pi-K sep
# 4. store all relevant results in drich-mobo-out_{jobid}.txt


logging.basicConfig(level=logging.INFO, format='%(asctime)s\t%(threadName)s\t%(name)s\t%(levelname)s\t%(message)s')


class SubJobManager:
    def __init__(self, p_eta_point, particle, n_part, job_id, input_name,json_fname=None):
        self.p_eta_point = p_eta_point
        self.p_eta_points = [p_eta_point]
        self.particle = particle
        self.particles = [particle]
        self.input_name = input_name
        self.json_fname = json_fname
        
        self.n_part = n_part
        self.job_id = job_id

        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        logging.info(f"SubJobManager dir_path: {self.dir_path}")
        if os.environ.get("AIDE_WORKDIR", None):
            self.output_dir = os.environ.get("AIDE_WORKDIR")
        else:
            self.output_dir = os.getcwd()
            os.environ['AIDE_WORKDIR'] = self.output_dir
        self.results_dir = os.path.join(self.output_dir,"log","results")
        os.makedirs(self.results_dir,exist_ok=True)
        self.output_name = os.path.join(self.results_dir, "drich-mobo-out_{}.npz".format(job_id))
        self.status_name = os.path.join(self.results_dir, "drich-mobo-status_{}.txt".format(job_id))
        for f in [self.output_name, self.status_name]:
            if os.path.exists(f):
                os.remove(f)

        # self.particles = ["pi+", "kaon+"]
        self.final_job_status = {}
        self.final_job_result = {}


    def runJobs(self):
        logging.info("SubJobManager ++++++ runJobs +++++++")
        for point_num, p_eta_point in enumerate(self.p_eta_points):
            # if p_eta_point not in self.final_job_status:
            #     self.final_job_status[p_eta_point] = {}
            self.final_job_status[point_num] = {}

            for particle in self.particles:
                # slurm_file = self.makeSlurmScript(p_eta_point,particle)
                # shellcommand = ["sbatch",slurm_file]

                p = p_eta_point[0]
                eta_min = p_eta_point[1][0]
                eta_max = p_eta_point[1][1]
                radiator = p_eta_point[2]

                shell_command = [os.path.join(self.dir_path, "shell_wrapper_job_local_analy.sh"),
                                 str(p), str(eta_min), str(eta_max), str(self.n_part), str(radiator), self.job_id, particle]

                if self.json_fname is not None:
                    shell_command.append(self.json_fname)

                logging.info("runTest Analy function::runjobs %s",shell_command)

                process = subprocess.run(shell_command)

                status_code = process.returncode
                logging.info(f"RunTestsAndObjective_local_sep_analy SubJobManager returncode: {status_code}")
                self.final_job_status[point_num][particle] = int(status_code)

        logging.info("SubJobManager ++++++ end runJobs +++++++")
        return

    def writeFailedObjectives(self):
        # executed when we have overlaps and want to punish this result,
        # but the trial didn't exactly "fail"
        # TODO: is this how we want to treat this?
        final_results = np.zeros(6,dtype=float)
        np.savez(self.output_name, failed_final_results=final_results)
        return

    def write_status_code(self, status_code):
        with open(self.status_name, 'w') as f:
            f.write(str(status_code))

    def retrieveResults(self):
        # when results finished, retrieve analysis script outputs
        # and calculate objectives
        logging.info("SubJobManager retrieving results")

        # results = {}
        # for i in range(len(self.p_eta_points)):
        for i, p_eta_point in enumerate(self.p_eta_points):
            # p_eta_point = self.p_eta_points[i]
            logging.info(f"SubJobManager job.{i} p_eta_point: {p_eta_point}")
            p = p_eta_point[0]
            eta_min = p_eta_point[1][0]
            eta_max = p_eta_point[1][1]
            
            for particle in self.particles:
                scan_path = os.path.join(os.environ["AIDE_WORKDIR"],
                                         "log",
                                         "results",
                                         #"recon_scan.txt"
                                    f"recon_scan_{self.job_id}_{particle}_p_{p}_eta_{eta_min}_{eta_max}.txt"
                                        )
                if not os.path.exists(scan_path):
                    logging.error(f"Missing result file {scan_path}")
                    
                
                plus_cher = np.loadtxt(scan_path)
                key = f"plus_cher_{i}_{particle}"
                self.final_job_result[key] = np.asarray(plus_cher)

        logging.info(f"SubJobManager saving results to {self.output_name}: {self.final_job_result}")
        np.savez(self.output_name, **self.final_job_result)
        logging.info("SubJobManager saved results")
        return

    def get_final_job_status(self):
        total, num_done = 0, 0
        logging.info(f"SubJobManager final_job_status: {self.final_job_status}")
        for i, p_eta_point in enumerate(self.p_eta_points):
            for particle in self.particles:
                total += 1
                if self.final_job_status[i][particle] == 0:
                    num_done += 1
        logging.info(f"SubJobManager final_job_status: num_done {num_done}, total: {total}")
        return num_done, total


def run(jobid, npart, p_eta_point, particle, input_name,json_fname=None):

    manager = SubJobManager(p_eta_point, particle, npart, jobid, input_name, json_fname)
    
    manager.runJobs()
    # manager.monitorJobs()

    manager.retrieveResults()
    num_done, total = manager.get_final_job_status()
    if num_done < total:
        logging.info("some job failed, flag as failure")
        manager.writeFailedObjectives()
        manager.write_status_code(1)
        sys.exit(1)

    else:
        manager.retrieveResults()
        logging.info("successfully retrieved results")
        manager.write_status_code(0)
        sys.exit(0)


if __name__ == "__main__":

    if not(6<= len(sys.argv)<=7):
        logging.error(f"Number of arguments should be 6 or 7 and not {len(sys.argv)}, exit 1")
        sys.exit(1)

    logging.info("Running the runTestsAndObjctiveCalc_local_sep_analy.py ")
    jobid = sys.argv[1]
    npart = int(sys.argv[2])
    p_eta_point = sys.argv[3]
    particle = sys.argv[4]
    input_name = sys.argv[5]
    json_fname = sys.argv[6] if len(sys.argv)==7 else None

    try:
        p_eta_point = json.loads(base64.b64decode(p_eta_point).decode("utf-8"))
        run(jobid, npart, p_eta_point, particle, input_name,json_fname)
    except Exception as ex:
        logging.error(f"RunTestsAndObjectiveCalc_local_sep_analy.py: Failed to run: {ex}")
        logging.error(traceback.format_exc())
        sys.exit(1)
