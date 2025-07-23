# webscraping/analisis.py
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def generar_bolsa_de_palabras(csv_limpio):
    print("📥 Cargando comentarios...")
    df = pd.read_csv(csv_limpio)

    if 'comentario' not in df.columns:
        raise ValueError("La columna 'comentario' no está en el archivo CSV.")

    comentarios = df['comentario'].dropna().tolist()
    texto_completo = " ".join(comentarios)
    palabras = texto_completo.split()

    frecuencias = Counter(palabras)

    # Guardar CSV de frecuencia
    print("💾 Guardando frecuencias en 'frecuencia_palabras.csv'...")
    df_frecuencias = pd.DataFrame(frecuencias.items(), columns=["palabra", "frecuencia"])
    df_frecuencias = df_frecuencias.sort_values(by="frecuencia", ascending=False)
    df_frecuencias.to_csv("frecuencia_palabras.csv", index=False)

    # Top 20
    print("\n🟢 Top 20 palabras más frecuentes:")
    for palabra, freq in frecuencias.most_common(20):
        print(f"{palabra}: {freq}")

    # Gráfico de barras
    print("\n📊 Generando gráfico de barras...")
    top_20 = frecuencias.most_common(20)
    palabras_top, freqs_top = zip(*top_20)

    plt.figure(figsize=(10, 5))
    plt.bar(palabras_top, freqs_top)
    plt.xticks(rotation=45)
    plt.title("Top 20 palabras más frecuentes")
    plt.xlabel("Palabras")
    plt.ylabel("Frecuencia")
    plt.tight_layout()
    plt.savefig("grafico_barras_frecuencia.png")
    plt.close()

    # Nube de palabras
    print("☁️ Generando nube de palabras...")
    nube = WordCloud(width=800, height=400, background_color="white").generate(texto_completo)
    plt.figure(figsize=(10, 5))
    plt.imshow(nube, interpolation="bilinear")
    plt.axis("off")
    plt.title("Nube de palabras")
    plt.tight_layout()
    plt.savefig("nube_palabras.png")
    plt.close()

    print("✅ Visualizaciones generadas correctamente.")
