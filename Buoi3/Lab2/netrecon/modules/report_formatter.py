"""Format scan data as a readable email report."""
import json


def format_report(result):
    lines = ['Kết quả NetRecon:', f"Target: {result['target']}", f"Mode: {result['mode']}", '']
    for section in ('scan', 'service', 'banner', 'vuln', 'map'):
        if section not in result:
            continue
        value = result[section]
        lines.append(f'--- {section.upper()} ---')
        if section == 'scan' and isinstance(value, list):
            lines.append('PORT         STATE')
            lines.extend(f"{row['port']}/{row['protocol']}    {row['state']}" for row in value)
        elif section in ('service', 'banner') and isinstance(value, dict):
            lines.extend(f'{port}: {text}' for port, text in value.items())
            if not value:
                lines.append('Không có cổng TCP mở để nhận dạng/lấy banner.')
        elif section == 'map' and isinstance(value, dict):
            lines.append('IP                 MAC                  TYPE')
            lines.extend(f"{row['ip']:<18} {row['mac']:<20} {row['type']}" for row in value.get('neighbors', []))
            lines.append(value.get('note', ''))
        elif section == 'vuln' and isinstance(value, dict):
            lines.extend(f"Port {row['port']} [{row['level']}]: {row['finding']}" for row in value.get('findings', []))
            if not value.get('findings'):
                lines.append('Không có dấu hiệu cấu hình được ghi nhận trong lượt quét này.')
            lines.append(value.get('note', ''))
        else:
            lines.append(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))
        lines.append('')
    return '\n'.join(lines)
