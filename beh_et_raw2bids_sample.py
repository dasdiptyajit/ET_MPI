import mne
import numpy as np
from pathlib import Path
import pandas as pd
import os
from os.path import join
import shutil
import subprocess
import warnings
#import environment_variables as ev


def edf2ascii(convert_exe, edf_file_name):
    """
    This function converts an edf file to an ascii file
    :param edf_file_name:
    :param convert_exe:
    :return:
    """
    cmd = convert_exe
    ascfile = Path(edf_file_name.parent, edf_file_name.stem + ".asc")

    # check if an asc file already exists
    if not os.path.isfile(ascfile):
        subprocess.run([cmd, "-p", edf_file_name.parent, edf_file_name])
    else:
        warnings.warn("An Ascii file for " + edf_file_name.stem + " already exists!")
    return ascfile


def ascii2mne_batch(raw_root, subjects, bids_root, task, session="1", convert_exe=""):
    """

    :param raw_root:
    :param subjects:
    :param bids_root:
    :param task:
    :param session:
    :param convert_exe:
    :return:
    """
    # Loop through each subject

    import pdb
    pdb.set_trace()
    for subject in subjects:
        # Get the subject directory:
        subject_dir = Path(raw_root, "sub-" + subject, "ses-" + session)
        # List the files in there:
        subject_files = [fl for fl in os.listdir(subject_dir) if fl.endswith(".edf")]
        # Create the save dir:
        if subject == "SX122":
            save_dir = Path(bids_root, "sub-" + "SX116", "ses-" + session, "eyetrack")
        else:
            save_dir = Path(bids_root, "sub-" + subject, "ses-" + session, "eyetrack")
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        task_files = [fl for fl in subject_files if fl.split("_task-")[1].split("_eyetrack.edf")[0] == task]
        # Loop through every file:
        for fl in task_files:
            # Read in EyeLink file
            print('Converting {} to asc'.format(fl))
            asci_file = edf2ascii(convert_exe, Path(subject_dir, fl))
            # Copy paste the file to the bids directory:
            asci_stem = asci_file.stem
            # Add leading 0 to files which are less than 10, to make sure that the files are loaded in the right
            # order
            if task not in ["auditory", "visual"]:
                if float(asci_stem.split('run-')[1].split('_task')[0]) <= 9:
                    asci_stem = (asci_stem.split('run-')[0] + "run-0" + asci_stem.split('run-')[1].split('_task')[0] +
                                 '_task' + asci_stem.split('run-')[1].split('_task')[1])
            else:
                asci_stem = (asci_stem.split('run-')[0] + "run-00" +
                             '_task' + asci_stem.split('run-')[1].split('_task')[1])
            if subject == "SX122":
                asci_stem = asci_stem.replace(subject, "SX116")
            print('Copying {} to {}'.format(asci_file, save_dir))
            shutil.copyfile(asci_file, Path(save_dir, asci_stem + asci_file.suffix))


def beh2bids_batch(raw_root, subjects, bids_root, task, session="1",
                   beh_fn_template="sub-{}_ses-{}_run-{}_task-{}_events.csv", run="all", remove_practice=True):
    # Loop through each subject
    for subject in subjects:
        # Get the subject directory:
        subject_dir = Path(raw_root, "sub-" + subject, "ses-" + session)

        # Load the concatenated tables:
        log_file = [beh_fl
                    for beh_fl in os.listdir(Path(subject_dir))
                    if beh_fl == beh_fn_template.format(subject, session, run, task) or
                    beh_fl == beh_fn_template.format(subject, session,run, task).split(".")[0] +
                    "_repetition_1.csv"]
        # Load and concatenate the log files:
        log_df = pd.concat([pd.read_csv(Path(subject_dir, log)) for log in log_file]).reset_index(drop=True)
        # Sort the table by the time stamps:
        log_df = log_df.sort_values(by="vis_stim_time").reset_index(drop=True)
        # For a few participants, the experiment crashed and blocks had to be restarted. Marking duplicates with a flag:
        log_df['is_duplicate'] = log_df.duplicated(subset=['block', 'trial'], keep='last')
        log_df = log_df[~log_df['is_duplicate']]
        # For some participants, there was a bug in the code such that the practice table were saved alongside the
        # prp. Removing any such trials:
        if remove_practice:
            log_df = log_df[log_df["is_practice"] == 0]
        # Create the bids directory for that subject:
        if subject == "SX122":  # The subject SX122 was misnamed, it was actually SX116
            save_dir = Path(bids_root, "sub-" + "SX116", "ses-" + session, "beh")
            fn = beh_fn_template.format("SX116", session, "all", task)
        else:
            save_dir = Path(bids_root, "sub-" + subject, "ses-" + session, "beh")
            fn = beh_fn_template.format(subject, session, "all", task)
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        # Save the data:
        log_df.to_csv(Path(save_dir, fn), index=False)


