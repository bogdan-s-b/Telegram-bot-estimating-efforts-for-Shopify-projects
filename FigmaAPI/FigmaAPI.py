import requests
import json


class FigmaDataExtractor:
    def __init__(self, file_key, headers):
        self.file_key = file_key
        self.headers = headers
        self.ai_data = {
            "buttons": [],
            "inputs": [],
            "text_blocks": [],
            "containers": []
        }

    def fetch_file_data(self):
        url = f'https://api.figma.com/v1/files/{self.file_key}'
        response = requests.get(url, headers=self.headers)
        return response.json() if response.status_code == 200 else None

    @staticmethod
    def get_size(node):
        box = node.get("absoluteBoundingBox", {})
        return box.get("width", 0), box.get("height", 0)

    @staticmethod
    def get_color(fills):
        for fill in fills:
            if fill.get("type") == "SOLID":
                c = fill.get("color", {})
                r, g, b = c.get("r", 0), c.get("g", 0), c.get("b", 0)
                return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
        return None

    def process_node(self, node):
        name = node.get("name", "")
        node_type = node.get("type", "")
        width, height = self.get_size(node)
        style = node.get("style", {})
        fills = node.get("fills", [])
        color = self.get_color(fills)
        text = node.get("characters", "")

        if "button" in name.lower() or "btn" in name.lower():
            self.ai_data["buttons"].append({
                "name": name,
                "text": text,
                "width": width,
                "height": height,
                "fontSize": style.get("fontSize"),
                "color": color
            })
        elif "input" in name.lower() or "field" in name.lower():
            self.ai_data["inputs"].append({
                "name": name,
                "placeholder": text,
                "width": width,
                "height": height
            })
        elif node_type == "TEXT" and len(text) > 20:
            self.ai_data["text_blocks"].append({
                "name": name,
                "text": text,
                "fontSize": style.get("fontSize"),
                "color": color,
                "width": width,
                "height": height
            })
        elif node_type == "FRAME" and len(node.get("children", [])) > 1:
            self.ai_data["containers"].append({
                "name": name,
                "width": width,
                "height": height,
                "children_count": len(node["children"])
            })

    def traverse_and_filter(self, node):
        self.process_node(node)
        for child in node.get("children", []):
            self.traverse_and_filter(child)

    def extract(self):
        file_data = self.fetch_file_data()
        if file_data and 'document' in file_data:
            self.traverse_and_filter(file_data['document'])
            return self.ai_data
        else:
            print("Failed to fetch or parse Figma file.")
            return None

