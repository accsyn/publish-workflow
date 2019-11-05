#!/usr/local/bin/python3
# Accsyn Hook example Python 2/3 script for processing an incoming publish request by user. See README.md for more information.

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
    generic_print("Pre Publish hook incoming data from user %s: %s"%(data['user_hr'], json.dumps(data, indent=3)))

    generic_print("Analyzing data")
    result = {
        "guidelines":"<html><body color='white'>Please follow our naming convention for publishing back to us:<br><ul><li>Publish directory: &lt;proj&ht;_&lt;task&ht;_&lt;vNNN&gt;</li><li>Publish preview: &lt;proj&gt;_&lt;task&gt;_&lt;vNNN&gt;_preview.mov|jpg</li><li>Publish assets: &lt;proj&gt;_&lt;task&gt;_&lt;vNNN&gt;_assets</li></ul><br><br>Select entries below and enter comment, time report and status:</body></html>",
        "comment":True,
        "time_report":True,
        "metadata":False,
        "statuses":[
            {"label": "For approval", "value":"for_approval", "default":True},
            {"label": "Work in progress", "value":"work_in_progress"},
        ], 
        "files":[]
    }
    ROOT_SHARE="/net/vol"
    DAILY_FOLDER=datetime.datetime.now().strftime("%Y%m%d")
    for entry in data['files']:
        d = copy.deepcopy(entry) # Return what we get - preserve ID field
        # Identify project, task
        parts = entry['filename'].split(".")[0].split("_")
        if 3<=len(parts):
            warning_message = validate_task_and_version(parts[0],parts[1],parts[2])
            if warning_message is None:
                project = parts[0]
                task = parts[1]
                version = get_version(parts[2])
                publish_ident = "%s_%s_v%03d"%(project, task, version)
                if len(parts) == 3:
                    if entry.get('is_dir') is True:
                        # This is a valid publish! Check the data provided
                        if 0<len(entry.get('files',[])):
                            start_image = 999999
                            end_image = -999999
                            found_numbers = []
                            for file_entry in entry['files']:
                                # Expect 'SOMENAME.<four digit number>.<ext>'
                                image_parts = file_entry['filename'].split(".")
                                if len(image_parts) == 3:
                                    # Check number
                                    try:
                                        number = int(image_parts[1])
                                        found_numbers.append(number)
                                        if number<start_image:
                                            start_image = number
                                        if end_image<number:
                                            end_image = number
                                        # Check extension
                                        if not image_parts[2].lower() in ['tiff','tif','png','tga','exr','dpx']:
                                            warning_message = "Image '%s' does not have a known frame format extension ('tiff','tif','png','tga','exr','dpx')!"%file_entry['filename']
                                            break
                                        # Here you can check if image size is ok and not varying - detect possible corrupt images.
                                    except:
                                        warning_message = "Image '%s' does not have a valid frame number!"%file_entry['filename']
                                        break
                                else:
                                    warning_message = "Image '%s' is not on the form 'imagename.number.ext'!"%file_entry['filename']
                            if warning_message is None:
                                image_count = end_image - start_image + 1
                                # Here you can check if all images are present, we check for missing images (holes)
                                n_prev = -1
                                for n in sorted(found_numbers):
                                    if n_prev != -1 and n != n_prev + 1:
                                        warning_message = "Image '%d' is missing!"%(n_prev + 1)
                                        break
                                    n_prev = n
                        else:
                            warning_message = "Directory is empty"
                        if warning_message is None:
                            d['ident'] = publish_ident
                            d['can_publish'] = True
                            d['path'] = "%s/%s/%s/publish/%s_%s_%03d"%(ROOT_SHARE, project, task, project, task, version)
                        else:
                            d['warning'] = warning_message
                            d['rejected'] = True
                    else:
                        d['warning'] = "Only directories can be published!"
                        d['rejected'] = True
                elif len(parts) == 4:
                    if parts[3] == "preview":
                        filename_parts = entry['filename'].split(".")
                        if len(filename_parts) == 2 and (filename_parts[1].lower() == "mov" or filename_parts[1].lower() == "jpg"):
                            d['ident'] = "%s_preview"%publish_ident
                            d['can_upload'] = True
                            d['path'] = "%s/%s/%s/preview/%s_%s_%03d.%s"%(ROOT_SHARE, project, task, project, task, version, filename_parts[1].lower())
                        else:
                            d['warning'] = "Previews can only be of .mov or .jpg file type/extension!"
                            d['rejected'] = True
                    elif parts[3] == "assets":
                        # Check so not empty
                        if 0<len(entry.get('files',[])):
                            d['ident'] = "%s_assets"%publish_ident
                            d['can_upload'] = True
                            d['path'] = "%s/%s/%s/assets/%s_%s_%03d"%(ROOT_SHARE, project, task, project, task, version)
                        else:
                            d['warning'] = "Empty assets directory!"
                            d['rejected'] = True
                    else:
                        d['warning'] = "Unknown additional %s asset, only previews and assets are supported!"%(publish_ident)
                        d['rejected'] = True
                else:
                    d['warning'] = "File are not following our naming convention!"
                    d['rejected'] = True
            else:
                d['warning'] = warning_message
                d['path'] = "%s/_FROM_VENDORS/%s/%s/%s"%(ROOT_SHARE, data['user_hr'], DAILY_FOLDER, entry['filename']) # Still offer to upload somewhere, you can also choose to reject this.
        else:
            d['warning'] = "File are not following our naming convention!"
            d['rejected'] = True
        result['files'].append(d)

    generic_print("My results: %s"%(json.dumps(result, indent=3)))

    p_output = sys.argv[2]
    generic_print("Writing results back to: %s"%(p_output))


    with open(p_output, "w") as f:
        f.write(json.dumps(result))

    sys.exit(0)