if __name__ == "__main__":

    subjects_dir = join('/','media', 'dip_linux', 'SanDisk', 'cog_data', 'ET_BEH_bids', 'source_curated_dir', '')
    bids_root = join(subjects_dir, 'ET_bids',  '')
    convert_exe = join(subjects_dir, 'ET_bids',  'edf2asc.exe')
    # # Subject list for each task:
    # subjects_list_prp = [
    #      "SX101", "SX102", "SX103", "SX105", "SX106", "SX107", "SX108", "SX109", "SX110", "SX111", "SX112", "SX113",
    #      "SX114", "SX115", "SX116", "SX117", "SX118", "SX119", "SX120", "SX121", "SX123"
    #  ]
    # subjects_list_introspection = [
    #      "SX101", "SX105", "SX106", "SX108", "SX109", "SX110", "SX113", "SX114", "SX115", "SX118", "SX122"
    #  ]
    #
    # Subject list for each task:
    subjects_list_prp = [
         "CA139"
     ]
    subjects_list_introspection = [
        "CA139"
     ]

    # # ===============================================================================================
    # # Convert the behavioral data:
    # # ===========================================
    # # PRP:
    # beh2bids_batch(ev.raw_root, subjects_list_prp, ev.bids_root, "prp", session="1",
    #                beh_fn_template="sub-{}_ses-{}_run-{}_task-{}_events.csv", run="all")
    # # ===========================================
    # # visual:
    # beh2bids_batch(ev.raw_root, subjects_list_prp, ev.bids_root, "visual", session="1",
    #                beh_fn_template="sub-{}_ses-{}_run-{}_task-{}_events.csv", run="0", remove_practice=False)
    # # ===========================================
    # # auditory:
    # beh2bids_batch(ev.raw_root, subjects_list_prp, ev.bids_root, "auditory", session="1",
    #                beh_fn_template="sub-{}_ses-{}_run-{}_task-{}_events.csv", run="0", remove_practice=False)
    # # ===========================================
    # # Introspection:
    # beh2bids_batch(ev.raw_root, subjects_list_introspection, ev.bids_root, "introspection", session="2",
    #                beh_fn_template="sub-{}_ses-{}_run-{}_task-{}_events.csv")
    # beh2bids_batch(ev.raw_root, subjects_list_introspection, ev.bids_root, "introspection", session="3",
    #                beh_fn_template="sub-{}_ses-{}_run-{}_task-{}_events.csv")

    # ===============================================================================================
    # Convert the eye-tracking data:
    # ===========================================
    # PRP:
    #raw_root, subjects, bids_root, task, session="1", convert_exe=""
    #/media/dip_linux/SanDisk/cog_data/ET_BEH_bids/source_curated_dir/CA139/CA139_MEEG_1/RESOURCES/ET/CA139_ET_1_DurR1.asc
    ascii2mne_batch(raw_root=subjects_dir, subjects=subjects_list_prp, bids_root=bids_root, task="prp",
                    convert_exe=convert_exe)
    # # ===========================================
    # # Auditory only practice:
    # ascii2mne_batch(ev.raw_root, subjects_list_prp, ev.bids_root, "auditory",
    #                 convert_exe=r"C:\Users\alexander.lepauvre\Documents\GitHub\Reconstructed_time_analysis\edf2asc.exe")
    # # ===========================================
    # # Visual only practice:
    # ascii2mne_batch(ev.raw_root, subjects_list_prp, ev.bids_root, "visual",
    #                 convert_exe=r"C:\Users\alexander.lepauvre\Documents\GitHub\Reconstructed_time_analysis\edf2asc.exe")
    # # ===========================================
    # # Introspection:
    # ascii2mne_batch(ev.raw_root, subjects_list_introspection, ev.bids_root, "introspection", session="2",
    #                 convert_exe=r"C:\Users\alexander.lepauvre\Documents\GitHub\Reconstructed_time_analysis\edf2asc.exe")
    # tasks_list = ["introspection"]
    # ascii2mne_batch(ev.raw_root, subjects_list_introspection, ev.bids_root, "introspection", session="3",
    #                 convert_exe=r"C:\Users\alexander.lepauvre\Documents\GitHub\Reconstructed_time_analysis\edf2asc.exe")
