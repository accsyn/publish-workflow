#!/usr/local/bin/python3
# Accsyn Hook example Python 2/3 script for postprocessing a publish. See README.md for more information.

import sys
import json


def get_version(version_ident):
    result = -1
    try:
        result = int(version_ident.split("v")[1])
    except:
        pass
    return result


def validate_task_and_version(project_ident, task_ident, version_ident):
    # Here you could check the project and task against your production database, for example directories on disk or
    # by querying a project management system/Google sheet or similar.
    if project_ident.lower() != "proj":
        return "Unknown project '{}'!".format(project_ident)
    if task_ident.lower() != "task001":
        return "Unknown task '{}'!".format(task_ident)
    if not version_ident.lower().startswith("v"):
        return "Invalid version identifier '{}' - has to start with an 'v'!".format(version_ident)
    try:
        version = int(version_ident.split("v")[1])
    except:
        return "Invalid version identifier '{)' - must be a 'v' followed by integer number!".format(version_ident)
    if version != 1:
        return "Version {} is not the next publishable version!".format(version)
    return None  # All ok


if __name__ == '__main__':

    p_input = sys.argv[1]
    data = json.load(open(p_input, "r"))
    print("Publish hook incoming data from user {}: {}".format(data['user_hr'], json.dumps(data, indent=3)))

    print("Analyzing data")
    for entry in data['files']:
        # Re-identify project, task
        parts = entry['filename'].split(".")[0].split("_")
        if 3 <= len(parts):
            warning_message = validate_task_and_version(parts[0], parts[1], parts[2])
            if warning_message is None:
                project = parts[0]
                task = parts[1]
                version = get_version(parts[2])
                publish_ident = "%s_%s_v%03d" % (project, task, version)
                path_server = entry['path']  # Absolute
                if len(parts) == 3:
                    # The published data, here you can mangle the file/directories as
                    # needed and create records in productiondatabase.
                    # In this example, we save the user comment, status and time report in a sidecar JSON
                    with open("{}.metadata.json".format(path_server), "w") as f_md:
                        json.dump({
                            'user': data['user_hr'],
                            'comment': entry['comment'],
                            'time_spent_s': entry['time_report'],
                            'status': entry['status'],
                            'metadata': entry.get('metadata')
                        }, f_md)
                        print("Saved publish {} metadata to: {}".format(publish_ident, f_md.name))

                elif len(parts) == 4:
                    if parts[3] == "preview":
                        # A preview made by user, here you can use the preview or generate a more solid custom preview
                        # using publish above.
                        pass
                    elif parts[3] == "assets":
                        # Here you can check assets, for example align known paths in work project files so they are
                        # openable on-prem
                        pass

    sys.exit(0)
