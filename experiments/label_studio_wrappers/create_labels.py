import uuid

def get_rectanglelabel_dict(x, y, width, height, inner_page, test_type, o_width=700, o_height=100, rotation=0, parentID=None):
    rectanglelabel_dict = {
        "original_width": o_width,
        "original_height": o_height,
        "image_rotation": rotation,
        "item_index": inner_page,
        "value": {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "rotation": rotation,
            "rectanglelabels": [test_type]
        },
        "id": str(uuid.uuid4())[:10],
        "from_name": "rectangles",
        "to_name": "pdf",
        "type": "rectanglelabels",
        "origin": "manual",
    }
    if parentID:
        rectanglelabel_dict["id"] = parentID
    return rectanglelabel_dict

def get_textarea_dict(x, y, width, height, inner_page, text, o_width=700, o_height=100, rotation=0, parentID=None):
    textarea_dict = {
        "original_width": o_width,
        "original_height": o_height,
        "image_rotation": rotation,
        "item_index": inner_page,
        "value": {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "rotation": 0,
            "text": [text],
        },
        "id": str(uuid.uuid4())[:10],
        "from_name": "transcription",
        "to_name": "pdf",
        "type": "textarea",
        "origin": "manual"
    }
    if parentID:
        textarea_dict["id"] = parentID
    return textarea_dict

def test_text_line_to_annot_dict(test_text_line, segment_page):
    final_results = []
    line_global_id = str(uuid.uuid4())[:10]
    for bbox_page, (x, y, width, height) in test_text_line.bbox_list:
        inner_page = bbox_page-segment_page
        label_dict = get_rectanglelabel_dict(x, y, width, height, inner_page, test_text_line.test_type, parentID=line_global_id)
        final_results.append(label_dict)
        textarea_dict = get_textarea_dict(x, y, width, height, inner_page, test_text_line.text, parentID=line_global_id)
        final_results.append(textarea_dict)
    return final_results

def mol_pic_to_annot_dict(mol_pic, annot_type = "Molecule"):
    x, y, width, height = mol_pic.bbox
    rectanglelable_dict = get_rectanglelabel_dict(x, y, width, height, 0, annot_type)
    textarea_dict = get_textarea_dict(x, y, width, height, 0, "The molecule", parentID=rectanglelable_dict.get('id'))
    return [rectanglelable_dict, textarea_dict] # 

# def get_rectangle_dict(x, y, width, height, o_width=700, o_height=100, rotation=0):
#     rectangle_dict = {
#         "original_width": o_width, # 1241, # 792, 612
#         "original_height": o_height, # 1754,
#         "image_rotation": rotation,
#         "value": {
#             "x": x,
#             "y": y,
#             "width": width,
#             "height": height,
#             "rotation": rotation,
#             # "rectanglelabels": [test_type]
#         },
#         "id": str(uuid.uuid4())[:10],
#         "from_name": "bbox", # "label"
#         "to_name": "image",
#         "type": "rectangle",
#         "origin": "manual",
#     }
#     return rectangle_dict


# def get_label_dict(x, y, width, height, label_name, o_width=700, o_height=100, rotation=0):
#     label_dict = {
#         "original_width": o_width,
#         "original_height": o_height,
#         "image_rotation": rotation,
#         "value": {
#             "x": x,
#             "y": y,
#             "width": width,
#             "height": height,
#             "rotation": 0,
#             "labels": [label_name]
#         },
#         "id": str(uuid.uuid4())[:10],
#         "from_name": "label",
#         "to_name": "image",
#         "type": "labels",
#         "origin": "manual"
#     }
#     return label_dict


        # {
        #   "original_width": 700,
        #   "original_height": 1000,
        #   "image_rotation": 0,
        #   "item_index": 0,
        #   "value": {
        #     "x": 12.47,
        #     "y": 60.95,
        #     "width": 47.56,
        #     "height": 3.45,
        #     "rotation": 0,
        #     "text": [
        #       "Rf (0.26)"
        #     ]
        #   },
        #   "id": "9d21ca78-6",
        #   "from_name": "transcription",
        #   "to_name": "pdf",
        #   "type": "textarea",
        #   "origin": "manual"
        # }
