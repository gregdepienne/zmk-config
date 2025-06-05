import csv
import re
import pprint
import sys

re_unicode_init = re.compile(r"^.+=\s+<&macro_press\s+&kp\s+L_CTL\s+&kp\s+L_SHIFT>.*")
re_unicode_code = re.compile(r"^.+,\s+<&macro_tap\s+&kp\s+U\s+&kp\s+([A-Z0-9]+)\s+&kp\s+([A-Z0-9]+)\s+&kp\s+([A-Z0-9]+)\s+&kp\s+([A-Z0-9]+)\s+&kp\s+SPACE>.*")
re_unicode_end = re.compile(r"^.+,\s+<&macro_release\s+&kp\s+L_CTL\s+&kp\s+L_SHIFT>.*")

map_unicode_to_alt = {}

with open('Alt_code_unicode.csv') as csv_file:
    csv_read=csv.reader(csv_file, delimiter=',')

    for index, row in enumerate(csv_read):
        if index > 1:
            # CP 437
            # map_unicode_to_alt[row[3][2:]] = row[1][4:]

            # Windows 1252
            map_unicode_to_alt[row[7][2:]] = row[5][4:]
# {'0000': '0', '0001': '01', '0002': '02', '0003': '03', '0004': '04', '0005': '05', '0006': '06', '0007': '07', '0008': '08', '0009': '09', '000A': '010', '000B': '011', '000C': '012', '000D': '013', '000E': '014', '000F': '015', '0010': '016', '0011': '017', '0012': '018', '0013': '019', '0014': '020', '0015': '021', '0016': '022', '0017': '023', '0018': '024', '0019': '025', '001A': '026', '001B': '027', '001C': '028', '001D': '029', '001E': '030', '001F': '031', '0020': '032', '0021': '033', '0022': '034', '0023': '035', '0024': '036', '0025': '037', '0026': '038',}

def keyword_to_digit(keyword):
    if keyword.startswith("N"):
        return keyword[1]
    else:
        return keyword

def string_digits_to_keywords(digits):
    result = ""
    for i in range(len(digits)):
        digit = digits[i]
        if digit in ["A", "B", "C", "D", "E", "F"]:
            result += f" &kp {digit}"
        else:
            result += f" &kp N{digit}"
    return result

known_unicodes = map_unicode_to_alt.keys()

list_of_lines = []
list_of_unicode_lines = {}
errors_line_nbs = []
unfound_codes = {}

with open('config/sofle_ergol_azerty.keymap', 'r') as file:
    for line in file:
        list_of_lines.append(line)

for line_index in range(len(list_of_lines)):
    if re_unicode_init.match(list_of_lines[line_index]):
        if re_unicode_end.match(list_of_lines[line_index+2]):
            if re_unicode_code.match(list_of_lines[line_index+1]):
                result = list(re_unicode_code.findall(list_of_lines[line_index+1])[0])
                result_code = ""
                for digit in range(4):
                    result_code += keyword_to_digit(result[digit])
                if result_code in known_unicodes:
                    list_of_unicode_lines[line_index+1] = (result_code, map_unicode_to_alt[result_code])
                    # list_of_unicode_lines[line_index+1] = (list_of_lines[line_index+1], result_code, map_unicode_to_alt[result_code])
                else: 
                    errors_line_nbs.append((line_index+1, list_of_lines[line_index+1], f"code {result_code} not in known_unicodes"))
                    macro = list_of_lines[line_index-4].strip().split(":")[0]
                    unfound_codes[line_index+1] = result_code, macro

            else:
                errors_line_nbs.append((line_index+1, list_of_lines[line_index+1]))

# print(list_of_unicode_lines)
# if errors_line_nbs:
#     print("Errors:", errors_line_nbs)
# print(f"{len(unfound_codes)} unfound codes: ")
# pprint.pprint(unfound_codes)
# print()
# print(f"{len(list_of_unicode_lines)} lines to modify:")
# pprint.pprint(list_of_unicode_lines)



