import { Component } from '@angular/core';
import { ScrapingService } from '../../services/scraping/scraping.service';

interface Comentario {
  usuario: string;
  comentario: string;
  video_title?: string;
  tweet_id?: string;
  plataforma: string;
  confianza?: number;
  riesgo?: number;
  etiquetas?: string[];
  fecha?: string;
}

@Component({
  selector: 'app-monitoreo',
  standalone: false,
  templateUrl: './monitoreo.component.html',
  styleUrl: './monitoreo.component.css',
})
export class MonitoreoComponent {
  palabraClave = 'mundial de clubes';
  maxResultados = 3;
  comentarios: any[] = [];
  cargando = false;

  constructor(private scrapingSer: ScrapingService) {}

  ejecutarScraping(plataforma: string) {
    this.cargando = true;

    this.scrapingSer
      .ejecutarScraping(plataforma, this.palabraClave, this.maxResultados)
      .subscribe({
        next: (res) => {
          const archivo = res.archivo_limpio || res.archivo_json;
          this.scrapingSer
            .obtenerComentarios(archivo)
            .subscribe((comentarios) => {
              const formateados = comentarios.map((c: any) => ({
                ...c,
                plataforma,
                confianza: Math.floor(Math.random() * 20) + 80,
                riesgo: Math.floor(Math.random() * 100),
                etiquetas: ['Fútbol'],
                fecha: new Date().toLocaleString(),
              }));
              this.comentarios.push(...formateados);
              this.cargando = false;
            });
        },
        error: (e) => {
          console.error('Error en scraping', e);
          this.cargando = false;
        },
      });
  }
  onPlatformChange(event: Event) {
    const selectElement = event.target as HTMLSelectElement;
    const plataforma = selectElement.value;
    this.ejecutarScraping(plataforma);
  }
}
