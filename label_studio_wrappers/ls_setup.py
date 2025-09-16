import os
from label_studio_sdk.client import LabelStudio

# label_config = """
# <View>
#   <RectangleLabels name="rectangles" toName="pdf" showInline="true">
#     <Label value="NMR" background="#F72585"/>
#     <Label value="IR" background="#7209B7"/>
#     <Label value="RF" background="#3A0CA3"/>
#     <Label value="MS" background="#EE9B00"/>
#     <Label value="Molecule" background="#AE2012"/>
#     <Label value="Candidate Molecule" background="#94D2BD"/>
#   </RectangleLabels>
#   <Image valueList="$pages" name="pdf"/>
#   <TextArea name="transcription" toName="pdf" editable="true" perRegion="true" required="true" placeholder="Recognized Text" displayMode="region-list"/>
#   <Choices name="user_approval" toName="pdf" choice="single" showInLine="true">
#   <Choice value="Yes"/>
#   <Choice value="No"/>
#   </Choices>
# </View>
# """

def get_unique_molecule_segment_test_type(molecule_segments):
    test_type_set = set()
    for molecule_segment in molecule_segments:
        test_type_set.update(molecule_segment.test_text_sequence.test_type_list)
    return list(test_type_set)

def get_label_lines(test_color_list):
    label_lines = ""
    for label, color in test_color_list:
        label_lines += f'    <Label value="{label}" background="{color}"/>\n'
    label_lines=label_lines.strip()
    return label_lines

def get_label_config_from_label_lines(label_lines):
    label_config = """
<View>
  <RectangleLabels name="rectangles" toName="pdf" showInline="true">
    {}
    <Label value="Molecule" background="#AE2012"/>
  </RectangleLabels>
  <Image valueList="$pages" name="pdf"/>
  <TextArea name="transcription" toName="pdf" editable="true" perRegion="true" required="true" placeholder="Recognized Text" displayMode="region-list"/>
</View>
""".format(label_lines)
    return label_config

def get_label_config(molecule_segments):
    COLOR_WHEEL = ['#FFD700', '#FFB14E', '#FA8775', '#EA5F94', '#CD34B5', '#9D02D7', '#0000FF', '#7695FF'] # two last colors!!!!!!!!!!!!
    unique_test_type_list = get_unique_molecule_segment_test_type(molecule_segments)
    test_color_list = list(zip(unique_test_type_list, COLOR_WHEEL[:len(unique_test_type_list)]))
    label_lines = get_label_lines(test_color_list)
    label_config = get_label_config_from_label_lines(label_lines)
    return label_config

def load_default_ls_url(ls_url=None):
    if ls_url is None:
        ls_url = 'http://localhost:8080'
    return ls_url

def ls_login(api_key, ls_url=None):
    ls_url = load_default_ls_url(ls_url)
    ls = LabelStudio(base_url=ls_url, api_key=api_key)
    return ls 

def get_annot_value_from_task(task):
    return task.get('annotations')[0].get('result')

def setup_label_studio_project(api_key, project_name, label_config, storage_config, ls_url=None):
    ls = ls_login(api_key, ls_url)
    project = ls.projects.create(title=project_name,
                                label_config=label_config,
                                description=f"extracted results of {project_name}",
                                )
    project_id = project.id
    storage_config['project'] = project_id
    os.makedirs(storage_config.get('path'), exist_ok=True)
    ls.import_storage.local.create(**storage_config)
    annot_client = ls.annotations
    tasks_client = ls.tasks
    user_id = ls.users.list()[0].id
    # return ls, project_id, user_id, tasks_client, annot_client
    return ls, project_id, user_id, tasks_client, annot_client