import json

file = r"c:\Users\Imart\Desktop\Multi Agent\Missing Spec Optimizer - Complete Flow v2.json"

with open(r"c:\Users\Imart\Desktop\Multi Agent\missing_spec_blueprint.md", "w", encoding="utf-8") as out:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            out.write(f"\n=========================================\nFile: {file}\n=========================================\n")
            nodes = data.get('nodes', [])
            for node in nodes:
                node_type = node.get('type', '')
                node_name = node.get('name', '')
                parameters = node.get('parameters', {})
                options = parameters.get('options', {})
                
                if 'prompt' in parameters or 'text' in parameters or 'messages' in parameters:
                    out.write(f"\n--- Node: {node_name} ({node_type}) ---\n")
                    
                    if 'messages' in parameters:
                        messages = parameters.get('messages', {}).get('messageValues', [])
                        for msg in messages:
                            out.write(f"{msg.get('type', 'UNKNOWN')}: {msg.get('message', '')}\n")
                    
                    if 'options' in parameters and 'systemMessage' in parameters['options']:
                        out.write(f"SYSTEM: {parameters['options']['systemMessage']}\n")
                        
                    if 'text' in parameters:
                        out.write(f"TEXT: {parameters['text']}\n")
                
                if node_type == 'n8n-nodes-base.code':
                    out.write(f"\n--- Code Node: {node_name} ---\n")
                    code = parameters.get('jsCode', '')
                    out.write(code[:300] + "...\n")
    except Exception as e:
        out.write(f"Error reading {file}: {e}\n")
