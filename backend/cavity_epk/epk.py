def epk_dict(author, file):
    epk_dict = {}
    epk_list = []
    for raw_line in file:
        line = raw_line.decode("utf-8")
        if not line.strip():
            continue
        epk_item = {}
        line_split = line.split()
        if line_split[0].startswith('cavity-name'):
            continue
        epk_item['name'] = line_split[0]
        epk_item['epk'] = line_split[1]
        epk_list.append(epk_item)
    file.close()
    epk_dict['author'] = author
    epk_dict['epks'] = epk_list
    return epk_dict
