import { Component, OnInit } from '@angular/core';
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
  clasificacion?: string;
}

@Component({
  selector: 'app-monitoreo',
  standalone: false,
  templateUrl: './monitoreo.component.html',
  styleUrl: './monitoreo.component.css',
})
export class MonitoreoComponent implements OnInit {
  palabraClave = '';
  maxResultados = 3;
  comentarios: Comentario[] = [];
  comentariosFiltrados: Comentario[] = [];

  plataformaSeleccionada = '';
  filtroPlataforma = 'todas';

  cargando = false;

  constructor(private scrapingSer: ScrapingService) {}

  ngOnInit(): void {
    this.cargarComentariosPrevios();
  }

  cargarComentariosPrevios() {
    this.cargando = true;
    const plataformas = ['x', 'youtube', 'tiktok'];
    let pendientes = plataformas.length;

    plataformas.forEach((plataforma) => {
      this.scrapingSer.obtenerComentariosDesdeApi(plataforma).subscribe({
        next: (comentarios) => {
          const formateados = comentarios.map((c: any) => ({
            ...c,
            plataforma,
            confianza: Math.floor(Math.random() * 20) + 80,
            riesgo: Math.floor(Math.random() * 100),
            etiquetas: ['Fútbol'],
            fecha: new Date().toLocaleString(),
          }));
          this.comentarios.push(...formateados);
          this.actualizarComentariosFiltrados();
          pendientes--;
          if (pendientes === 0) this.cargando = false;
        },
        error: () => {
          pendientes--;
          if (pendientes === 0) this.cargando = false;
        },
      });
    });
  }

  ejecutarScraping() {
    if (!this.plataformaSeleccionada) return;
    this.cargando = true;

    this.scrapingSer
      .ejecutarScraping(this.plataformaSeleccionada, this.palabraClave, this.maxResultados)
      .subscribe({
        next: () => {
          this.scrapingSer
            .obtenerComentariosDesdeApi(this.plataformaSeleccionada)
            .subscribe((comentarios) => {
              const formateados = comentarios.map((c: any) => ({
                ...c,
                plataforma: this.plataformaSeleccionada,
                confianza: Math.floor(Math.random() * 20) + 80,
                riesgo: Math.floor(Math.random() * 100),
                etiquetas: ['Fútbol'],
                fecha: new Date().toLocaleString(),
              }));
              this.comentarios.push(...formateados);
              this.actualizarComentariosFiltrados();
              this.cargando = false;
            });
        },
        error: (e) => {
          console.error('Error en scraping', e);
          this.cargando = false;
        },
      });
  }

  actualizarComentariosFiltrados() {
    this.comentariosFiltrados = this.filtroPlataforma === 'todas'
      ? [...this.comentarios]
      : this.comentarios.filter(c => c.plataforma === this.filtroPlataforma);
  }

  onChangeFiltroPlataforma(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.filtroPlataforma = select.value;
    this.actualizarComentariosFiltrados();
  }

  onSeleccionPlataforma(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.plataformaSeleccionada = select.value;
  }
}
