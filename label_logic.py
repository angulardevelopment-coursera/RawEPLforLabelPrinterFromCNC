# label_logic.py

def apply_edging_or_paint_logic(parsed_data_list, lookup_data):
    """
    Applies edging/paint data from lookup_data to each part in parsed_data_list
    based on PartName and dimensions.
    Updates both 'Edging' and 'Comments' fields of each part.
    lookup_data is a list of tuples: (base_part_name, value_if_L_ge_W, value_if_W_gt_L, comment)
    """
    if not lookup_data:
        print("  Info: No lookup data provided for applying edging/paint. Edging and Comments columns will be cleared.")
        for part in parsed_data_list: 
            part['Edging'] = ""
            part['Comments'] = "" 
        return

    for part in parsed_data_list:
        part_name = part['PartName']
        length = part['Length']
        width = part['Width']
        
        applied_edging_value = "" 
        applied_comment_value = "" 
        
        for base_name, value_L_ge_W, value_W_gt_L, comment_from_lookup in lookup_data: 
            if base_name.upper() in part_name.upper(): 
                if length >= width:
                    applied_edging_value = value_L_ge_W
                else: 
                    applied_edging_value = value_W_gt_L
                applied_comment_value = comment_from_lookup 
                break 
        
        part['Edging'] = applied_edging_value 
        part['Comments'] = applied_comment_value 
        
        if not applied_edging_value:
            print(f"  Info: No Edging/Paint rule found for PartName: '{part_name}'")