def extract_pipelines(pipeline_definitions):#  za da se izvleche informaciq za jobs i tasks
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
                if not valid_tag(tag):
                    extracted_data.append({"pipeline": pipeline, "job_name": job_name, "tag": tag})
                stack.extend(current.values())  # Добавяме всички стойности от речника в стека
            elif isinstance(current, list):
                stack.extend(current)  # 

    return extracted_data 

def valid_tag(tag, version):
    if not tag:
        return True # We do not log empty tags
    if tag.startswith("v") and tag[1:].isdigit():
        tag_version = int(tag[1:])
        if tag_version >= version:
            return True
    return False

pipeline_definitions = { "some-pipeline":
    {
        "jobs": [
            {
                "name": "hello-world",
                "plan": [
                    {
                        "config": {
                            "platform": "linux",
                            "image_resource": {
                                "name": "",
                                "type": "registry-image",
                                "source": {
                                    "password": "((concourse-docker-image-password))",
                                    "repository": "iacbox.common.repositories.cloud.sap/iacbox2",
                                    "tag": "v699",
                                    "username": "((concourse-docker-image-username))"
                                }
                            },
                            "run": {
                                "path": "echo",
                                "args": [
                                    "Hello, world!"
                                ]
                            }
                        },
                        "task": "say-hello"
                    }
                ]
            },
            {
                "name": "hello-world-gosho",
                "plan": [
                    {
                        "config": {
                            "platform": "linux",
                            "image_resource": {
                                "name": "",
                                "type": "registry-image",
                                "source": {
                                    "password": "((concourse-docker-image-password))",
                                    "repository": "iacbox.common.repositories.cloud.sap/iacbox2",
                                    "tag": "v700",
                                    "username": "((concourse-docker-image-username))"
                                }
                            },
                            "run": {
                                "path": "echo",
                                "args": [
                                    "Hello, world!"
                                ]
                            }
                        },
                        "task": "say-hello"
                    }
                ]
            }
        ]
    }
}
# print(extract_pipelines(pipeline_definitions))

def test(option1, option2):
    print(f"Option1: {option1}, option2: {option2}")

test(option2="gosho", option1="pesho")