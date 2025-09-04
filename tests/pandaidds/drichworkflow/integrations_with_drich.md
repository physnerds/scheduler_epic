# This document briefly explains how to use the scheduler_epic for the drich-mobo. 

## Build/Install scheduler_epic (tested on the BNL eic machine)
1. Install conda package-manager.
2. Install pre-requisites for the scheduler_epic in a clean conda environment.
2. Follow the  instructions mentioned in the scheduler_epic readme.md to install all the dependencies.
3. Get the latest version of idds-client and workflow if not already.
```bash
pip install --upgrade idds-client idds-common idds-workflow
```
4. Clone the drich port scheduler_epic
```bash
git clone -b abashyal_drich_ports https://github.com/physnerds/scheduler_epic.git
```

5. Go to the drichworkflow directory

```bash
cd scheduler_epic/tests/pandaidds/drichworkflow
```

6. In *ProjectUtils/ePICUtils* directory, there are simreco and analysis python codes that has edits to work with the scheduler_epic. You can either use replace the python codes of drich-mobo (panda-idds branch) with these ones or edit the *drichworkflow/test_pandaidds_multi_steps_drich.py* accordingly.
6. Download the dRICH-MOBO (panda-idds branch) inside the *drichworflow directory* directory.

## Suggested Rough structure of directory

drichworkflow \
 --test_pandaidds_multi_steps.drich.py \
 -- optimize_dev.config  \
 -- parameters.config  \
 -- ProjectUtils (from the dRICHMOBO project) \
    -- ePICUtils (from the dRICHMOBO project) \
    -- runTestsAndObjectiveCalc_local_sep_analy.py (from this project) \
    -- runTestsAndObjectiveCalc_local_sep_simreco.py (from this project) \
    -- Everything Else (from dRICHMOBO project) 

## Running instructions
To run the optimiztion with 50 trials, 1000 total events with 2 sim-reco jobs of 500 events each for example:

```bash
python test_pandaidds_multi_steps_drich.py -d parameters.config -c optimize_dev.config --trials 50 --name "drich_multistep_50trials" --queue BNL_PanDA_1 --n_evts_per_job 500 --n_tot_evts 1000 
```
## Results and checkpoints
Results and checkpoints in *drichworkflow/work*
 
 