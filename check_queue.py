import json
import os
from pathlib import Path
from datetime import datetime

def check_status():
    queue_file = Path("publish_queue.json")
    if not queue_file.exists():
        print("⚠️  Nenhuma fila de publicação encontrada (publish_queue.json).")
        return

    with open(queue_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        queue = data.get("queue", [])

    if not queue:
        print("📭 Fila de publicação está vazia.")
        return

    print("\n" + "="*70)
    print(f"{'ID':<10} | {'PLATAFORMAS':<25} | {'HORÁRIO':<20} | {'STATUS':<12}")
    print("-" * 70)

    for job in sorted(queue, key=lambda x: x['scheduled_time']):
        jid = job['id']
        platforms = ",".join(job['platforms'])
        # Formatar tempo
        st = datetime.fromisoformat(job['scheduled_time']).strftime("%d/%m %H:%M")
        status = job['status'].upper()
        
        status_icon = "📅"
        if status == "PUBLISHED": status_icon = "✅"
        if status == "FAILED": status_icon = "❌"
        if status == "PUBLISHING": status_icon = "📤"

        print(f"{jid:<10} | {platforms:<25} | {st:<20} | {status_icon} {status:<12}")

    print("="*70)
    print(f"\nTotal: {len(queue)} jobs na fila.")

if __name__ == "__main__":
    check_status()