def linux_bloc_to_win_bloc(list_of_lines, line_index, linux_code, win_code):
    line_0 = list_of_lines[line_index - 1]
    line_1 = list_of_lines[line_index]
    line_2 = list_of_lines[line_index + 1]

    if not re_unicode_init.match(line_0):
        print("error match init: ", line_index, line_0)
        sys.exit(1)
    if not re_unicode_code.match(line_1):
        print("error match code: ", line_index, line_1)
        sys.exit(1)
    if not re_unicode_end.match(line_2):
        print("error match end: ", line_index, line_2)
        sys.exit(1) 

    new_line_0 = re.sub(r"&kp L_CTL &kp L_SHIFT", r"&kp L_ALT", line_0)

    new_line_2 = re.sub(r"&kp L_CTL &kp L_SHIFT", r"&kp L_ALT", line_2)

    re_find = " &kp U" + string_digits_to_keywords(linux_code) + " &kp SPACE"
    re_replace = string_digits_to_keywords(win_code)

    new_line_1 = re.sub(re_find, re_replace, line_1)

    line_title = list_of_lines[line_index - 5]
    new_line_title = re.sub(": ", "_win: ", line_title)
    new_line_title = re.sub(" {", "_win {", new_line_title)

    line_comment = list_of_lines[line_index - 6]
    line_comment_bits = re.findall(r"(^\s+// .+ : )(\S+)( : .+)\n$", line_comment)
    new_line_comment = f"{line_comment_bits[0][0]}Alt({win_code}){line_comment_bits[0][2]}\n"

    return [
        new_line_comment,
        new_line_title,
        list_of_lines[line_index - 4],
        list_of_lines[line_index - 3],
        list_of_lines[line_index - 2],
        new_line_0, 
        new_line_1, 
        new_line_2,
        list_of_lines[line_index + 2],
        list_of_lines[line_index + 3],
        list_of_lines[line_index + 4],
    ]

# print(linux_bloc_to_win_bloc(list_of_lines, 60, "201E", "0132"))


def linux_bloc_to_no_win_bloc(list_of_lines, line_index, linux_code, macro_name):
    line_0 = list_of_lines[line_index - 1]
    line_1 = list_of_lines[line_index]
    line_2 = list_of_lines[line_index + 1]
    if not re_unicode_init.match(line_0):
        print("error match init: ", line_index, line_0)
        sys.exit(1)
    if not re_unicode_code.match(line_1):
        print("error match code: ", line_index, line_1)
        sys.exit(1)
    if not re_unicode_end.match(line_2):
        print("error match end: ", line_index, line_2)
        sys.exit(1)

    
    line_supp = list_of_lines[line_index - 6]
    line_supp_bits = re.findall(r"(^\s+// [^:]+ : )(.+)\n$", line_supp)
    new_line_supp = f"{line_supp_bits[0][0]}NO {macro_name}_win \n"

    return [ new_line_supp, list_of_lines[line_index + 4]]

# print(linux_bloc_to_no_win_bloc(list_of_lines, 60, "201E", "macro_toto"))

