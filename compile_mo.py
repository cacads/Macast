"""Compile .po files to .mo files for Macast i18n"""
import os
import struct


def parse_po(po_path):
    """Parse .po file, return list of (msgid, msgstr) tuples"""
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    current_msgid = []
    current_msgstr = []
    in_msgid = False
    in_msgstr = False

    for line in content.split('\n'):
        s = line.strip()
        if s.startswith('msgid "'):
            if current_msgid or current_msgstr:
                entries.append((''.join(current_msgid), ''.join(current_msgstr)))
                current_msgid = []
                current_msgstr = []
            current_msgid.append(s[7:-1])
            in_msgid, in_msgstr = True, False
        elif s.startswith('msgstr "'):
            current_msgstr.append(s[8:-1])
            in_msgid, in_msgstr = False, True
        elif s.startswith('"') and in_msgid:
            current_msgid.append(s[1:-1])
        elif s.startswith('"') and in_msgstr:
            current_msgstr.append(s[1:-1])

    if current_msgid or current_msgstr:
        entries.append((''.join(current_msgid), ''.join(current_msgstr)))

    return entries


def write_mo(mo_path, entries):
    """Write .mo binary file"""
    sorted_entries = sorted(entries, key=lambda x: x[0])
    n = len(sorted_entries)
    header_size = 28
    o_table_off = header_size
    t_table_off = header_size + n * 8

    # Build string data
    o_data_list = []
    t_data_list = []
    o_offsets = []
    t_offsets = []

    cur_off = t_table_off + n * 8
    for o, t in sorted_entries:
        ob = o.encode('utf-8') + b'\x00'
        tb = t.encode('utf-8') + b'\x00'
        o_offsets.append((len(ob), cur_off))
        cur_off += len(ob)
        t_offsets.append((len(tb), cur_off))
        cur_off += len(tb)
        o_data_list.append(ob)
        t_data_list.append(tb)

    hash_offset = cur_off

    with open(mo_path, 'wb') as f:
        f.write(struct.pack('<I', 0x950412de))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', n))
        f.write(struct.pack('<I', o_table_off))
        f.write(struct.pack('<I', t_table_off))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', hash_offset))
        for ln, off in o_offsets:
            f.write(struct.pack('<II', ln, off))
        for ln, off in t_offsets:
            f.write(struct.pack('<II', ln, off))
        for d in o_data_list:
            f.write(d)
        for d in t_data_list:
            f.write(d)


def main():
    i18n_dir = 'i18n'
    for lang in os.listdir(i18n_dir):
        po = os.path.join(i18n_dir, lang, 'LC_MESSAGES', 'macast.po')
        mo = os.path.join(i18n_dir, lang, 'LC_MESSAGES', 'macast.mo')
        if os.path.exists(po):
            entries = parse_po(po)
            write_mo(mo, entries)
            print(f'Compiled: {lang} ({len(entries)} strings)')


if __name__ == '__main__':
    main()
