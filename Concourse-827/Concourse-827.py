import os
#from inspect import stack
import logging # za da logva vutre v python scripta
import json # za pipeline confuguration da zapiswa kakvoto fetchne v log file
import subprocess # za da izpulnqva komandi vutre v python scripta ili s api . 
import argparse
#from shutil import rmtree

def arguments_parse(): 
    parser = argparse.ArgumentParser(description="Collect user input for Concourse and Docker.")
    
    parser.add_argument("--concourse_url", required=True, help="Concourse URL")
    parser.add_argument("--concourse_team", required=True, help="Concourse team name")
    parser.add_argument("--concourse_user", required=True, help="Concourse username")
    parser.add_argument("--concourse_password", required=True, help="Concourse password")
    parser.add_argument("--iacbox_version", type=int, default=700, help="iacBox version (default: 700)")
    args = parser.parse_args()

    return vars(args) # vars(args) преобразува обекта Namespace в обикновен речник (dict), за по-лесно използване.

def concourse_login(concourse_url, concourse_team, concourse_username, concourse_password):
    subprocess.run(
        ["fly", "login", "-t", "dev", "-c", concourse_url, "-n", concourse_team, "-u", concourse_username, "-p", concourse_password],
        check=True
        #capture_output=True#tova e za da zapazi izhoda stdout and stderr za da mogat da se obrabotqt, a bez tqh izkarva error-a na konzolata i exitva
    )
    print("Successfully logged into Concourse.")

def fetch_pipelines_names():
    result= subprocess.run(
        ["fly", "-t", "dev", "ps", "--json"],
        check=True, capture_output=True, text=True)
    pipelines = json.loads(result.stdout)
    pipeline_names = [pipeline["name"] for pipeline in pipelines] #vryshta samo imenata na pipeline-ite
    return pipeline_names

def fetch_pipeline_definitions(pipeline_names, logger):
    pipeline_definitions = {} # prazen dict, koito shte se naplni s informaciq za pipeline-ite

    for pipeline in pipeline_names:  # iterira direktno prez imenata na pipeline-ite / obhojda vsqko ime na pipeline ot spisaka s pipeline-ite
    
        result = subprocess.run(
            ["fly", "-t", "dev", "gp", "-p", pipeline, "--json"],
            capture_output=True, # capture-a go polzvam za da mi zapishe result.stdout v pipeline_definition, checkTrue za da sme sigurni che otdolu fly-a vrushta izpulnena komanda
        )
        if result.stderr:
            logger.error(f"Failed to fetch pipeline '{pipeline}' configuration. Reason: {result.stderr}") # slagam print-a za da se uverq, che obhojdaneto po pipeline-ite e uspeshno
            continue
        
        pipeline_definitions[pipeline] = json.loads(result.stdout)  # Storva vseki pipeline kato key i value e obekt s informaciq za pipeline-a

    return pipeline_definitions 
    
def extract_pipelines(pipeline_definitions, logger, iacbox_version):#  za da se izvleche informaciq za jobs i tasks
    extracted_data = [] # otnovo prazen dict, koito shte pobere extractnatata data za pipeline-ite # d podsigurq dali e iacbox.
    for pipeline, config in pipeline_definitions.items():
        stack = [config]
        job_name = "No job name found"
        while stack:
             
            current = stack.pop()
            if isinstance(current, dict):
                if "plan" in current.keys():
                    job_name = current.get("name") 
                tag = current.get("tag")
                if tag_under_version(tag, iacbox_version):#argparse version to check
                    logger.error(f"Job '{job_name}' in pipeline '{pipeline}' has a tag with version '{tag}'!")
                stack.extend(current.values())  # Добавяме всички стойности от речника в стека
            elif isinstance(current, list):
                stack.extend(current)  # 

    return extracted_data 
                
def tag_under_version(tag, iacbox_version):
    if not tag:
        return False 
    if tag.startswith("v") and tag[1:].isdigit():
        tag_version = int(tag[1:])
        if tag_version < iacbox_version:
            return True
    return False

def enable_logger(log_file_path):
    
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    logging.basicConfig(
        filename=log_file_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    return logging.getLogger()

def main():
    log_file_path = "/tmp/invalid_iacbox_versions.log"
    logger = enable_logger(log_file_path=log_file_path)

    args = arguments_parse()
    concourse_login(
        args["concourse_url"],
        args["concourse_team"],
        args["concourse_user"],
        args["concourse_password"]
    )
    iacbox_version = args["iacbox_version"] # dobaviam go kato bonus iziskvane / ako usera podade arg da go polzva.Ako li ne - default = 700

    pipeline_names = fetch_pipelines_names()
    pipeline_definitions = fetch_pipeline_definitions(pipeline_names=pipeline_names, logger=logger)
    extract_pipelines(iacbox_version=iacbox_version, pipeline_definitions=pipeline_definitions, logger=logger)
    
    
if __name__ == "__main__":
    main()