def make_new_list_of_lines(list_of_lines, unfound_codes, unicode_lines):
    offset = 0
    new_list_of_lines = []

    unfound_codes_indices = list(unfound_codes.keys())
    unicode_lines_indices = list(unicode_lines.keys())

    next_unfound_code = None
    next_unicode = None
    
    if len(unfound_codes_indices):
        next_unfound_code_index = unfound_codes_indices[0]
    
    if len(unicode_lines_indices):
        next_unicode_index = unicode_lines_indices[0]

    next_interesting_index = None
    
    if next_unfound_code_index:
        if next_unicode_index:
            next_interesting_index = min(next_unfound_code_index, next_unicode_index)
            if next_interesting_index in unfound_codes.keys():
                unfound_codes_indices.pop(0)
            else:
                unicode_lines_indices.pop(0)
        else:
            next_interesting_index = next_unfound_code_index
            unfound_codes_indices.pop(0)
    else:
        if next_unicode_index:
            next_interesting_index = next_unicode_index
            unicode_lines_indices.pop(0)
        else:
            next_interesting_index = None

    for index_in_orig in range(len(list_of_lines)):
        # print(index_in_orig, next_interesting_index, unfound_codes_indices, unicode_lines_indices, len(new_list_of_lines))
        if next_interesting_index:
            if index_in_orig < next_interesting_index + 4:
                new_list_of_lines.append(list_of_lines[index_in_orig])
            else:
                if next_interesting_index in unfound_codes.keys():
                    new_list_of_lines += linux_bloc_to_no_win_bloc(
                        list_of_lines,
                        next_interesting_index,
                        unfound_codes[next_interesting_index][0],
                        unfound_codes[next_interesting_index][1]
                    )
                else:
                    new_list_of_lines += linux_bloc_to_win_bloc(
                        list_of_lines,
                        next_interesting_index,
                        unicode_lines[next_interesting_index][0],
                        unicode_lines[next_interesting_index][1],
                    )
                
                if len(unfound_codes_indices):
                    if len(unicode_lines_indices):
                        if unfound_codes_indices[0] < unicode_lines_indices[0]:
                            next_interesting_index = unfound_codes_indices.pop(0)
                        else:
                            next_interesting_index = unicode_lines_indices.pop(0)
                    else:
                        next_interesting_index = unfound_codes_indices.pop(0)
                else:
                    if len(unicode_lines_indices):
                        next_interesting_index = unicode_lines_indices.pop(0)
                    else:
                        next_interesting_index = None

        else:
            new_list_of_lines.append(list_of_lines[index_in_orig])

    return new_list_of_lines

new_list_of_lines = make_new_list_of_lines(list_of_lines, unfound_codes, list_of_unicode_lines)


try:
    with open('config/sofle_ergol_azerty_windows.keymap', "x") as f:
        f.writelines(new_list_of_lines)
except FileExistsError:
    print("Already exists.")


# pourquoi pas macro_s_sharp ??

# Windows 1252
# 23 unfound codes: 
# {398: ('1E9E', 'macro_s_sharp'),   598
#  411: ('2011', 'macro_nb_hyphen'),
#  503: ('202F', 'macro_sp_insec_fine'),
#  536: ('2081', 'macro_sub_1'),
#  557: ('2082', 'macro_sub_2'),
#  569: ('2083', 'macro_sub_3'),
#  581: ('2084', 'macro_sub_4'),
#  591: ('2074', 'macro_sup_4'),
#  602: ('2085', 'macro_sub_5'),
#  612: ('2075', 'macro_sup_5'),
#  623: ('2086', 'macro_sub_6'),
#  633: ('2076', 'macro_sup_6'),
#  644: ('2087', 'macro_sub_7'),
#  654: ('2077', 'macro_sup_7'),
#  665: ('2088', 'macro_sub_8'),
#  675: ('2078', 'macro_sup_8'),
#  686: ('2089', 'macro_sub_9'),
#  696: ('2079', 'macro_sup_9'),
#  707: ('2080', 'macro_sub_0'),
#  717: ('2070', 'macro_sup_0'),
#  750: ('2264', 'macro_less_eq_to'),
#  771: ('2265', 'macro_great_eq_to'),
#  843: ('2260', 'macro_not_equal')}

