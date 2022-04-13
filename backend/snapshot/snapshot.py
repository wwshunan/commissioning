from epics import PV

def get_element_values(parent_list, source, keys):
    for item in source:
        if not any('pv' in x for x in item.keys()):
            current_dict = {}
            current_dict[item['label']] = []
            parent_list.append(current_dict)
            get_element_values(current_dict[item['label']], item['children'], keys)
            if not current_dict[item['label']]:
                parent_list.remove(current_dict)
        elif item['id'] in keys:
            for x in item:
                if 'pv' in x:
                    label = item['id']
                    if x != 'pv':
                        set_val = PV(item['write_pv']).get()
                        get_val = PV(item['rb_pv']).get()
                        parent_list.append({label: (set_val, get_val)})
                    else:
                        val = PV(item[x]).get()
                        parent_list.append({label: val})





#class Snapshot(object):
#    def __init__(self, data):
