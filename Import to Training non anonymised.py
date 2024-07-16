import platform
from connect import *
import csv
import sys
import os

###############################################################################
# Custom SCRIPT PARAMETERS

# Hardcoded location of the patient list
id_filename = r"S:\Cancer Services - Radiation Physics\Auto-planning\MVision\Scripts\List of patients to export\PR1_Batch_Export_Patients.csv"

# Path to the DICOM files
dicom_files_path = r"\\Clw-rad-rsdb-01\dicom"

###############################################################################
# Function to import DICOM data for a given patient from a file path
def PKImportFromPath(path, patient_id):
    patient_db = get_current("PatientDB")
    import_warnings = []

    # Query the DICOM files for the patient
    try:
        matching_patients = patient_db.QueryPatientsFromPath(Path=path, SearchCriterias={'PatientID': patient_id})
        if len(matching_patients) == 0:
            return "No matching patient found in the path", import_warnings
        elif len(matching_patients) > 1:
            return "Multiple patients found with the same ID", import_warnings
        matching_patient = matching_patients[0]
    except SystemError as error:
        import_warnings.append(str(error))
        return "Failed to query DICOM path", import_warnings

    # Query all the studies from the matching patient
    try:
        studies = patient_db.QueryStudiesFromPath(Path=path, SearchCriterias=matching_patient)
        if not studies:
            return "No studies found for the matching patient", import_warnings
    except SystemError as error:
        import_warnings.append(str(error))
        return "Failed to query studies from DICOM path", import_warnings

    # Query all the series from the matching studies
    series = []
    try:
        for study in studies:
            series += patient_db.QuerySeriesFromPath(Path=path, SearchCriterias=study)
    except SystemError as error:
        import_warnings.append(str(error))
        return "Failed to query series from DICOM path", import_warnings

    # Import all series
    try:
        import_warnings = patient_db.ImportPatientFromPath(Path=path, SeriesOrInstances=series)
        return "Imported", import_warnings
    except SystemError as error:
        import_warnings.append(str(error))
        return "Failed to import patient", import_warnings

###############################################################################
# Main function
# This function reads the list of patients/beamsets from the input file and attempts
# to import each one from the specified DICOM files directory.
# The results of each import are output to the console or a log file.

def main():
    patient_db = get_current("PatientDB")
    plan_list = []

    # Open the input file and read in the list, create an entry in plan_list array for each row of csv
    try:
        with open(id_filename, 'r') as csvfile:
            file_reader = csv.reader(csvfile)
            for i, row in enumerate(file_reader):
                if len(row) >= 2:
                    plan_list.append(row)
                else:
                    print(f"Skipped row {i+1} due to missing details")
    except Exception as e:
        print(f"Could not read input file: {str(e)}")
        sys.exit()

    # Log the number of plans read from the CSV
    print(f"Read {len(plan_list)} patient plans from the CSV file.")

    # Loop over all patient folders in the DICOM files path
    for folder_name in os.listdir(dicom_files_path):
        for plan_details in plan_list:
            csv_patient_id, plan_name = plan_details[:2]

            # Check if the patient ID is part of the folder name
            if csv_patient_id in folder_name:
                dicom_files_path_patient = os.path.join(dicom_files_path, folder_name)

                if not os.path.exists(dicom_files_path_patient):
                    print(f"DICOM files path does not exist: {dicom_files_path_patient}")
                    continue

                # Import the DICOM files
                result, import_warnings = PKImportFromPath(dicom_files_path_patient, csv_patient_id)
                if import_warnings is None:
                    import_warnings = []

                print(f"Patient ID: {csv_patient_id}, Plan Name: {plan_name}, Result: {result}")
                for warning in import_warnings:
                    print(f"  Warning: {warning}")

if __name__ == "__main__":
    main()