# 37 lines to modify:
# {60: ('201E', '0132'),
#  72: ('00AB', '0171'),
#  82: ('201C', '0147'),
#  92: ('2018', '0145'),
#  104: ('00BB', '0187'),
#  114: ('201D', '0148'),
#  124: ('2019', '0146'),
#  137: ('00A2', '0162'),
#  150: ('2030', '0137'),
#  172: ('00B6', '0182'),
#  202: ('00C7', '0199'),
#  214: ('0153', '0156'),
#  224: ('0152', '0140'),
#  267: ('00C0', '0192'),
#  280: ('00C9', '0201'),
#  293: ('00C8', '0200'),
#  309: ('00F1', '0241'),
#  319: ('00D1', '0209'),
#  346: ('00D9', '0217'),
#  366: ('00E6', '0230'),
#  376: ('00C6', '0198'),
#  388: ('00DF', '0223'),
#  421: ('00BF', '0191'),
#  433: ('2013', '0150'),
#  446: ('2014', '0151'),
#  459: ('2026', '0133'),
#  477: ('00B7', '0183'),
#  546: ('00B9', '0185'),
#  740: ('003C', '060'),
#  761: ('003E', '062'),
#  786: ('2030', '0137'),
#  804: ('00D7', '0215'),
#  858: ('00B1', '0177'),
#  873: ('00F7', '0247'),
#  912: ('00A6', '0166'),
#  924: ('00AC', '0172'),
#  958: ('00A0', '0160')}

# CP 437
# 39 unfound codes: 
# {60: ('201E', 'macro_dqt_low'),
#  82: ('201C', 'macro_dqm_l'),
#  92: ('2018', 'macro_sqm_l'),
#  114: ('201D', 'macro_dqm_r'),
#  124: ('2019', 'macro_sqm_r'),
#  150: ('2030', 'macro_mer_mil'),
#  214: ('0153', 'macro_o_e'),
#  224: ('0152', 'macro_c_o_e'),
#  267: ('00C0', 'macro_c_a_grave'),
#  293: ('00C8', 'macro_c_e_grave'),
#  346: ('00D9', 'macro_c_u_grave'),
#  398: ('1E9E', 'macro_s_sharp'),
#  411: ('2011', 'macro_nb_hyphen'),
#  433: ('2013', 'macro_en_dash'),
#  446: ('2014', 'macro_em_dash'),
#  459: ('2026', 'macro_h_ellipsis'),
#  503: ('202F', 'macro_sp_insec_fine'),
#  536: ('2081', 'macro_sub_1'),
#  546: ('00B9', 'macro_sup_1'),
#  557: ('2082', 'macro_sub_2'),
#  569: ('2083', 'macro_sub_3'),
#  581: ('2084', 'macro_sub_4'),
#  591: ('2074', 'macro_sup_4'),
#  602: ('2085', 'macro_sub_5'),
#  612: ('2075', 'macro_sup_5'),
#  623: ('2086', 'macro_sub_6'),
#  633: ('2076', 'macro_sup_6'),
#  644: ('2087', 'macro_sub_7'),
#  654: ('2077', 'macro_sup_7'),
#  665: ('2088', 'macro_sub_8'),
#  675: ('2078', 'macro_sup_8'),
#  686: ('2089', 'macro_sub_9'),
#  696: ('2079', 'macro_sup_9'),
#  707: ('2080', 'macro_sub_0'),
#  717: ('2070', 'macro_sup_0'),
#  786: ('2030', 'macro_per_mil'),
#  804: ('00D7', 'macro_multiply'),
#  843: ('2260', 'macro_not_equal'),
#  912: ('00A6', 'macro_broken_bar')}

# 21 lines to modify:
# {72: ('00AB', '174'),
#  104: ('00BB', '175'),
#  137: ('00A2', '155'),
#  172: ('00B6', '20'),
#  202: ('00C7', '128'),
#  280: ('00C9', '144'),
#  309: ('00F1', '164'),
#  319: ('00D1', '165'),
#  366: ('00E6', '145'),
#  376: ('00C6', '146'),
#  388: ('00DF', '225'),
#  421: ('00BF', '168'),
#  477: ('00B7', '250'),
#  740: ('003C', '60'),
#  750: ('2264', '243'),
#  761: ('003E', '62'),
#  771: ('2265', '242'),
#  858: ('00B1', '241'),
#  873: ('00F7', '246'),
#  924: ('00AC', '170'),
#  958: ('00A0', '255')}