def robust_read_ini(path: str) -> dict:
    """Reads an INI-like file, collecting repeated keys within sections into lists."""
    sections = dict()
    current_section = None

    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                sections[current_section] = dict()
                continue
            if "=" in line and current_section:
                key, value = map(str.strip, line.split("=", 1))
                section_dict = sections[current_section]
                if key in section_dict:
                    if isinstance(section_dict[key], list):
                        section_dict[key].append(value)
                    else:
                        section_dict[key] = [section_dict[key], value]
                else:
                    section_dict[key] = value
            else:
                print(f"Skipping line {lineno}: {line}")
    return sections


def robust_write_ini(path: str, contents: dict) -> None:
    """Note that this dict can have lists as values, which will be written as repeated keys."""
    with open(path, "w", encoding="utf-8") as f:
        for section, keys in contents.items():
            f.write(f"[{section}]\n")
            for key, value in keys.items():
                if isinstance(value, list):
                    for v in value:
                        f.write(f"{key} = {v}\n")
                else:
                    f.write(f"{key} = {value}\n")
            f.write("\n")