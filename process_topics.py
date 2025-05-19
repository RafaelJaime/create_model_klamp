import os
import re
import time
import requests
import openai
from pathlib import Path
from datetime import datetime

# Configuración
TOPICS_FILE = "topics.md"
REPORTS_DIR = "reports"
API_KEY = os.environ.get("OPENAI_API_KEY")  # Asegúrate de tener tu API key como variable de entorno

# Inicializar el cliente de OpenAI
openai.api_key = API_KEY

def setup_environment():
    """Configura el entorno necesario."""
    # Crear la carpeta de informes si no existe
    reports_dir = Path(REPORTS_DIR)
    if not reports_dir.exists():
        reports_dir.mkdir(parents=True)
    
    # Verificar que la API key está configurada
    if not API_KEY:
        print("⚠️ No se encontró la API key de OpenAI como variable de entorno.")
        print("Por favor, configura la variable de entorno OPENAI_API_KEY")
        return False
    return True

def read_topics_file():
    """Lee el archivo de temas y devuelve su contenido."""
    try:
        with open(TOPICS_FILE, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ Error: El archivo {TOPICS_FILE} no existe.")
        return None

def parse_topics(content):
    """Extrae los temas del contenido del archivo."""
    if not content:
        return []
    
    # Encontrar todas las líneas con formato [ ] o [x]
    topic_lines = re.findall(r'^\[([ x])\] (.+)$', content, re.MULTILINE)
    
    # Devolver una lista de tuplas (estado, tema)
    return [(checked, topic) for checked, topic in topic_lines]

def deep_research(topic):
    """Realiza una investigación profunda sobre el tema utilizando la API de OpenAI."""
    print(f"🔍 Investigando: {topic[:70]}...")
    
    try:
        completion = openai.chat.completions.create(
            model="gpt-4",  # Puedes cambiar el modelo según tu preferencia
            messages=[
                {"role": "system", "content": "Eres un asistente especializado en investigación médica y legislativa en el contexto español y andaluz. Genera informes detallados, estructurados y bien documentados basados en el tema proporcionado."},
                {"role": "user", "content": f"Realiza una investigación profunda sobre el siguiente tema del ámbito sanitario español:\n\n{topic}\n\nProporciona un informe detallado que incluya:\n1. Introducción al tema\n2. Marco legal y normativo\n3. Aspectos clave y puntos principales\n4. Aplicación práctica\n5. Referencias y fuentes"}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Error al realizar la investigación: {e}")
        return f"Error en la investigación: {e}"

def save_report(topic, content):
    """Guarda el informe generado en un archivo dentro de la carpeta reports."""
    # Crear un nombre de archivo válido basado en el tema
    filename = re.sub(r'[^\w\s-]', '', topic)  # Eliminar caracteres especiales
    filename = re.sub(r'\s+', '_', filename)   # Reemplazar espacios con guiones bajos
    filename = filename[:100]  # Limitar longitud
    
    # Añadir fecha y extensión
    now = datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(REPORTS_DIR, f"{now}_{filename}.md")
    
    # Guardar el informe
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(f"# {topic}\n\n")
            file.write(f"*Informe generado el {datetime.now().strftime('%d/%m/%Y')}*\n\n")
            file.write(content)
        print(f"✅ Informe guardado en: {filepath}")
        return os.path.basename(filepath)
    except Exception as e:
        print(f"❌ Error al guardar el informe: {e}")
        return None

def update_topics_file(content, topic, report_filename):
    """Actualiza el archivo de temas para marcar el tema como completado."""
    # Escape caracteres especiales de regex en el tema
    escaped_topic = re.escape(topic)
    
    # Reemplazar [ ] por [x] para el tema específico
    updated_content = re.sub(
        f'\\[ \\] {escaped_topic}',
        f'[x] {topic} - [Ver informe](./{REPORTS_DIR}/{report_filename})',
        content
    )
    
    # Guardar el archivo actualizado
    try:
        with open(TOPICS_FILE, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        print(f"✅ Archivo {TOPICS_FILE} actualizado.")
        return True
    except Exception as e:
        print(f"❌ Error al actualizar el archivo: {e}")
        return False

def process_topics():
    """Procesa todos los temas pendientes."""
    # Configurar el entorno
    if not setup_environment():
        return
    
    # Leer el archivo de temas
    content = read_topics_file()
    if not content:
        return
    
    # Analizar los temas
    topics = parse_topics(content)
    pending_topics = [(status, topic) for status, topic in topics if status == ' ']
    
    print(f"📋 Total de temas: {len(topics)}")
    print(f"🔄 Temas pendientes: {len(pending_topics)}")
    
    # Procesar cada tema pendiente
    for i, (_, topic) in enumerate(pending_topics):
        print(f"\n📝 Procesando tema {i+1}/{len(pending_topics)}")
        
        # Realizar investigación
        report_content = deep_research(topic)
        
        # Guardar informe
        report_filename = save_report(topic, report_content)
        if not report_filename:
            continue
        
        # Actualizar archivo de temas
        update_topics_file(content, topic, report_filename)
        
        # Actualizar contenido para el próximo tema
        content = read_topics_file()
        
        # Esperar un poco entre solicitudes a la API
        if i < len(pending_topics) - 1:
            print("⏳ Esperando antes de procesar el siguiente tema...")
            time.sleep(5)  # 5 segundos de espera
    
    print("\n✨ ¡Procesamiento de temas completado!")

if __name__ == "__main__":
    process_topics()