input_file = "metadata.csv"
output_file = "metadata_fixed.csv"

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

fixed_lines = []

for line in lines:
    line = line.strip()

    if not line:
        continue

    parts = line.split("|", 1)

    if len(parts) != 2:
        continue

    filename, text = parts

    fixed_line = f"{filename}|{text}|{text}\n"
    fixed_lines.append(fixed_line)

with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("Fixed metadata saved as metadata_fixed.csv")