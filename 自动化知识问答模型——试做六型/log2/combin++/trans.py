import json
import os
from pathlib import Path

def convert_files(input_dir, output_file):
    id_counter = 0
    all_entries = []

    input_path = Path(input_dir)
    txt_files = list(input_path.glob('*.txt'))

    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f_in:
            content = f_in.read()
            entries = []
            parts = content.split('```json')

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                clean_part = part.replace('```', '').strip()
                if clean_part.startswith('['):
                    try:
                        batch = json.loads(clean_part)
                        entries.extend(batch)
                    except:
                        pass
                else:
                    for line in clean_part.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                entries.append(entry)
                            except:
                                pass

            # 直接添加所有条目，不再检查重复
            all_entries.extend(entries)

    with open(output_file, 'w', encoding='utf-8') as f_out:
        for entry in all_entries:
            new_entry = {
                "id": id_counter,
                "Q": entry.get("content", ""),
                "A": entry.get("summary", "")
            }
            f_out.write(json.dumps(new_entry, ensure_ascii=False) + '\n')
            id_counter += 1

    return id_counter

# 使用示例
input_directory = '.'  # 当前目录
output_file = 'knowledge.json'
total_entries = convert_files(input_directory, output_file)
print(f"处理完成，共合并 {total_entries} 条数据")