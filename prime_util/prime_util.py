from modules import *


def format_openai_response(block):
    if block.type == "text":
        return block.text.value
    elif block.type == "code":
        return f"```{block.text.value}```"
    else:
        return "[Unsupported content type]"


def get_from_json(filename):
    try:
        with open(filename, encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def suffix_number(s):
    m = re.search(r'\d+$', s)
    return int(m.group()) if m else None


def parse_function(s: str):
    def helper(s, idx=0, inherited_name=''):
        name = inherited_name
        args = []
        current = ''
        meta = {}

        def flush_arg():
            nonlocal current, meta
            if current:
                args.append({**meta, 'type': current})
                current = ''
                meta = {}

        while idx < len(s):
            c = s[idx]

            # Identifiers
            if c.isalnum() or c == '_':
                current += c
                idx += 1
                continue

            # Modifiers for current token
            if c in '?*':
                if c == '?': meta['opt'] = True
                if c == '*': meta['zero_rep'] = True
                idx += 1
                continue

            if c == '{':
                end = s.find('}', idx)
                range_text = s[idx + 1:end]
                parts = range_text.split(',')
                if len(parts) == 2:
                    meta['from_to'] = (int(parts[0]), int(parts[1]))
                else:
                    meta['times'] = int(parts[0])
                idx = end + 1
                continue

            # Nested function
            if c == '(':
                func_name = current
                current = ''
                nested_func, idx = helper(s, idx + 1, func_name)

                # 🧠 Handle modifiers trailing the nested function call
                while idx < len(s) and s[idx] in '?*{':
                    mod = s[idx]
                    if mod == '?':
                        nested_func['opt'] = True
                        idx += 1
                    elif mod == '*':
                        nested_func['zero_rep'] = True
                        idx += 1
                    elif mod == '{':
                        end = s.find('}', idx)
                        range_text = s[idx + 1:end]
                        parts = range_text.split(',')
                        if len(parts) == 2:
                            nested_func['from_to'] = (int(parts[0]), int(parts[1]))
                        else:
                            nested_func['times'] = int(parts[0])
                        idx = end + 1
                args.append(nested_func)
                meta = {}
                continue

            # Argument separator
            if c == ',':
                flush_arg()
                idx += 1
                continue

            # Function close
            if c == ')':
                flush_arg()
                return {'type': 'func', 'name': name, 'args': args}, idx + 1

            idx += 1

        flush_arg()
        return {'type': 'func', 'name': name, 'args': args}, idx

    first_paren = s.find('(')
    if first_paren == -1:
        raise ValueError("Invalid format: missing '('")
    root_name = s[:first_paren].strip()
    result, _ = helper(s, first_paren + 1, root_name)
    return result


def iprint(*args, **kwargs):
    if CAN_PRINT:
        print("[DEBUG]", *args, **kwargs)


def ipprint(*args, **kwargs):
    if CAN_PRINT:
        pprint(*args, **kwargs)
