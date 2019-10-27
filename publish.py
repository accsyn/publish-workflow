#!/usr/local/bin/python3
# Accsyn Hook example Python 2/3 script for postprocessing a publish. See README.md for more information.

import sys, os, json, copy, datetime

def generic_print(s):
    try:
        if ((3, 0) < sys.version_info):
            # Python 3 code in this block
            expr = """print(s)"""
        else:
            # Python 2 code in this block
            expr = """print s"""
        eval(expr)
    except:
        pass

def get_version(version_ident):
    version = -1
    parts = version_ident.split("v")
    try:
        version = int(parts[1])
    except:
        pass
    return version

def validate_task_and_version(project_ident, task_ident, version_ident):
    # Here you could check the project and task against your production database, for example directories on disk or by querying a project management system/Google sheet or similar.
    if project_ident.lower() != "proj":
        return "Unknown project '%s'!"%project_ident
    if task_ident.lower() != "task001":
        return "Unknown task '%s'!"%task_ident
    if not version_ident.lower().startswith("v"):
        return "Invalid version identifier '%s' - has to start with an 'v'!"%version_ident
    parts = version_ident.split("v")
    try:
        version = int(parts[1])
    except:
        return "Invalid version identifier '%s' - must be a 'v' followed by integer number!"%version_ident
    if version != 1:
        return "Version %d is not the next publishable version!"%version
    return None # All ok

if __name__ == '__main__':

    p_input = sys.argv[1]
    data = json.load(open(p_input, "r"))
    generic_print("Publish hook incoming data from user %s: %s"%(data['user_hr'], json.dumps(data, indent=3)))

    generic_print("Analyzing data")
    for entry in data['files']:
        # Re-identify project, task
        parts = entry['filename'].split(".")[0].split("_")
        if 3<=len(parts):
            warning_message = validate_task_and_version(parts[0],parts[1],parts[2])
            if warning_message is None:
                project = parts[0]
                task = parts[1]
                version = get_version(parts[2])
                publish_ident = "%s_%s_v%03d"%(project, task, version)
                path_server = entry['path'] # Absolute
                if len(parts) == 3:
                    # The published data, here you can mangle the file/directories as needed and create records in production database.
                    # In this example, we save the user comment, status and time report in a sidecar JSON
                    with open("%s.metadata.json"%path_server, "w") as f_md:
                        json.dump({
                            'user':data['user_hr'],
                            'comment':entry['comment'],
                            'time_spent_s':entry['time_report'],
                            'status':entry['status'],
                        }, f_md)
                        generic_print("Saved publish %s metadata to: %s"%(publish_ident, f_md.name))

                elif len(parts) == 4:
                    if parts[3] == "preview":
                        # A preview made by user, here you can use the preview or generate a more solid custom preview using publish above.
                        pass
                    elif parts[3] == "assets":
                        # Here you can check assets, for example align known paths in work project files so they are openable on-prem
                        pass

    sys.exit(0)